"""Hand-computable checks for `scripts/analysis/nmn/spectral_bound.py` (method 1).

Plain-language context: the module under test answers a ceiling question about the
neuromodulator — *given only the trained weights, how far apart can the network's
output be for two different things the modulator might be feeling?* It is a chain of
small inequalities (a per-unit sum of absolute weights, a largest singular value, a
GRU derivative bound, a couple of operator norms multiplied together), and every link
is the kind of arithmetic that looks right whether or not it is.

So these tests do not re-derive the chain in the test file — that would just echo the
same mistake back. They pin each link to a number worked out by hand on a matrix
small enough to do on paper, and then pin the assembled end-to-end actor-site bound
to a number assembled from those same hand values. If someone changes a 1-norm to a
2-norm, drops the factor of 2 that comes from the modulator state living in
`[-1, 1]` rather than `[0, 1]`, or reverses the `min` that picks the tighter of two
routes, at least one of these fails.

The worked example, once, in full (used by several tests below):

    modulator hidden width m = 2, modulated layer width H = 2, grouping_size = 1

    gain head kernel   K_g = [[1, -2],
                              [3,  4]]
        column 1-norms      = [1+3, 2+4] = [4, 6]
        reachable swing     = 2 * [4, 6] = [8, 12]        (factor 2: opposite corners)
        K_g' K_g            = [[10, 10], [10, 20]]
        eigenvalues         = 15 +/- 5*sqrt(5)
        sigma_max(K_g)      = sqrt(15 + 5*sqrt(5)) ~ 5.1167

    offset head kernel K_b = identity(2)
        swing               = [2, 2],  sigma_max = 1
"""
import math
import os
import sys

import numpy as np
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from scripts.analysis.nmn import spectral_bound as sb   # noqa: E402


K_GAIN = np.array([[1.0, -2.0], [3.0, 4.0]])
SIGMA_GAIN = math.sqrt(15.0 + 5.0 * math.sqrt(5.0))     # ~5.116672
K_OFFSET = np.eye(2)


# --------------------------------------------------------------------------
# Link 1 — the per-unit reachable swing
# --------------------------------------------------------------------------

def test_column_l1_is_the_sum_of_absolute_weights_per_output_unit():
    # Column sums of |K|: unit 0 gets |1| + |3| = 4, unit 1 gets |-2| + |4| = 6.
    assert np.allclose(sb.column_l1(K_GAIN), [4.0, 6.0])


def test_column_l1_rejects_a_non_matrix():
    with pytest.raises(ValueError, match="2-D kernel"):
        sb.column_l1(np.array([1.0, 2.0, 3.0]))


def test_sigma_max_of_a_diagonal_matrix_is_its_largest_entry():
    assert sb.sigma_max(np.diag([3.0, -4.0])) == pytest.approx(4.0)


def test_sigma_max_matches_the_hand_eigenvalue_of_the_worked_example():
    assert sb.sigma_max(K_GAIN) == pytest.approx(SIGMA_GAIN, rel=1e-12)


def test_expand_groups_repeats_each_group_across_its_units_and_truncates():
    # grouping_size 2 over a 3-wide layer: groups [5, 7] -> units [5, 5, 7].
    assert np.allclose(sb.expand_groups(np.array([5.0, 7.0]), 2, 3), [5.0, 5.0, 7.0])
    assert np.allclose(sb.expand_groups(np.array([5.0, 7.0]), 2, 4), [5.0, 5.0, 7.0, 7.0])


def test_expand_groups_refuses_a_head_too_narrow_to_cover_the_layer():
    with pytest.raises(ValueError, match="cannot cover it"):
        sb.expand_groups(np.array([5.0, 7.0]), 1, 4)


def test_head_stats_swing_is_twice_the_column_l1_not_once():
    """The factor of 2 is load-bearing: the modulator state ranges over [-1, 1], so
    two contexts can sit at OPPOSITE corners of the cube. Halving it would understate
    every bound in this module by exactly 2x."""
    st = sb.head_stats(K_GAIN, bias=np.zeros(2), baseline=np.zeros(2),
                       grouping_size=1, target_width=2)
    assert st["swing_max"] == pytest.approx(12.0)
    assert st["swing_mean"] == pytest.approx(10.0)     # mean of [8, 12]
    assert st["swing_min"] == pytest.approx(8.0)


