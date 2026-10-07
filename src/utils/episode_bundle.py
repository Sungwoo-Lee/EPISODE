"""Episode bundles: one uncompressed ZIP per behaviour-test sweep cell.

A sweep cell is the folder ``<scratch>/<run_label>/<cond>/<step>/`` that ``eval_rollout.py``
writes for one checkpoint in one test scene (about 64 small files: per-episode ``.npz`` arrays,
``.rec.gz`` recordings, a ``run_meta.pkl``, a parquet and two JSON files). This module stores the
SAME files, byte for byte, in one archive ``<scratch>/<run_label>/<cond>/<step>.zip`` and reads
them back. Plan: docs/develop/active/refactors/SWEEP_EPISODE_BUNDLES_AND_ON_NODE_MEASURES.md (F1).

Format
    ``ZIP_STORED`` (no compression: the recordings are already gzip), member names are POSIX paths
    relative to the cell, sorted, directory entries kept (``name/``). The archive comment is JSON:
    ``{"pack_host", "pack_time", "n", "bytes", "src_mtime_max_ns"}``.

API
    cell_path(cond_dir, step)       -> archive, legacy folder, or None (raises CellConflict)
    members(cell, pattern)          -> relative member names, ordered like sorted(dir.glob(pattern))
    open_member / load_recording / load_npz
    pack(src_dir, zip_path)         -> manifest; atomic (partial file, verify, then rename)
    verify(src_dir, zip_path)       -> manifest, or raises BundleMismatch
    delete_verified(cell_dir, zip_path, wal_path, repo_root=...)  -> the ONLY deleting function
    extract(zip_path, dest_dir)     -> for tools that need a folder

``cell`` arguments accept either form: a legacy folder or a ``.zip`` path.

Nothing here derives the repository root from this file's location (plan-review finding N1): the
one function that needs it, ``delete_verified``, takes ``repo_root`` as a required argument.
Pure Python + numpy; no JAX.
"""
from __future__ import annotations

import fnmatch
import gzip
import hashlib
import io
import json
import os
import pickle
import re
import socket
import time
import zipfile
from pathlib import Path, PurePosixPath
from typing import BinaryIO, Dict, List, Optional, Tuple

import numpy as np

BUNDLE_SUFFIX = ".zip"
DEFAULT_EPISODE_PATTERN = "**/episode_*.rec.gz"
_CHUNK = 1 << 20

#: A sweep cell never holds these; finding one means the path is not a cell (fail closed).
PROTECTED_SUFFIXES = (".csv", ".png", ".html", ".mp4", ".gif", ".npy", ".txt")
PROTECTED_DIRS = ("_provenance", "videos", "motifs")

Manifest = Dict[str, Tuple[int, str]]


class BundleMismatch(Exception):
    """An archive does not hold exactly the files of its source folder."""


class CellConflict(Exception):
    """A cell exists as both archive and folder, and the folder is newer than the archive."""


class DeleteRefused(Exception):
    """delete_verified refused: a path, host or content guard did not pass."""


# ------------------------------------------------------------------------------------ helpers ----
def _is_zip(cell) -> bool:
    return str(cell).endswith(BUNDLE_SUFFIX)


def _sha256_file(path) -> Tuple[int, str]:
    h = hashlib.sha256()
    n = 0
    with open(path, "rb") as fh:
        while True:
            b = fh.read(_CHUNK)
            if not b:
                break
            h.update(b)
            n += len(b)
    return n, h.hexdigest()


def _drop_cache(path) -> None:
    """Ask the kernel to drop its cached pages of `path`, so the next read goes to the storage
    (review finding M1: a re-read from this host's page cache would not test the NAS copy)."""
    fd = os.open(str(path), os.O_RDONLY)
    try:
        os.fsync(fd)
        os.posix_fadvise(fd, 0, 0, os.POSIX_FADV_DONTNEED)
    finally:
        os.close(fd)


def _walk(src_dir) -> Tuple[List[str], List[str]]:
    """(dirs, files) under src_dir as sorted relative POSIX names (dirs without trailing '/').
    Symlinks are refused: a cell never contains one and packing a link target is ambiguous."""
    src = Path(src_dir)
    if not src.is_dir():
        raise FileNotFoundError(f"not a directory: {src}")
    dirs, files = [], []
    for root, dnames, fnames in os.walk(src):
        rootp = Path(root)
        for d in dnames:
            p = rootp / d
            if p.is_symlink():
                raise BundleMismatch(f"symlink in cell (refused): {p}")
            dirs.append(p.relative_to(src).as_posix())
        for f in fnames:
            p = rootp / f
            if p.is_symlink():
                raise BundleMismatch(f"symlink in cell (refused): {p}")
            files.append(p.relative_to(src).as_posix())
    return sorted(dirs), sorted(files)


