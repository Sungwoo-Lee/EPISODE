"""Markdown tables for THIRST_TASK §6 from validate_all.json (no hand-typed numbers)."""
import json, sys

R = json.load(open(sys.argv[1]))
pct = lambda v: f"{100 * v:.2f} %"

print("**6.1 Load**\n")
print("| Cell | Grid | sensor_radius | Pond | Smell per pond cell (ch. 0) | Whole pond (ch. 0) | Obs width (breakdown / real `get_observation`) | Breakdown modalities missing from noise | Noise on |")
print("|---|---|---|---|---|---|---|---|---|")
for k, r in R.items():
    L = r["load"]
    print(f"| {k} | {L['grid']} | {L['sensor_radius']:g} | {L['pond_size'][0]}×{L['pond_size'][1]} | "
          f"{L['pond_cell_property'][0]:.4f} | {L['pond_total_smell'][0]:.4f} | {L['obs_width_breakdown']} / "
          f"{L['obs_width_real']} | {L['noise_missing_for_breakdown'] or 'none'} | {L['noise_enabled']} |")

print("\n**6.2 Placement** (2,000 real resets per world, PRNG key 7)\n")
print("| Cell | Active entity outside its own area (fallback signature) | Active entities at (0,0) per reset: observed / uniform expectation / other corners | Two active entities on one cell | Active entity on the pond | Agent starts on the pond | Fire pairs closer than 4 | Agent starts on a burning fire | Pond corner frequencies | Mean active: food / ambushers / fires / animals |")
print("|---|---|---|---|---|---|---|---|---|---|")
for k, r in R.items():
    P = r["placement"]
    c = P["active_counts_mean"]
    fq = " / ".join(f"{v:.3f}" for v in P["pond_topleft_freq"].values())
    print(f"| {k} | {pct(P['fallback_signature_active_outside_own_area'])} | "
          f"{P['active_slots_at_0_0_per_reset']:.3f} / {P['active_slots_at_0_0_expected_if_uniform']:.3f} / "
          f"{P['active_slots_at_other_corners_mean']:.3f} | {pct(P['overlap_two_active_share_a_cell'])} | "
          f"{pct(P['any_active_on_pond'])} | {pct(P['agent_starts_on_pond'])} | "
          f"{pct(P['active_fire_pairs_closer_than_separation'])} | {pct(P['agent_starts_on_burning_fire'])} | {fq} | "
          f"{c['food']:.1f} / {c['ambushers']:.1f} / {c['fires']:.1f} / {c['animals']:.1f} |")

print("\n**6.3 Smell direction** (channel 0 = food + pond; every non-source cell of 2,000 real layouts as a hypothetical agent position)\n")
print("| Cell | Any channel-0 smell in range (random cell) | d=2: points to nearest / chance / in range (cells) | d=5 | d=10 | d=15 |")
print("|---|---|---|---|---|---|")
for k, r in R.items():
    S = r["smell"]
    row = f"| {k} | {pct(S['any_channel0_smell_in_range_at_a_random_cell'])} |"
    for d in (2, 5, 10, 15):
        b = S[f"d={d}"]
        if b["n_cells"] == 0:
            row += " — (no cell at this distance) |"
        else:
            row += (f" {100 * b['points_to_nearest']:.1f} % / {100 * b['chance']:.1f} % / "
                    f"{100 * b['smell_in_range']:.1f} % (n={b['n_cells']:,}) |")
    print(row)

print("\n**6.4 Walk from the start cell to the nearest pond cell** (Manhattan steps, 2,000 resets)\n")
print("| Cell | Mean | Median | 95th pct | Max |")
print("|---|---|---|---|---|")
for k, r in R.items():
    w = r["walk"]
    if k.endswith("sW"):
        print(f"| {k[:3]} (all reaches) | {w['start_to_pond_mean']:.1f} | {w['p50']:.0f} | {w['p95']:.0f} | {w['max']} |")
