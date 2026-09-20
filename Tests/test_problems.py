from fractions import Fraction
import pytest
import controller # pyright: ignore[reportUnusedImport] # needed to prevent some sort of circular import error nonsense
from src.core.definitions import *
from src.core.definitions import console as console
from src.core.solver import Solver as Solver
from src.core.solver_nightmare import Solver_Nightmare
from src.problems.problems import get_best_time as get_best_time
import src.problems.problems as problems
# problems, solver
# import math
# NOTE: run .venv/bin/pytest --capture=tee-sys to see code output in real-time, rather than having it all captured.

def get_problem_and_compare_output(p_id, expected_cost, consider_end_round_early=False):
    """
    Assert that the solver produces the same evaluation cost as before, and within a reasonable amount of time.
    """
    if (type(expected_cost[0]) is str):
        expected_cost = tuple(Fraction(s) for s in expected_cost)
    p = problems.get_requested_problem(p_id=p_id)
    console.print(f"\nNow testing problem {p.identity}")
    if (p.mode == NIGHTMARE):
        s: Solver_Nightmare = Solver_Nightmare(
            p,
            fail_on_warn=True,
            consider_end_round_early=consider_end_round_early,
        )
    else:
        s : Solver = Solver(
            p,
            fail_on_warn=True,
            consider_end_round_early=consider_end_round_early,
        )
    s.solve()
    assert (s.expected_cost == expected_cost), s.expected_cost # Fractions have perfect accuracy
    # previous_best_time = get_best_time(p)
    # assert (s.seconds_to_solve <= max(previous_best_time + 20, previous_best_time * 1.15))
    # console.print(
    #     f"Previous best time: {previous_best_time:,}. Time this run: {s.seconds_to_solve:,}."
    # )

@pytest.mark.parametrize(
    ("p_id", "expected_cost"),
    [
        pytest.param("b63yrw4", ("0", "0"), id="b63yrw4"),
        pytest.param("2", ("9/7", "20/7"), id="2"),
        pytest.param("I4BYJK_S", ("29/18", "71/18"), id="I4BYJK_S"),
        pytest.param("c630yvb", ("1", "3/2"), id="c630yvb"),
        pytest.param("i64l26l_s", ("12/7", "129/28"), id="i64l26l_s"),
    ]
)
def test_standard_no_ere(p_id, expected_cost):
    get_problem_and_compare_output(p_id, expected_cost, consider_end_round_early=False)

@pytest.mark.parametrize(
    ("p_id", "expected_cost"),
    [
        pytest.param("f52lujg", ("40/23", "113/23"), id="f52lujg"),
        # answer better than before cache bitset or before it. deepening
        pytest.param("f5xtdf", ("73/39", "135/26"), id="f5xtdf"),
        pytest.param("f435fe", ("382/177", "349/59"), id="f435fe"),
        pytest.param("f63gekb", ("55/24", "131/20"), id="f63gekb"),
    ]
)
def test_extreme_no_ere(p_id, expected_cost):
    get_problem_and_compare_output(p_id, expected_cost, consider_end_round_early=False)


@pytest.mark.parametrize(
    ("p_id", "expected_cost"),
    [
        pytest.param("I4BYJK_S", ("29/18", "67/18"), id="I4BYJK_S"), # 4/18 less.
        # tree of c51 is isomorphic to i4by_S
        pytest.param("c51riiq", ("29/18", "67/18"), id="c51riiq"), # 4/18 less.
        pytest.param("2", ("9/7", "20/7"), id="2"), # same as no ere
        pytest.param("f5xtdf", ("73/39", "135/26"), id="f5xtdf"), # same as no ere
    ]
)
def test_ere_non_nightmare(p_id, expected_cost):
    get_problem_and_compare_output(p_id, expected_cost, consider_end_round_early=True)


@pytest.mark.parametrize(
    ("p_id", "expected_cost"),
    [
        pytest.param("b63yrw4_N", ("0", "0"), id="b63yrw4_N"),
        pytest.param("1_N", ("1", "7/3"), id="1_N"),
        pytest.param("2_N", ("127/56", "1031/168"), id="2_N"),
        pytest.param("i48zcx", ("13/6", "283/48"), id="i48zcx"),
        pytest.param("A52F7E1_N", ("53/30", "61/15"), id="A52F7E1_N"),
    ]
)
def test_nightmare_no_ere(p_id, expected_cost):
    get_problem_and_compare_output(p_id, expected_cost, consider_end_round_early=False)
