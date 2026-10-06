"""Generate (and verify) the modulator-input grid at level 05 -- four agent configs + eval specs.

PLAIN LANGUAGE
--------------
The modulated agent carries a small second network (the "modulator") that reads the
agent's senses and, at every step, multiplies each neuron of the main network by a gain
and adds an offset (FiLM). In the fast-bush-healing replication it read ALL of the
agent's senses. This study changes only WHAT it reads, at level 05 (the 10x10 world with
predators, rabbits, body temperature and campfires, fast healing in a bush):

  N   -- felt injury only                         ["Interoceptive Nociception"]          1 number
  I   -- fullness + felt injury                   ["Satiation", "Interoceptive Nociception"]  2
  IT  -- fullness + body temperature + felt injury ["Satiation", "Body Temperature",
                                                    "Interoceptive Nociception"]          3
  X   -- the outside world only                   ["Extero Nociception", "Thermoception",
                                                    "Olfaction", "Collision", "Visual"]  49

Level 05 senses 58 numbers in all: Satiation 1, Body Temperature 1, Interoceptive
Nociception 1, Extero Nociception 1, Thermoception 5, Olfaction 25, Collision 5,
Proprioception 6, Visual 13 (get_observation_breakdown, checked live by --verify).

PROPRIOCEPTION (the agent's previous action, 6 numbers) IS IN NO CELL. It is neither a
body-state signal nor a signal about the outside world, and the September input grid
excluded it from both restricted slices for that reason (user decision 2026-09-07, see
../nmn_input_site_grid/generate_site_grid_arms.py). Keeping the same rule keeps X
comparable to the September "outside world only" slice. Consequence: IT and X together
are 52 of the 58 numbers, not all of them.

The MAIN network still reads every sense in every cell. Only the modulator's input
changes. (An exclusive-input version, where the main network loses what the modulator
gets, is a separate follow-up; it needs code.)

Design doc: docs/experiments/active/hypervigilance/NMN_INPUT_L05.md

WHERE THE COMMON PART COMES FROM
--------------------------------
Every key except `agent.modulation.input_sensors` is READ from the reference agent of the
fast-bush-healing replication's level-05 modulated runs:

  configs/models/recurrent_ppo/nmn_input_site_grid_gaenorm/nmngaenorm_t16quad_ALL.yaml

That file is itself generated (by ../nmn_input_site_grid/generate_site_grid_arms.py) and is
NOT edited here. `--verify` checks the one-key claim mechanically, and checks the resolved
training config against the replication run's SAVED config.

The seed is NOT in these files: --seed 42|43|44 on the command line, as in the replication
and the capacity grid.

USAGE (from anywhere; the script chdir's to the repo root itself)
-----------------------------------------------------------------
  python configs/models/recurrent_ppo/nmn_input_l05/generate_input_arms.py
      -> (re)writes the four agent YAMLs and the eight eval-sweep specs.
  ... --check
      -> writes nothing; fails if any file on disk differs from what this script generates.
  ... --verify
      -> --check, PLUS (on CPU):
         [1] each config vs the reference: flattened diff == exactly
             {agent.modulation.input_sensors};
         [2] each config resolved through train.py's merge order (+ the launch flags of the
             design doc) vs the replication run's saved models/config.yaml: the only
             differences allowed are input_sensors, seed and the run's names (tag, wandb.*);
         [3] the live level-05 observation breakdown equals the one this study was designed on;
         [4] each model CONSTRUCTED with the trainer's own seed-42 init key: the modulator's
             input columns are exactly the named sensors' columns, its first layer is that
             wide, the task network's starting weights are bit-identical to the reference's,
             forward pass finite, finite non-zero gradient into the modulator's input layer
             and every FiLM head; and ISOLATION: changing every column the cell does NOT
             read leaves the modulator's state and outputs bit-identical over two steps,
             while changing a column it DOES read changes them.
This script lives under configs/ (not scripts/) on the precedent of the site-grid and
capacity-grid generators: a config generator should not trigger the scripts dependency-map
contract.
"""
import argparse
import copy
import difflib
import io
import os
import sys

import yaml

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.abspath(os.path.join(_HERE, *(['..'] * 4)))
sys.path.insert(0, _ROOT)
os.chdir(_ROOT)

from src.utils.config import dump_config_yaml, _FlowListDumper   # noqa: E402


