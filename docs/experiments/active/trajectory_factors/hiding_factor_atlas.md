# Hiding Factor Atlas — every environment parameter, and whether it has been tested

**Shareable page:** https://claude.ai/code/artifact/36369fd2-66a7-4b66-8077-21f0c83282cd
**Republish:** edit `hiding_factor_atlas.html` in this folder, then publish it to the URL above.
From a session that did not publish it, read that URL first and pass it as `url` — publishing
without it makes a second, separate artifact instead of a new version of this one. Go through the
[`publish-page`](../../../../.claude/skills/publish-page/SKILL.md) skill, not the `Artifact` tool
directly.

## What this is

A catalogue of **all 65 settings the grid-world environment has**, written in plain language, each
annotated with what it does, whether the world rerolls it from one episode to the next, where it is
recorded, and whether any study has yet tested it as a driver of **bush hiding** (the share of an
episode's steps the agent spends standing in a bush).

It exists because the hiding work so far has tested 15 factors and there was no single place saying
what the other 50 are. The organising idea is **cadence** — a value the environment rerolls before
every episode is causally identified and free to analyse from data already collected, while a value
pinned in the config file cannot be studied without training another agent. That distinction decides
what every open question on the list costs.

**This is an inventory, not an analysis.** Nothing on the page is measured; no entry claims a
parameter does or does not move hiding, except where it restates a published result.

## Reference world

The config chain of the arm of the resting-bonus sweep where resting earns no extra healing — the
agent the published hiding study analysed:

- [`04-restprem_a01.yaml`](../../../../configs/environment/experiment/basic_bushrefuge_restpremium/04-restprem_a01.yaml)
- [`04-jump_attack_10x10.yaml`](../../../../configs/environment/experiment/basic_bushrefuge/04-jump_attack_10x10.yaml)
- [`03-random_init_10x10.yaml`](../../../../configs/environment/experiment/basic_bushrefuge/03-random_init_10x10.yaml)
- [`default.yaml`](../../../../configs/environment/default.yaml)

## Related

- [[a01_hiding_drivers]] — the million-episode factor analysis whose 15 tested factors this extends
- [[a01_factor_analysis]] — the first pass, and the pipeline's end-to-end check
- [[sensor_ladder]] — the fourteen-arm study that varied the sensory settings listed here as fixed
- [[INJURY_HIDING_SIGN_RECONCILIATION]] — why "hides more when injured" and "hides less" are both true
- [[TRAJECTORY_STORE_SCHEMA]] — the per-episode draw columns every `ep` entry is recorded in