def test_head_stats_constant_part_is_head_bias_plus_learned_baseline():
    st = sb.head_stats(K_GAIN, bias=np.array([1.0, 1.0]),
                       baseline=np.array([-0.25, 0.75]),
                       grouping_size=1, target_width=2)
    assert st["const_min"] == pytest.approx(0.75)       # 1 + (-0.25)
    assert st["const_max"] == pytest.approx(1.75)       # 1 + 0.75
    assert st["const_mean"] == pytest.approx(1.25)


def test_head_stats_takes_the_tighter_of_the_two_l2_routes():
    """Two valid ceilings on ||delta gamma||_2 exist -- the spectral route
    2*sqrt(m)*sigma and the per-unit route sqrt(H)*swing_max. The module must report
    the smaller. On the worked example the spectral route wins (14.47 < 16.97)."""
    st = sb.head_stats(K_GAIN, np.zeros(2), np.zeros(2), 1, 2)
    spectral = 2.0 * math.sqrt(2) * SIGMA_GAIN          # ~14.4722
    per_unit = math.sqrt(2) * 12.0                      # ~16.9706
    assert spectral < per_unit
    assert st["dev_l2_max"] == pytest.approx(spectral, rel=1e-12)
    assert st["dev_linf_max"] == pytest.approx(12.0)


# --------------------------------------------------------------------------
# Link 2 — the GRU's single-step input sensitivity
# --------------------------------------------------------------------------

def test_gru_input_lipschitz_matches_the_hand_derivation():
    """One input, one hidden unit, so every spectral norm is just an absolute value.

        gates packed as (r, z, n):  W_ir = [2], W_iz = [6], W_in = [5]
        recurrent candidate block:  W_hn = [8]  ->  M_n = 8

        L = 0.5*|W_iz| + |W_in| + 0.25*M_n*|W_ir|
          = 0.5*6      + 5      + 0.25*8*2        = 3 + 5 + 4 = 12
    """
    dense_i = np.array([[2.0, 6.0, 5.0]])              # (in=1, 3*hidden=3)
    dense_h = np.array([[0.0, 0.0, 8.0]])              # (hidden=1, 3*hidden=3)
    assert sb.gru_input_lipschitz(dense_i, dense_h) == pytest.approx(12.0)


def test_gru_input_lipschitz_rejects_a_kernel_that_is_not_three_gates_wide():
    with pytest.raises(ValueError, match="3\\*hidden columns"):
        sb.gru_input_lipschitz(np.zeros((1, 4)), np.zeros((1, 4)))


# --------------------------------------------------------------------------
# Link 3 — the LayerNorm activation ceiling
# --------------------------------------------------------------------------

def test_layernorm_activation_bounds_use_unit_variance_across_features():
    """A LayerNorm output has exactly zero mean and unit variance over its H
    features, so its Euclidean norm is sqrt(H) and no component exceeds sqrt(H-1).

        H = 4, scale = [2, -1, 1, 1] (max |s| = 2), bias = [1, 0, 0, 0]
        ||a||_2   <= 2*sqrt(4) + ||bias||_2 = 4 + 1 = 5
        ||a||_inf <= 2*sqrt(3) + 1
    """
    l2, linf = sb.layernorm_activation_bounds(
        np.array([2.0, -1.0, 1.0, 1.0]), np.array([1.0, 0.0, 0.0, 0.0]))
    assert l2 == pytest.approx(5.0)
    assert linf == pytest.approx(2.0 * math.sqrt(3.0) + 1.0)


# --------------------------------------------------------------------------
# Link 4 — the assembled actor-site output bound
# --------------------------------------------------------------------------

def _toy_params():
    """A 2-unit network whose every bound is hand-computable (see module docstring)."""
    return {
        "modulator": {
            # modulator hidden width 2, so the three gate blocks are 2 columns each:
            #   W_ir = [[2, 0]]  W_iz = [[6, 0]]  W_in = [[5, 0]]   (sigma 2, 6, 5)
            #   W_hn = [[8, 0], [0, 0]]  ->  M_n = 8
            #   L = 0.5*6 + 5 + 0.25*8*2 = 12
            "gru": {"dense_i": {"kernel": np.array(
                        [[2.0, 0.0, 6.0, 0.0, 5.0, 0.0]])},
                    "dense_h": {"kernel": np.array(
                        [[0.0, 0.0, 0.0, 0.0, 8.0, 0.0],
                         [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]])}},
            "head_actor": {"kernel": K_GAIN, "bias": np.zeros(2)},
            "head_actor_add": {"kernel": K_OFFSET, "bias": np.zeros(2)},
            "z_actor_baseline": np.zeros(2),
            "z_actor_add_baseline": np.zeros(2),
        },
        "actor_fc1": {"kernel": np.eye(2), "bias": np.zeros(2)},
        "actor_fc2": {"kernel": np.diag([2.0, 0.0]), "bias": np.zeros(2)},
        "critic_fc1": {"kernel": np.eye(2), "bias": np.zeros(2)},
        "critic_fc2": {"kernel": np.array([[1.0], [0.0]]), "bias": np.zeros(1)},
    }