class _QuotedStr(str):
    """Dumps with explicit double quotes (sensor names contain spaces; spelling is load-bearing)."""


_FlowListDumper.add_representer(
    _QuotedStr,
    lambda dumper, data: dumper.represent_scalar('tag:yaml.org,2002:str', str(data), style='"'))

REFERENCE_AGENT = 'configs/models/recurrent_ppo/nmn_input_site_grid_gaenorm/nmngaenorm_t16quad_ALL.yaml'
ENV_CONFIG = 'configs/environment/experiment/basic/05-campfire_thermal_10x10.yaml'
# The replication's level-05 modulated seed-42 run: its saved config is the ground truth.
REFERENCE_RUN = 'results/JAX_RecurrentPPO/20261005-160241_rppo_healrep_l05_t16quad_s42'
OUT_DIR = 'configs/models/recurrent_ppo/nmn_input_l05'
EVAL_DIR = 'configs/eval_sweeps/nmninp'
DESIGN_DOC = 'docs/experiments/active/hypervigilance/NMN_INPUT_L05.md'

# Level-05 observation layout this study was designed on (checked live by --verify [3]).
BREAKDOWN_L05 = {'Satiation': 1, 'Body Temperature': 1, 'Interoceptive Nociception': 1,
                 'Extero Nociception': 1, 'Thermoception': 5, 'Olfaction': 25, 'Collision': 5,
                 'Proprioception': 6, 'Visual': 13}

# (cell code, sensor list, plain-language description). Order = run order in the manifest.
CELLS = [
    ('N', ["Interoceptive Nociception"],
     "felt injury only -- the smoothed internal ache that is the agent's only trace of its wound"),
    ('I', ["Satiation", "Interoceptive Nociception"],
     "the body's fullness and felt injury (the September 'body-only' slice)"),
    ('IT', ["Satiation", "Body Temperature", "Interoceptive Nociception"],
     "fullness, body temperature and felt injury -- every body-state signal level 05 has"),
    ('X', ["Extero Nociception", "Thermoception", "Olfaction", "Collision", "Visual"],
     "the outside world only: contact pain, felt air/fire heat, smell, collision, vision "
     "(proprioception excluded, as in September)"),
]
SEEDS_STAGE1 = (42,)
SEEDS_STAGE2 = (43, 44)

# Launch flags fixed by the design doc (identical to the replication's level-05 runs).
EPISODES = 10000000
LOG_INTERVAL = 10
WANDB_GROUP = 'nmn_input_l05'
WANDB_JOB_TYPE = 'ablation'
ONE_KEY = ['agent.modulation.input_sensors']

# Eval scene sets: (set name, probe folder) -- identical to configs/eval_sweeps/healrep/healrep_l05_*.
EVAL_SETS = [
    ('neutral', 'configs/environment/experiment/behavior_probes/thermal/neutral_clean'),
    ('own', 'configs/environment/experiment/behavior_probes/hvsmell/two_channel'),
    ('grid', 'configs/environment/experiment/behavior_probes/injury_grid/neutral_clean'),
    ('gridchase', 'configs/environment/experiment/behavior_probes/injury_grid/chase_neutral_clean'),
]
EVAL_NODES = [109, 113]   # placeholder; confirm free nodes before running a sweep


def stem(code):
    return 'nmninp_%s' % code


def tag(code, seed):
    return 'rppo_nmninp_l05_%s_s%d' % (code, seed)


def width(sensors):
    return sum(BREAKDOWN_L05[s] for s in sensors)


def _header(code, sensors, desc):
    lines = [
        "# GENERATED FILE -- DO NOT EDIT BY HAND.",
        "# Regenerate with:",
        "#   python configs/models/recurrent_ppo/nmn_input_l05/generate_input_arms.py",
        "# Drift check (writes nothing):  ... generate_input_arms.py --check",
        "# Full check (one-key diff, saved-config diff, model build, input isolation):  ... --verify",
        "#",
        "# Modulator-input grid, level 05 -- cell %s" % code,
        "# Study: %s" % DESIGN_DOC,
        "#",
        "# Identical to %s" % REFERENCE_AGENT,
        "# (the replication's level-05 modulated agent: FiLM at encoder, GRU, actor and critic;",
        "# 16-unit modulator, grouping 1; temperature channel off; GAE_NORM returns) in every key",
        "# except one:",
        "#   modulation.input_sensors -- what the MODULATOR reads (reference: \"all\", 58 numbers",
        "#   at level 05). Here: %s" % desc,
        "#   = %d of the 58 numbers. The main network still reads all 58." % width(sensors),
        "#",
        "# Seed is passed per run on the command line (--seed 42|43|44), as in the replication.",
        "",
    ]
    return "\n".join(lines) + "\n"