def _newest_file_mtime_ns(src_dir) -> Optional[int]:
    _, files = _walk(src_dir)
    if not files:
        return None
    return max(os.stat(Path(src_dir) / f).st_mtime_ns for f in files)


def read_comment(zip_path) -> dict:
    """The archive's JSON comment, or raise BundleMismatch if absent/unparseable."""
    with zipfile.ZipFile(zip_path) as zf:
        raw = zf.comment
    try:
        meta = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as e:
        raise BundleMismatch(f"{zip_path}: archive comment is not bundle JSON ({e})")
    for k in ("pack_host", "pack_time", "n", "bytes", "src_mtime_max_ns"):
        if k not in meta:
            raise BundleMismatch(f"{zip_path}: archive comment lacks '{k}'")
    return meta


def _match_parts(pat: List[str], name: List[str]) -> bool:
    """Path.glob-style match of split pattern against split relative name. '**' = zero or more
    directory levels; other segments use fnmatchcase (POSIX pathlib is case-sensitive)."""
    if not pat:
        return not name
    if pat[0] == "**":
        # '**' consumes zero or more DIRECTORY segments; the last name segment is never a dir here.
        for k in range(0, len(name)):
            if _match_parts(pat[1:], name[k:]):
                return True
        return False
    if not name:
        return False
    return fnmatch.fnmatchcase(name[0], pat[0]) and _match_parts(pat[1:], name[1:])


# ------------------------------------------------------------------------------------- reader ----
def cell_path(cond_dir, step) -> Optional[Path]:
    """<cond_dir>/<step>.zip if it exists, else legacy <cond_dir>/<step>/ if it exists, else None.

    If BOTH exist, the archive wins only if no file in the folder is newer than the newest source
    file recorded at pack time (``src_mtime_max_ns`` in the comment; both times come from the same
    filesystem, so host clock skew cannot cause a false result). A folder written AFTER the archive
    (an old-code re-test, review M7) raises CellConflict -- stale episodes are never returned."""
    cond_dir = Path(cond_dir)
    z = cond_dir / f"{step}{BUNDLE_SUFFIX}"
    d = cond_dir / str(step)
    has_z, has_d = z.is_file(), d.is_dir()
    if has_z and has_d:
        meta = read_comment(z)
        newest = _newest_file_mtime_ns(d)
        if newest is not None and newest > int(meta["src_mtime_max_ns"]):
            raise CellConflict(
                f"{d} holds a file newer than its archive {z} "
                f"({newest} > {meta['src_mtime_max_ns']} ns); resolve by hand")
        return z
    if has_z:
        return z
    if has_d:
        return d
    return None


def members(cell, pattern: str = DEFAULT_EPISODE_PATTERN) -> List[str]:
    """Relative POSIX names of the FILES in `cell` matching `pattern`, in the order
    ``sorted(Path(cell).glob(pattern))`` gives for a folder."""
    if _is_zip(cell):
        pat = PurePosixPath(pattern).parts
        with zipfile.ZipFile(cell) as zf:
            names = [i.filename for i in zf.infolist() if not i.is_dir()]
        hits = [n for n in names if _match_parts(list(pat), list(PurePosixPath(n).parts))]
        return sorted(hits, key=PurePosixPath)
    root = Path(cell)
    return [p.relative_to(root).as_posix() for p in sorted(root.glob(pattern)) if p.is_file()]


def read_member(cell, name: str) -> bytes:
    if _is_zip(cell):
        with zipfile.ZipFile(cell) as zf:
            return zf.read(name)
    with open(Path(cell) / name, "rb") as fh:
        return fh.read()


def open_member(cell, name: str) -> BinaryIO:
    """A binary file object holding the member's bytes (read fully; cell files are small)."""
    return io.BytesIO(read_member(cell, name))


def load_recording(cell, name: str) -> dict:
    """Same result as ``src.utils.eval_recording.load_episode`` on the member's file."""
    with gzip.GzipFile(fileobj=open_member(cell, name), mode="rb") as fh:
        return pickle.load(fh)


def load_npz(cell, name: str) -> dict:
    with np.load(open_member(cell, name), allow_pickle=False) as z:
        return {k: z[k] for k in z.files}


