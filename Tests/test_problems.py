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

def pid_val_to_param(pid: str, val: tuple[str, str]):
    return pytest.param(pid, val, id=pid)

def pid_val_to_param_list(lst):
    return [pid_val_to_param(*row) for row in lst]

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
    pid_val_to_param_list(
        [
            ("1", ("1", "1")),
            ("C4643N", ("1", "5/3")),
            ("I46CVW_S", ("1", "3")),
            ("2", ("9/7", "20/7")),
            ("I48ZCX_S", ("3/2", "2")),
            ("I4BYJK_S", ("29/18", "71/18")),
            ("I4CDU0_S", ("50/27", "110/27")),
            ("FC_USA_250_S", ("1", "1")),
            ("A52F7E1", ("1", "5/3")),
            ("C5HCBJ", ("1", "2")),
            ("C52MT5C", ("3/2", "15/4")),
            ("C51RIIQ", ("29/18", "71/18")),
            ("C5MR03", ("39/20", "101/20")),
            ("B63YRW4", ("0", "0")),
            ("I65A0OX_S", ("1", "1")),
            ("C630YVB", ("1", "3/2")),
            ("I64L26L_S", ("12/7", "129/28")),
        ]
    )
)
def test_standard_no_ere(p_id, expected_cost):
    get_problem_and_compare_output(p_id, expected_cost, consider_end_round_early=False)

@pytest.mark.parametrize(
    ("p_id", "expected_cost"),
    pid_val_to_param_list(
        [
            ("D48DUU", ("58/33", "167/33")),
            ("F435FE", ("382/177", "349/59")),
            ("F52LUJG", ("40/23", "113/23")),
            # f5x answer better than before iterative deepening
            ("F5XTDF", ("73/39", "135/26")),
            ("E63YF4H", ("1", "29/11")),
            ("F63EZQM", ("17/14", "45/14")),
            ("F65D9IV", ("33/17", "93/17")),
            ("F6380QQ", ("242/115", "688/115")),
            ("F64IK3Y", ("299/131", "846/131")),
            ("F63GEKB", ("55/24", "131/20")),
        ]
    )
)
def test_extreme_no_ere(p_id, expected_cost):
    get_problem_and_compare_output(p_id, expected_cost, consider_end_round_early=False)


@pytest.mark.parametrize(
    ("p_id", "expected_cost"),
    pid_val_to_param_list(
        [
            ("1", ("1", "1")),
            ("C4643N", ("1", "5/3")),
            ("I46CVW_S", ("1", "3")),
            ("2", ("9/7", "20/7")),
            ("I48ZCX_S", ("3/2", "2")),
            ("I4BYJK_S", ("29/18", "67/18")), # benefits from ERE
            ("I4CDU0_S", ("50/27", "110/27")),
            ("FC_USA_250_S", ("1", "1")),
            ("A52F7E1", ("1", "5/3")),
            ("C5HCBJ", ("1", "2")),
            ("C52MT5C", ("3/2", "15/4")),
            ("C51RIIQ", ("29/18", "67/18")), # benefits from ERE
            ("C5MR03", ("39/20", "101/20")),
            ("B63YRW4", ("0", "0")),
            ("I65A0OX_S", ("1", "1")),
            ("C630YVB", ("1", "3/2")),
            ("I64L26L_S", ("12/7", "129/28")),

            # Extremes. None benefit from ERE.
            ("D48DUU", ("58/33", "167/33")),
            ("F435FE", ("382/177", "349/59")),
            ("F52LUJG", ("40/23", "113/23")),
            ("F5XTDF", ("73/39", "135/26")),
            ("E63YF4H", ("1", "29/11")),
            ("F63EZQM", ("17/14", "45/14")),
            ("F65D9IV", ("33/17", "93/17")),
            ("F6380QQ", ("242/115", "688/115")),
            ("F64IK3Y", ("299/131", "846/131")),
            ("F63GEKB", ("55/24", "131/20")),
        ]
    )
)
def test_ere_non_nightmare(p_id, expected_cost):
    get_problem_and_compare_output(p_id, expected_cost, consider_end_round_early=True)

def test_ere_nightmare(p_id, expected_cost):
    raise NotImplementedError("Considering end round early on nightmare answers unknown, as of yet.")

@pytest.mark.parametrize(
    ("p_id", "expected_cost"),
    pid_val_to_param_list(
        [
            ("1_N", ("1", "7/3")),
            ("C4643N_N", ("11/6", "34/9")),
            ("I48ZCX", ("13/6", "283/48")),
            ("2_N", ("127/56", "1031/168")),
            ("I46CVW", ("19/8", "101/16")),
            ("I4BYJK", ("11/4", "1585/216")),
            ("I4CDU0", ("203/72", "553/72")),
            ("FC_USA_250", ("17/10", "4")),
            ("A52F7E1_N", ("53/30", "61/15")),
            ("C5HCBJ_N", ("19/10", "99/20")),
            ("C52MT5C_N", ("233/80", "7547/960")),
            ("B63YRW4_N", ("0", "0")),
            ("I65A0OX", ("8/5", "11/3")),
            ("C630YVB_N", ("15/8", "1201/240")),
        ]
    )
)
def test_nightmare_no_ere(p_id, expected_cost):
    get_problem_and_compare_output(p_id, expected_cost, consider_end_round_early=False)