def build(code, sensors, desc):
    base = yaml.safe_load(open(REFERENCE_AGENT))
    agent = copy.deepcopy(base['agent'])
    mod = agent['modulation']
    if mod['input_sensors'] != 'all':
        raise SystemExit("reference %s has input_sensors=%r, expected 'all' -- refusing to generate."
                         % (REFERENCE_AGENT, mod['input_sensors']))
    unknown = [s for s in sensors if s not in BREAKDOWN_L05]
    if unknown:
        raise SystemExit("cell %s names sensors absent at level 05: %s" % (code, unknown))
    mod['input_sensors'] = [_QuotedStr(s) for s in sensors]
    buf = io.StringIO()
    dump_config_yaml({'agent': agent}, buf)
    return os.path.join(OUT_DIR, stem(code) + '.yaml'), _header(code, sensors, desc) + buf.getvalue()


def build_eval(set_name, probe, stage):
    seeds = SEEDS_STAGE1 if stage == 1 else SEEDS_STAGE2
    n = len(CELLS) * len(seeds)
    head = [
        "# GENERATED FILE -- DO NOT EDIT BY HAND (generator:",
        "#   configs/models/recurrent_ppo/nmn_input_l05/generate_input_arms.py).",
        "# Modulator-input grid, level 05 -- stage %d runs (%d) -- test scenes '%s' (%s)."
        % (stage, n, set_name, probe),
        "# Design: %s (Section 5, readout)." % DESIGN_DOC,
        "# Same probe folder, conditions, episodes, x axis and measures as",
        "# configs/eval_sweeps/healrep/healrep_l05_%s_rppo.yaml, whose output holds the reference runs."
        % set_name,
        "# Run paths are globs on the planned tag; each must resolve to exactly ONE run folder",
        "# (run_sweep.py refuses 0 or 2+ matches -- after a relaunch, pin the live folder by hand).",
        "# Nodes are a placeholder: confirm free nodes (gpu-status + diary) before launching the sweep.",
    ]
    if stage == 2:
        head.append("# Stage 2 is run only for cells the user advances: delete the rows of the other cells.")
    spec = {
        'name': 'nmninp_l05_%s_stage%d' % (set_name, stage),
        'algo': 'rppo',
        'output_dir': 'results/eval/avoidance/metrics_history_rppo_nmninp/l05_%s' % set_name,
        'probe': probe,
        'conditions': 'all',
        'episodes': 30,
        'nodes': list(EVAL_NODES),
        'x_axis': 'steps',
        'plot_measures': ['bush_hiding', 'survival_steps'],
        'runs': [{'label': 'l05_%s_s%d' % (code, s),
                  'path': 'results/JAX_RecurrentPPO/*_%s' % tag(code, s)}
                 for code, _sens, _d in CELLS for s in seeds],
    }
    body = yaml.safe_dump(spec, sort_keys=False, default_flow_style=False)
    return (os.path.join(EVAL_DIR, 'nmninp_l05_%s_stage%d_rppo.yaml' % (set_name, stage)),
            "\n".join(head) + "\n" + body)


def all_files():
    files = [build(c, s, d) for c, s, d in CELLS]
    files += [build_eval(n, p, st) for st in (1, 2) for n, p in EVAL_SETS]
    return files


def write_all(check_only=False):
    stale = []
    files = all_files()
    for path, text in files:
        if check_only:
            if not os.path.exists(path):
                stale.append("%s: MISSING on disk" % path)
                continue
            on_disk = open(path).read()
            if on_disk != text:
                diff = "\n".join(difflib.unified_diff(on_disk.splitlines(), text.splitlines(),
                                                      path + ' (on disk)', path + ' (generated)',
                                                      lineterm=''))
                stale.append("%s: DIFFERS from generated output\n%s" % (path, diff))
        else:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, 'w') as f:
                f.write(text)
            print("wrote %s" % path)
    if check_only:
        if stale:
            print("\n".join(stale))
            raise SystemExit("--check FAILED: %d of %d files drifted." % (len(stale), len(files)))
        print("--check OK: all %d files match the generator byte-for-byte." % len(files))