# --------------------------------------------------------------------------- packer / verifier ----
def verify(src_dir, zip_path, _wal_accepted: Optional[Manifest] = None) -> Manifest:
    """Exact equality or raise BundleMismatch: same file names, same directory entries, same size
    and sha256 per member, ``testzip()`` is None. Returns the archive manifest {name: (size, sha)}.

    `_wal_accepted` (used only by delete_verified's resume path): files absent from `src_dir` are
    accepted if they are listed there with the archive's size and sha256."""
    src_dir, zip_path = Path(src_dir), Path(zip_path)
    _drop_cache(zip_path)
    s_dirs, s_files = _walk(src_dir)
    manifest: Manifest = {}
    with zipfile.ZipFile(zip_path) as zf:
        bad = zf.testzip()
        if bad is not None:
            raise BundleMismatch(f"{zip_path}: CRC error in member {bad}")
        infos = zf.infolist()
        z_dirs = sorted(i.filename.rstrip("/") for i in infos if i.is_dir())
        z_files = sorted(i.filename for i in infos if not i.is_dir())
        if len(set(z_files)) != len(z_files):
            raise BundleMismatch(f"{zip_path}: duplicate member names")
        resume = bool(_wal_accepted)
        if resume:
            if not set(s_dirs) <= set(z_dirs):
                raise BundleMismatch(f"{src_dir}: directories not in archive: "
                                     f"{sorted(set(s_dirs) - set(z_dirs))}")
        elif s_dirs != z_dirs:
            raise BundleMismatch(f"{src_dir} vs {zip_path}: directory entries differ: "
                                 f"only in source {sorted(set(s_dirs) - set(z_dirs))}, "
                                 f"only in archive {sorted(set(z_dirs) - set(s_dirs))}")
        extra = sorted(set(s_files) - set(z_files))
        if extra:
            raise BundleMismatch(f"{src_dir}: files not in archive: {extra}")
        missing = sorted(set(z_files) - set(s_files))
        for name in z_files:
            info = zf.getinfo(name)
            h = hashlib.sha256()
            with zf.open(info) as fh:
                while True:
                    b = fh.read(_CHUNK)
                    if not b:
                        break
                    h.update(b)
            manifest[name] = (info.file_size, h.hexdigest())
        for name in missing:
            if not resume or _wal_accepted.get(name) != manifest[name]:
                raise BundleMismatch(f"{src_dir}: archive member missing from source: {name}")
        for name in s_files:
            size, sha = _sha256_file(src_dir / name)
            if (size, sha) != manifest[name]:
                raise BundleMismatch(f"{src_dir / name}: differs from archive member "
                                     f"(size {size} vs {manifest[name][0]})")
    return manifest


def pack(src_dir, zip_path) -> Manifest:
    """Write src_dir's tree into ``<zip_path>.partial-<host>-<pid>``, verify it against the source
    after dropping this host's cached pages, and only then rename it to `zip_path`.
    On any failure the partial file is removed and the error raised; `zip_path` is never left
    half-written. Refuses to overwrite an existing `zip_path`. Returns the manifest."""
    src_dir, zip_path = Path(src_dir), Path(zip_path)
    if not zip_path.name.endswith(BUNDLE_SUFFIX):
        raise ValueError(f"bundle path must end with {BUNDLE_SUFFIX}: {zip_path}")
    if zip_path.exists():
        raise FileExistsError(f"archive already exists (refusing to overwrite): {zip_path}")
    host = socket.gethostname()
    partial = zip_path.with_name(f"{zip_path.name}.partial-{host}-{os.getpid()}")
    dirs, files = _walk(src_dir)
    entries = sorted([(d + "/", True) for d in dirs] + [(f, False) for f in files])
    try:
        total = 0
        mt_max = 0
        with zipfile.ZipFile(partial, "w", compression=zipfile.ZIP_STORED) as zf:
            for name, is_dir in entries:
                p = src_dir / name.rstrip("/")
                zi = zipfile.ZipInfo.from_file(p, arcname=name.rstrip("/") + ("/" if is_dir else ""),
                                               strict_timestamps=False)
                zi.compress_type = zipfile.ZIP_STORED
                if is_dir:
                    zf.writestr(zi, b"")
                    continue
                st = os.stat(p)
                mt_max = max(mt_max, st.st_mtime_ns)
                with open(p, "rb") as src, zf.open(zi, "w", force_zip64=st.st_size > 2**31) as dst:
                    while True:
                        b = src.read(_CHUNK)
                        if not b:
                            break
                        dst.write(b)
                total += st.st_size
            zf.comment = json.dumps({
                "pack_host": host, "pack_time": time.time(), "n": len(files),
                "bytes": total, "src_mtime_max_ns": mt_max,
            }, sort_keys=True).encode("utf-8")
        manifest = verify(src_dir, partial)   # _drop_cache (fsync + DONTNEED) happens inside
        os.replace(partial, zip_path)
    except BaseException:
        if partial.exists():
            partial.unlink()
        raise
    return manifest


def extract(zip_path, dest_dir) -> Path:
    """Unpack an archive into `dest_dir` (must not exist or be empty) and verify the result."""
    dest = Path(dest_dir)
    if dest.exists() and any(dest.iterdir()):
        raise FileExistsError(f"extract destination is not empty: {dest}")
    dest.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path) as zf:
        zf.extractall(dest)
    verify(dest, zip_path)
    return dest


# ----------------------------------------------------------------------------- guarded delete ----
_DIGITS = re.compile(r"[0-9]+")