def test_actor_site_output_bound_matches_the_hand_assembled_chain():
    """Worked end to end:

        pre-FiLM activation  a = I x + 0, with x the task GRU output in (-1, 1)^2
            ||a||_2   <= 1 * sqrt(2) = 1.41421      ||a||_inf <= 1

        ||delta(gamma*a)||_2 <= min( swing_max * ||a||_2 , dev_l2 * ||a||_inf )
                              = min( 12 * 1.41421 , 14.4722 * 1 ) = 14.4722
        ||delta beta||_2     <= 2*sqrt(2)*1 = 2.82843
        ||delta u||_2        <= 17.30065

        ReLU is 1-Lipschitz; actor_fc2 has sigma_max = 2
        bound on ||delta logits||_2 = 2 * 17.30065 = 34.60130
    """
    out = sb.site_bounds(_toy_params(), "actor", grouping_size=1, hidden_size=2)

    gain_term = 2.0 * math.sqrt(2) * SIGMA_GAIN * 1.0            # 14.47221
    offset_term = 2.0 * math.sqrt(2) * 1.0                       # 2.82843
    assert out["pre_film_act_l2"] == pytest.approx(math.sqrt(2))
    assert out["film_output_deviation"] == pytest.approx(gain_term + offset_term)
    assert out["bound_dlogits"] == pytest.approx(2.0 * (gain_term + offset_term))
    assert math.isnan(out["bound_dvalue"])               # the actor site cannot move V


def test_actor_site_lipschitz_is_the_gru_bound_times_the_head_spectral_norm():
    out = sb.site_bounds(_toy_params(), "actor", grouping_size=1, hidden_size=2)
    assert out["modulator_gru_lipschitz"] == pytest.approx(12.0)
    assert out["lipschitz_gamma"] == pytest.approx(12.0 * SIGMA_GAIN)
    assert out["lipschitz_beta"] == pytest.approx(12.0 * 1.0)


def test_site_bounds_refuses_a_site_the_run_never_enabled():
    with pytest.raises(ValueError, match="was not enabled in this run"):
        sb.site_bounds(_toy_params(), "critic", grouping_size=1, hidden_size=2)


def test_encoder_bound_refuses_to_invent_a_number_without_layernorm():
    p = _toy_params()
    p["modulator"]["head_multimodal"] = {"kernel": K_GAIN, "bias": np.zeros(2)}
    p["modulator"]["head_multimodal_add"] = {"kernel": K_OFFSET, "bias": np.zeros(2)}
    p["modulator"]["z_hidden_baseline"] = np.zeros(2)
    p["modulator"]["z_hidden_add_baseline"] = np.zeros(2)
    with pytest.raises(ValueError, match="use_layer_norm"):
        sb.site_bounds(p, "encoder_multimodal", grouping_size=1, hidden_size=2)


def test_enabled_sites_reads_the_runs_own_saved_config():
    cfg = {"hidden_size": 128, "modulation": {
        "type": "FiLM", "grouping_size": 1, "rnn_mechanism": "activation",
        "sites": {"encoder": True, "rnn": False, "actor": True, "critic": False}}}
    assert sb.enabled_sites(cfg) == ["encoder_unimodal", "encoder_multimodal", "actor"]
    assert sb.enabled_sites({"modulation": {"type": None}}) == []


def test_checkpoint_bounds_refuses_a_non_film_modulation_type():
    cfg = {"hidden_size": 2, "modulation": {
        "type": "Multiplicative", "sites": {"encoder": False, "rnn": False,
                                            "actor": True, "critic": False},
        "rnn_mechanism": "activation"}}
    with pytest.raises(ValueError, match="linear FiLM operator"):
        sb.checkpoint_bounds(_toy_params(), cfg)