def _flatten(d, prefix=''):
    flat = {}
    for k, v in d.items():
        key = "%s.%s" % (prefix, k) if prefix else str(k)
        if isinstance(v, dict):
            flat.update(_flatten(v, key))
        else:
            flat[key] = v
    return flat


def _diff_keys(a, b):
    return sorted(set(a) ^ set(b)) + sorted(k for k in set(a) & set(b) if a[k] != b[k])


def _resolve_like_train(agent_path, seed, run_tag):
    """train.py's merge order (main(), 'Configuration Loading') + the design doc's launch flags.

    Copied from the capacity-grid generator, whose reconstruction was validated by reproducing
    the replication run's saved config; [2] below re-validates it on the reference agent.
    """
    from src.utils.config import Config, get_default_config
    from src.environment.config_loader import load_env_config
    from src.utils.rolling_logging import resolve_logging_cfg
    cfg = get_default_config()
    cfg.merge(Config.load_yaml('configs/train/default.yaml'))
    cfg.merge(Config.load_yaml('configs/train/recurrent_ppo.yaml'))
    cfg.merge(load_env_config('configs/evaluation/default.yaml'))
    cfg.merge(Config.load_yaml('configs/logger/wandb.yaml'))
    cfg.merge(Config.load_yaml('configs/visualization/default.yaml'))
    cfg.merge(load_env_config(ENV_CONFIG))
    cfg.merge(Config.load_yaml(agent_path))
    cfg.set('wandb.group', WANDB_GROUP)
    cfg.set('wandb.job_type', WANDB_JOB_TYPE)
    cfg.set('wandb.name', run_tag)
    cfg.set('tag', run_tag)
    cfg.set('seed', seed)
    cfg.set('episodes', EPISODES)
    lc = resolve_logging_cfg(cfg.get, defaults={'smoothing_episodes': 5000, 'interval_episodes': 4000,
                                                'smoothing_iters': 100, 'interval_iters': 50})
    cfg.set('training.num_envs', cfg.get_mandatory('training.num_envs'))
    cfg.set('training.log_interval', LOG_INTERVAL)
    cfg.set('training.log_accumulate', cfg.get('training.log_accumulate', True))
    if lc is not None:
        cfg.set('logging.episode.smoothing_episodes', lc['smoothing_episodes'])
        cfg.set('logging.episode.interval_episodes', lc['interval_episodes'])
        cfg.set('logging.step.smoothing_iters', lc['smoothing_iters'])
        cfg.set('logging.step.interval_iters', lc['interval_iters'])
    return cfg