def _guard_paths(cell_dir, zip_path, repo_root) -> Tuple[Path, Path]:
    if repo_root is None:
        raise DeleteRefused("repo_root is required")
    root = Path(repo_root).resolve(strict=True)
    eval_root = root / "results" / "eval"
    cell = Path(cell_dir).resolve(strict=True)
    zp = Path(zip_path).resolve(strict=True)
    try:
        rel = cell.relative_to(eval_root)
    except ValueError:
        raise DeleteRefused(f"{cell} is not under {eval_root}")
    parts = rel.parts
    # Class S only: results/eval/**/_scratch/<label>/<cond>/<digits>
    if len(parts) < 4 or parts[-4] != "_scratch":
        raise DeleteRefused(f"{cell} is not a sweep cell (_scratch/<label>/<cond>/<step>)")
    label, cond, step = parts[-3], parts[-2], parts[-1]
    if not _DIGITS.fullmatch(step):
        raise DeleteRefused(f"{cell}: last component is not a checkpoint step")
    if label.startswith("_") or cond.startswith("_"):
        raise DeleteRefused(f"{cell}: label/cond starting with '_' is pipeline bookkeeping")
    if any(p in PROTECTED_DIRS for p in parts):
        raise DeleteRefused(f"{cell}: path contains a protected directory")
    if zp != cell.parent / f"{step}{BUNDLE_SUFFIX}":
        raise DeleteRefused(f"{zp} is not the sibling archive of {cell}")
    return cell, zp


def _read_wal(wal_path, cell: Path) -> Manifest:
    out: Manifest = {}
    wal = Path(wal_path)
    if not wal.exists():
        return out
    key = str(cell)
    with open(wal) as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            if rec["cell"] == key:
                out[rec["name"]] = (int(rec["size"]), rec["sha256"])
    return out


def delete_verified(cell_dir, zip_path, wal_path, *, repo_root) -> int:
    """The ONLY function that deletes episode originals. Returns the number of files unlinked.

    Guards, all before anything is removed:
      - path: `cell_dir` is ``<repo_root>/results/eval/**/_scratch/<label>/<cond>/<digits>`` and
        `zip_path` is its sibling ``<digits>.zip``; nothing under `_provenance/`, `videos/`,
        `motifs/`; no file with a protected suffix (.csv/.png/.html/.mp4/.gif/.npy/.txt) in the cell.
      - host: refuses on the host that packed the archive (comment's ``pack_host``). No override.
      - content: cache dropped, then verify(cell_dir, zip_path) again.
    Then appends (cell, name, size, sha256) per file to `wal_path` and fsyncs it BEFORE unlinking,
    unlinks exactly the verified files (after re-checking size + mtime), and removes directories
    bottom-up with os.rmdir (never rmtree): a file that appeared after verification makes rmdir
    fail and is left in place.
    Resume: if an earlier call died midway, files listed in the WAL for this cell and absent on
    disk are accepted; files still present are verified as usual.
    `repo_root` is required (review finding N1) -- it is never derived from this file's location."""
    cell, zp = _guard_paths(cell_dir, zip_path, repo_root)
    _, files_now = _walk(cell)
    for f in files_now:
        if f.endswith(PROTECTED_SUFFIXES) or any(p in PROTECTED_DIRS for p in PurePosixPath(f).parts):
            raise DeleteRefused(f"{cell / f}: protected file inside cell; refusing")
    meta = read_comment(zp)
    here = socket.gethostname()
    if meta["pack_host"] == here:
        raise DeleteRefused(f"{zp} was packed on this host ({here}); delete from another host")
    accepted = _read_wal(wal_path, cell)
    stats_before = {f: os.stat(cell / f) for f in files_now}
    manifest = verify(cell, zp, _wal_accepted=accepted)
    _, files_verified = _walk(cell)
    if files_verified != files_now:
        raise BundleMismatch(f"{cell}: file list changed during verification")
    with open(wal_path, "a") as fh:
        for f in files_verified:
            size, sha = manifest[f]
            fh.write(json.dumps({"cell": str(cell), "name": f, "size": size, "sha256": sha,
                                 "zip": str(zp), "host": here, "time": time.time()}) + "\n")
        fh.flush()
        os.fsync(fh.fileno())
    for f in files_verified:
        st, st0 = os.stat(cell / f), stats_before[f]
        if (st.st_size, st.st_mtime_ns) != (st0.st_size, st0.st_mtime_ns):
            raise BundleMismatch(f"{cell / f}: changed after verification; nothing deleted")
    for f in files_verified:
        os.unlink(cell / f)
    for root, _dnames, _fnames in os.walk(cell, topdown=False):
        os.rmdir(root)   # raises OSError (ENOTEMPTY) if anything new appeared
    return len(files_verified)
