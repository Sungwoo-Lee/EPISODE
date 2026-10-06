"""Generate (and verify) the modulator-capacity grid -- nine agent configs.

PLAIN LANGUAGE
--------------
The modulated agent carries a small second network (the "modulator") that reads the
agent's senses and, at every step, multiplies each neuron of the main network by a gain
and adds an offset (FiLM). Two of its size settings have never been changed in the
project's recent studies:

  mod_hidden_size  -- how many units the modulator's own recurrent network has (16 so far);
  grouping_size    -- how many neighbouring neurons of the main network share ONE
                      state-dependent gain/offset (1 so far, i.e. every neuron has its own).

This study trains a 3 x 3 grid of them at level 05 (the 10x10 world with body
temperature and campfires, fast healing in a bush):

  mod_hidden_size in {32, 64, 128}  x  grouping_size in {8, 16, 32}  = 9 agent configs.

The task layers are 128 neurons wide, so grouping 8 / 16 / 32 means 16 / 8 / 4
state-dependent gains per modulated layer. (The per-neuron learned baselines inside the
modulator stay per-neuron at every grouping; only the state-dependent part is grouped --
see src/models/neuromodulator.py, `_get_signal`.)

Design doc: docs/experiments/active/hypervigilance/NMN_CAPACITY_GRID_L05.md

WHERE THE COMMON PART COMES FROM
--------------------------------
Every key except the two above is READ from the reference agent of the fast-bush-healing
replication's level-05 modulated runs:

  configs/models/recurrent_ppo/nmn_input_site_grid_gaenorm/nmngaenorm_t16quad_ALL.yaml

That file is itself generated (by ../nmn_input_site_grid/generate_site_grid_arms.py) and is
NOT edited here. `--verify` checks the two-key claim mechanically, and also checks the
resolved training config against the replication run's SAVED config (the ground truth of
what that run trained with), so a drift anywhere in the config stack since 2026-10-05
fails here rather than at launch.

The seed is NOT in these files: the replication passed `--seed 42|43|44` on the command
line (its saved config shows top-level `seed: 43` for the s43 run while
training.seed stays 42), and this grid does the same. One config per cell serves all seeds.

USAGE (from anywhere; the script chdir's to the repo root itself)
-----------------------------------------------------------------
  python configs/models/recurrent_ppo/nmn_capacity_grid/generate_capacity_arms.py
      -> (re)writes the nine YAML files.
  ... --check
      -> writes nothing; fails if any file on disk differs from what this script generates.
  ... --verify
      -> --check, PLUS (on CPU):
         [1] each config vs the reference: flattened diff == exactly
             {agent.modulation.mod_hidden_size, agent.modulation.grouping_size};
         [2] each config resolved through train.py's merge order (+ the launch flags of the
             design doc) vs the replication run's saved models/config.yaml: the only
             differences allowed are the two keys and the run's names (tag, wandb.*);
         [3] each model CONSTRUCTED with the trainer's own seed-42 init key: modulator
             sizes, head widths, finite forward pass, finite non-zero gradient into every
             modulator head, the state-dependent gain constant within each group, and the
             task network's starting weights bit-identical to the reference model's.
This script lives under configs/ (not scripts/) on the precedent of the site-grid
generator: a config generator should not trigger the scripts dependency-map contract.
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

from src.utils.config import dump_config_yaml   # noqa: E402

REFERENCE_AGENT = 'configs/models/recurrent_ppo/nmn_input_site_grid_gaenorm/nmngaenorm_t16quad_ALL.yaml'
ENV_CONFIG = 'configs/environment/experiment/basic/05-campfire_thermal_10x10.yaml'
# The replication's level-05 modulated seed-42 run: its saved config is the ground truth.
REFERENCE_RUN = 'results/JAX_RecurrentPPO/20261005-160241_rppo_healrep_l05_t16quad_s42'
OUT_DIR = 'configs/models/recurrent_ppo/nmn_capacity_grid'

HIDDEN = (32, 64, 128)
GROUPING = (8, 16, 32)
TASK_WIDTH = 128
REF_HIDDEN, REF_GROUPING = 16, 1

# Launch flags fixed by the design doc (identical to the replication's level-05 runs).
EPISODES = 10000000
LOG_INTERVAL = 10
WANDB_GROUP = 'nmn_capacity_l05'
WANDB_JOB_TYPE = 'ablation'
TWO_KEYS = ['agent.modulation.grouping_size', 'agent.modulation.mod_hidden_size']


def stem(h, g):
    return 'nmncap_h%d_g%d' % (h, g)


def tag(h, g, seed):
    return 'rppo_nmncap_l05_h%dg%d_s%d' % (h, g, seed)


def _header(h, g):
    lines = [
        "# GENERATED FILE -- DO NOT EDIT BY HAND.",
        "# Regenerate with:",
        "#   python configs/models/recurrent_ppo/nmn_capacity_grid/generate_capacity_arms.py",
        "# Drift check (writes nothing):  ... generate_capacity_arms.py --check",
        "# Full check (two-key diff, saved-config diff, model build):  ... --verify",
        "#",
        "# Modulator-capacity grid, level 05 -- cell h%d g%d" % (h, g),
        "# Study: docs/experiments/active/hypervigilance/NMN_CAPACITY_GRID_L05.md",
        "#",
        "# Identical to %s" % REFERENCE_AGENT,
        "# (the replication's level-05 modulated agent: FiLM at encoder, GRU, actor and critic;",
        "# reads all 27 sensed numbers; temperature channel off; GAE_NORM returns) in every key",
        "# except two:",
        "#   modulation.mod_hidden_size  %3d   (reference %d)  -- units in the modulator's own GRU"
        % (h, REF_HIDDEN),
        "#   modulation.grouping_size    %3d   (reference %d)   -- neurons sharing one state-"
        "dependent gain/offset;" % (g, REF_GROUPING),
        "#                                     %d gains per modulated %d-wide layer (reference %d)"
        % (TASK_WIDTH // g, TASK_WIDTH, TASK_WIDTH // REF_GROUPING),
        "#",
        "# Seed is passed per run on the command line (--seed 42|43|44), as in the replication.",
        "",
    ]
    return "\n".join(lines) + "\n"


def build(h, g):
    base = yaml.safe_load(open(REFERENCE_AGENT))
    agent = copy.deepcopy(base['agent'])
    mod = agent['modulation']
    if (mod['mod_hidden_size'], mod['grouping_size']) != (REF_HIDDEN, REF_GROUPING):
        raise SystemExit("reference %s has mod_hidden_size=%r grouping_size=%r, expected %d/%d "
                         "-- refusing to generate." % (REFERENCE_AGENT, mod['mod_hidden_size'],
                                                       mod['grouping_size'], REF_HIDDEN, REF_GROUPING))
    if TASK_WIDTH % g:
        raise SystemExit("grouping %d does not divide the task width %d" % (g, TASK_WIDTH))
    mod['mod_hidden_size'] = h
    mod['grouping_size'] = g
    buf = io.StringIO()
    dump_config_yaml({'agent': agent}, buf)
    body = buf.getvalue()
    # Quote the sensor selector exactly as the reference file does, so that a plain text
    # diff against the reference (comments stripped) shows the two keys and nothing else.
    if body.count('input_sensors: all\n') != 1:
        raise SystemExit("expected one `input_sensors: all` line in the dumped agent block")
    body = body.replace('input_sensors: all\n', 'input_sensors: "all"\n')
    return stem(h, g) + '.yaml', _header(h, g) + body


def cells():
    return [(h, g) for h in HIDDEN for g in GROUPING]


def write_all(check_only=False):
    stale = []
    files = [build(h, g) for h, g in cells()]
    for fname, text in files:
        path = os.path.join(OUT_DIR, fname)
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
    """train.py's merge order (main(), 'Configuration Loading') + the design doc's launch flags."""
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

    print("[1] each config vs %s -- flattened diff must be exactly the two keys" % REFERENCE_AGENT)
    for h, g in cells():
        path = os.path.join(OUT_DIR, stem(h, g) + '.yaml')
        arm = _flatten(yaml.safe_load(open(path)))
        dk = _diff_keys(arm, ref)
        check(dk == TWO_KEYS and arm['agent.modulation.mod_hidden_size'] == h
              and arm['agent.modulation.grouping_size'] == g,
              "%s differs only in %s (h %d->%d, g %d->%d)"
              % (os.path.basename(path), dk, REF_HIDDEN, h, REF_GROUPING, g))

    print("[2] resolved config vs the replication run's SAVED config (%s/models/config.yaml)" % REFERENCE_RUN)
    saved = _flatten(yaml.safe_load(open(os.path.join(REFERENCE_RUN, 'models', 'config.yaml'))))
    # the reference agent itself first: proves the reconstruction of train.py's merge is faithful
    rcfg = _flatten(_resolve_like_train(REFERENCE_AGENT, 42, 'rppo_healrep_l05_t16quad_s42').to_dict())
    rd = _diff_keys(rcfg, saved)
    run_name_keys = ['wandb.group', 'wandb.job_type']
    check(sorted(rd) == sorted(run_name_keys),
          "reference agent resolved now == reference run's saved config, except the WandB "
          "group/job type this grid uses (got %s)" % rd)
    for k in rd:
        print("        %s: now %r | saved %r" % (k, rcfg.get(k), saved.get(k)))
    for h, g in cells():
        for seed in (42, 43, 44):
            t = tag(h, g, seed)
            c = _flatten(_resolve_like_train(os.path.join(OUT_DIR, stem(h, g) + '.yaml'), seed, t).to_dict())
            d = _diff_keys(c, saved)
            allowed = set(TWO_KEYS) | {'tag', 'wandb.name', 'seed'} | set(run_name_keys)
            check(set(d) <= allowed and set(TWO_KEYS) <= set(d),
                  "%s seed %d: differs from the saved config only in %s" % (stem(h, g), seed, d))

    print("[3] construct every model with the trainer's seed-42 init key (CPU)")
    cfg0 = _resolve_like_train(REFERENCE_AGENT, 42, 'x')
    params = load_env_params(cfg0)
    breakdown = get_observation_breakdown(params)
    env = ParallelEnv(params)
    _st, _obs = env.reset(jax.random.PRNGKey(0), 2)
    input_dim = int(_obs.shape[-1])
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

    ref_model = make(REFERENCE_AGENT)
    ref_task = task_params(ref_model)
    print("    reference (h16 g1): modulator parameters = %d; task-network parameters = %d"
          % (n_params(ref_model.modulator), sum(v.size for v in ref_task.values())))
    heads = ['head_unimodal', 'head_unimodal_add', 'head_multimodal', 'head_multimodal_add',
             'head_rnn', 'head_rnn_add', 'head_actor', 'head_actor_add', 'head_critic', 'head_critic_add']
    x = jax.random.normal(jax.random.PRNGKey(1), (3, input_dim))
    for h, g in cells():
        print("  %s" % stem(h, g))
        m = make(os.path.join(OUT_DIR, stem(h, g) + '.yaml'))
        mod = m.modulator
        check(mod.mod_hidden_size == h and mod.grouping_size == g, "modulator built with h=%d g=%d" % (h, g))
        check(mod.num_groups_hidden == TASK_WIDTH // g, "%d state-dependent gains per site" % (TASK_WIDTH // g))
        widths = {hn: tuple(getattr(mod, hn).kernel.value.shape) for hn in heads}
        check(all(s == (h, TASK_WIDTH // g) for s in widths.values()),
              "all 10 FiLM heads have kernel shape (%d, %d)" % (h, TASK_WIDTH // g))
        check(tuple(mod.gru.dense_h.kernel.value.shape)[0] == h, "modulator GRU state width %d" % h)
        check(m.site_encoder and m.site_rnn and m.site_actor and m.site_critic and not m.temperature_enabled
              and m.rnn_mechanism == 'activation', "sites all four, rnn_mechanism activation, temperature off")
        tp = task_params(m)
        same = tp.keys() == ref_task.keys() and all(np.array_equal(tp[k], ref_task[k]) for k in tp)
        check(same, "task-network starting weights bit-identical to the reference (same seed)")
        print("        modulator parameters = %d (reference %d)" % (n_params(mod), n_params(ref_model.modulator)))

        h0 = m.initial_state(batch_size=3)
        check(tuple(h0[1].shape) == (3, h), "initial modulator state shape (3, %d)" % h)
        logits, value, h1, info = m(x, h0)
        check(bool(jnp.all(jnp.isfinite(logits))) and bool(jnp.all(jnp.isfinite(value)))
              and logits.shape == (3, action_dim), "forward pass finite, logits (3, %d)" % action_dim)
        # second step from a non-zero modulator state, then check the grouping structure
        logits, value, h2, info = m(x, h1)
        dyn = np.asarray(info.z_actor) - np.asarray(mod.z_actor_baseline.value)
        grouped = dyn.reshape(3, TASK_WIDTH // g, g)
        check(np.allclose(grouped, grouped[..., :1]), "state-dependent actor gain constant within each group of %d" % g)
        check(not np.allclose(grouped[:, 0, 0], grouped[:, 1, 0]) or TASK_WIDTH // g == 1,
              "different groups get different gains")

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
        check(ok, "finite, non-zero gradient reaches every one of the 10 FiLM heads")

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
        os.makedirs(OUT_DIR, exist_ok=True)
        write_all()


if __name__ == '__main__':
    main()