def verify():
    os.environ.setdefault('JAX_PLATFORMS', 'cpu')
    import jax
    import jax.numpy as jnp
    import numpy as np
    from flax import nnx
    from src.environment.config_loader import load_env_params
    from src.environment.sensor import get_observation_breakdown
    from src.environment.wrapper import ParallelEnv
    from src.models.recurrent_ppo_network import ActorCriticRNN
    from src.utils.init_keys import trainer_init_keys

    failures = []

    def check(cond, msg):
        print("    %s %s" % ("ok  " if cond else "FAIL", msg))
        if not cond:
            failures.append(msg)

    ref = _flatten(yaml.safe_load(open(REFERENCE_AGENT)))

    print("[1] each config vs %s -- flattened diff must be exactly input_sensors" % REFERENCE_AGENT)
    for code, sensors, _d in CELLS:
        path = os.path.join(OUT_DIR, stem(code) + '.yaml')
        arm = _flatten(yaml.safe_load(open(path)))
        dk = _diff_keys(arm, ref)
        check(dk == ONE_KEY and arm[ONE_KEY[0]] == sensors,
              "%s differs only in %s -> %s" % (os.path.basename(path), dk, arm[ONE_KEY[0]]))

    print("[2] resolved config vs the replication run's SAVED config (%s/models/config.yaml)" % REFERENCE_RUN)
    saved = _flatten(yaml.safe_load(open(os.path.join(REFERENCE_RUN, 'models', 'config.yaml'))))
    rcfg = _flatten(_resolve_like_train(REFERENCE_AGENT, 42, 'rppo_healrep_l05_t16quad_s42').to_dict())
    rd = _diff_keys(rcfg, saved)
    run_name_keys = ['wandb.group', 'wandb.job_type']
    check(sorted(rd) == sorted(run_name_keys),
          "reference agent resolved now == reference run's saved config, except the WandB "
          "group/job type this grid uses (got %s)" % rd)
    for k in rd:
        print("        %s: now %r | saved %r" % (k, rcfg.get(k), saved.get(k)))
    for code, sensors, _d in CELLS:
        for seed in SEEDS_STAGE1 + SEEDS_STAGE2:
            t = tag(code, seed)
            c = _flatten(_resolve_like_train(os.path.join(OUT_DIR, stem(code) + '.yaml'), seed, t).to_dict())
            d = _diff_keys(c, saved)
            allowed = set(ONE_KEY) | {'tag', 'wandb.name', 'seed'} | set(run_name_keys)
            check(set(d) <= allowed and set(ONE_KEY) <= set(d) and c['seed'] == seed
                  and c['tag'] == t and c['wandb.name'] == t,
                  "%s seed %d: differs from the saved config only in %s" % (stem(code), seed, d))

    print("[3] live level-05 observation breakdown")
    cfg0 = _resolve_like_train(REFERENCE_AGENT, 42, 'x')
    params = load_env_params(cfg0)
    breakdown = get_observation_breakdown(params)
    env = ParallelEnv(params)
    _st, _obs = env.reset(jax.random.PRNGKey(0), 2)
    input_dim = int(_obs.shape[-1])
    check(dict(breakdown) == BREAKDOWN_L05 and list(breakdown) == list(BREAKDOWN_L05),
          "breakdown (names, order, widths) == the design's %s" % BREAKDOWN_L05)
    check(input_dim == sum(BREAKDOWN_L05.values()), "observation width %d == 58" % input_dim)
    offsets, cur = {}, 0
    for name, dim in BREAKDOWN_L05.items():
        offsets[name] = list(range(cur, cur + dim))
        cur += dim

    action_dim = 4 + int(params.rest_action_enabled) + int(params.eat_action_enabled)
    _k, _ek, init_key = trainer_init_keys(42)

    def make(agent_path):
        c = _resolve_like_train(agent_path, 42, 'x')
        return ActorCriticRNN(
            input_dim=input_dim, action_dim=action_dim,
            hidden_size=c.get_mandatory('agent.hidden_size'), rngs=nnx.Rngs(init_key),
            rnn_type=c.get_mandatory('agent.rnn_type'), activation=c.get_mandatory('agent.activation'),
            modulation_config=c.get('agent.modulation'), observation_breakdown=breakdown,
            encoding_config=c.to_dict().get('agent', {}))

    def task_params(model):
        flat = {}
        for path, leaf in jax.tree_util.tree_flatten_with_path(nnx.state(model, nnx.Param))[0]:
            key = jax.tree_util.keystr(path)
            if 'modulator' not in key:
                flat[key] = np.asarray(leaf)
        return flat

    def n_params(module):
        return int(sum(np.asarray(x).size for x in jax.tree_util.tree_leaves(nnx.state(module, nnx.Param))))

    print("[4] construct every model with the trainer's seed-42 init key (CPU)")
    ref_model = make(REFERENCE_AGENT)
    ref_task = task_params(ref_model)
    print("    reference (all 58): modulator parameters = %d; task-network parameters = %d"
          % (n_params(ref_model.modulator), sum(v.size for v in ref_task.values())))
    heads = ['head_unimodal', 'head_unimodal_add', 'head_multimodal', 'head_multimodal_add',
             'head_rnn', 'head_rnn_add', 'head_actor', 'head_actor_add', 'head_critic', 'head_critic_add']
    z_fields = ['z_unimodal', 'z_unimodal_add', 'z_multimodal', 'z_multimodal_add', 'z_rnn', 'z_rnn_add',
                'z_actor', 'z_actor_add', 'z_critic', 'z_critic_add']
    key = jax.random.PRNGKey(1)
    x = jax.random.normal(key, (3, input_dim)) * 2.0
    for code, sensors, _d in CELLS:
        print("  %s  %s" % (stem(code), sensors))
        m = make(os.path.join(OUT_DIR, stem(code) + '.yaml'))
        expected = tuple(i for s in sensors for i in offsets[s])
        check(m.mod_input_idx == expected and not m._mod_input_is_all,
              "modulator reads exactly columns %s (%d numbers)"
              % ((expected if len(expected) <= 6 else '%d..%d (with gaps)' % (expected[0], expected[-1])),
                 len(expected)))
        check(tuple(m.modulator.gru.dense_i.kernel.value.shape)[0] == len(expected),
              "modulator input layer is %d wide" % len(expected))
        check(m.modulator.mod_hidden_size == 16 and m.modulator.grouping_size == 1,
              "modulator size unchanged (16 units, grouping 1)")
        check(m.site_encoder and m.site_rnn and m.site_actor and m.site_critic and not m.temperature_enabled
              and m.rnn_mechanism == 'activation', "sites all four, rnn_mechanism activation, temperature off")
        tp = task_params(m)
        same = tp.keys() == ref_task.keys() and all(np.array_equal(tp[k], ref_task[k]) for k in tp)
        check(same, "task-network starting weights bit-identical to the reference (same seed)")
        print("        modulator parameters = %d (reference %d)" % (n_params(m.modulator), n_params(ref_model.modulator)))

        h0 = m.initial_state(batch_size=3)
        logits, value, h1, info = m(x, h0)
        logits, value, h2, info = m(x, h1)
        check(bool(jnp.all(jnp.isfinite(logits))) and bool(jnp.all(jnp.isfinite(value)))
              and logits.shape == (3, action_dim), "forward pass finite, logits (3, %d)" % action_dim)

        # Isolation: perturb every column NOT read -> modulator state + outputs bit-identical.
        excluded = np.array(sorted(set(range(input_dim)) - set(expected)))
        noise = jax.random.normal(jax.random.PRNGKey(7), (3, len(excluded))) * 3.0
        x_ex = x.at[:, excluded].add(noise)
        _l, _v, g1, info_e1 = m(x_ex, h0)
        _l, _v, g2, info_e2 = m(x_ex, g1)
        iso = bool(np.array_equal(np.asarray(g2[1]), np.asarray(h2[1])))
        iso &= all(np.array_equal(np.asarray(getattr(info_e2, f)), np.asarray(getattr(info, f)))
                   for f in z_fields)
        check(iso, "changing the %d unread columns leaves modulator state and FiLM outputs bit-identical"
              % len(excluded))
        # ...and the task network DOES see them (it still reads all 58).
        check(not np.array_equal(np.asarray(_l), np.asarray(logits)),
              "the main network's output does change with the unread columns (it still reads all 58)")
        # Sensitivity: perturb one column that IS read -> modulator state changes.
        x_in = x.at[:, expected[0]].add(1.5)
        _l, _v, k1, _i = m(x_in, h0)
        check(not np.array_equal(np.asarray(k1[1]), np.asarray(h1[1])),
              "changing a read column (%d) changes the modulator state" % expected[0])

        def loss_fn(model):
            lg, v, _h, _i = model(x, model.initial_state(batch_size=3))
            lg2, v2, _h2, _i2 = model(x, _h)
            return jnp.sum(jax.nn.log_softmax(lg2)[:, 0]) + jnp.sum(v2)
        grads = nnx.grad(loss_fn)(m)
        gmod = grads.modulator
        ok = True
        for hn in heads:
            gk = np.asarray(getattr(gmod, hn).kernel.value)
            ok &= bool(np.all(np.isfinite(gk))) and float(np.abs(gk).sum()) > 0
        gi = np.asarray(gmod.gru.dense_i.kernel.value)
        ok_in = bool(np.all(np.isfinite(gi))) and float(np.abs(gi).sum()) > 0
        check(ok, "finite, non-zero gradient reaches every one of the 10 FiLM heads")
        check(ok_in, "finite, non-zero gradient reaches the modulator's input layer")

    if failures:
        raise SystemExit("--verify FAILED: %d check(s):\n  %s" % (len(failures), "\n  ".join(failures)))
    print("\n--verify OK")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--check', action='store_true')
    ap.add_argument('--verify', action='store_true')
    a = ap.parse_args()
    if a.check or a.verify:
        write_all(check_only=True)
        if a.verify:
            verify()
    else:
        write_all()


if __name__ == '__main__':
    main()
