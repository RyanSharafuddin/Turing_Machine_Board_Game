# not needed to invoke pytest from command line, but needed for VS Code to work w/pytest.
import os
os.chdir("/Users/Ryan/My Corner/Projects/Python/Turing_Machine_Board_Game/Main_Stuff")

from fractions import Fraction
import pytest
import controller # pyright: ignore[reportUnusedImport] # needed to prevent some sort of circular import error nonsense
from src.core.definitions import *
from src.core.definitions import console as console
from src.core.solver import Solver as Solver
from src.core.solver_nightmare import Solver_Nightmare
from src.core.solver_capitulate import Solver_Capitulate
from src.problems.problems import get_best_time as get_best_time
import src.problems.problems as problems
# problems, solver
# import math
# NOTE: run .venv/bin/pytest --capture=tee-sys to see code output in real-time, rather than having it all captured.

def pid_val_to_param(pid: str, val: tuple[str, str]):
    return pytest.param(pid, val, id=pid)

def pid_val_to_param_list(lst):
    return [pid_val_to_param(*row) for row in lst]

def get_problem_and_compare_output(
        p_id,
        expected_cost,
        consider_end_round_early=False,
        capitulate=False,
        heuristic_func_index=0,
    ):
    """
    Assert that the solver produces the same evaluation cost as before, and within a reasonable amount of time.
    """
    if (type(expected_cost[0]) is str):
        expected_cost = tuple(Fraction(s) for s in expected_cost)
    p = problems.get_requested_problem(p_id=p_id)
    console.print(f"\nNow testing problem {p.identity}")
    if capitulate:
        s = Solver_Capitulate(p, heuristic_func_index=heuristic_func_index)
    else:
        s_cons = Solver_Nightmare if (p.mode == NIGHTMARE) else Solver
        s = s_cons(
            p,
            fail_on_warn=True,
            consider_end_round_early=consider_end_round_early,
            calculate_mem_usage=False,
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

@pytest.mark.parametrize(
    ("p_id", "expected_cost"),
    pid_val_to_param_list(
        [
            ("1", ("1/1", "1/1")),
            ("2", ("9/7", "20/7")),
            ("F6380QQ", ("56/23", "142/23")),
            ("F65D9IV", ("169/68", "395/68")),
            ("C4643N", ("1/1", "5/3")),
            ("A52F7E1", ("1/1", "5/3")),
            ("C5HCBJ", ("1/1", "2/1")),
            ("B63YRW4", ("0/1", "0/1")),
            ("C630YVB", ("1/1", "3/2")),
            ("F435FE", ("577/177", "394/59")),
            ("F5XTDF", ("89/39", "139/26")),
            ("F52LUJG", ("55/23", "107/23")),
            ("E63YF4H", ("18/11", "34/11")),
            ("F63EZQM", ("13/7", "53/14")),
            ("I4BYJK", ("1483/432", "1687/216")),
            ("I48ZCX", ("47/16", "43/8")),
            ("I48ZCX_S", ("3/2", "2/1")),
            ("D48DUU", ("71/33", "54/11")),
            ("I46CVW", ("27/8", "107/16")),
            ("I46CVW_S", ("1/1", "3/1")),
            ("F64IK3Y", ("387/131", "905/131")),
            ("F63GEKB", ("343/120", "273/40")),
            ("C52MT5C", ("2/1", "29/8")),
            ("C52MT5C_N", ("4163/960", "20681/1920")),
            ("C51RIIQ", ("35/18", "71/18")),
            ("C51RIIQ_N", ("761/180", "1423/135")),
            ("I65A0OX", ("9/5", "21/5")),
            ("I65A0OX_S", ("1/1", "1/1")),
            ("FC_USA_250", ("17/10", "4/1")),
            ("FC_USA_250_S", ("1/1", "1/1")),
            ("C5MR03", ("5/2", "26/5")),
            ("C5MR03_N", ("461/100", "10991/960")),
            ("I4CDU0", ("281/72", "587/72")),
            ("I4CDU0_S", ("59/27", "113/27")),
            ("I64L26L", ("85613/20160", "5591/504")),
            ("I64L26L_S", ("13/7", "121/28")),
            ("C4643N_N", ("11/6", "34/9")),
            ("A52F7E1_N", ("59/30", "131/30")),
            ("C5HCBJ_N", ("21/10", "41/10")),
            ("B63YRW4_N", ("0/1", "0/1")),
            ("C630YVB_N", ("179/80", "631/120")),
            ("I4BYJK_S", ("29/18", "71/18")),
            ("1_N", ("1/1", "7/3")),
            ("2_N", ("11/4", "73/14")),
        ]
    )
)
def test_capitulate_ac_heuristic(p_id, expected_cost):
    get_problem_and_compare_output(
        p_id,
        expected_cost,
        consider_end_round_early=False,
        capitulate=True,
        heuristic_func_index=1
    )

@pytest.mark.parametrize(
    ("p_id", "expected_cost"),
    pid_val_to_param_list(
        [
            ("1", ("1/1", "1/1")),
            ("2", ("12/7", "24/7")),
            ("F6380QQ", ("3/1", "819/115")),
            ("F65D9IV", ("191/68", "231/34")),
            ("C4643N", ("1/1", "5/3")),
            ("A52F7E1", ("1/1", "5/3")),
            ("C5HCBJ", ("1/1", "9/4")),
            ("B63YRW4", ("0/1", "0/1")),
            ("C630YVB", ("1/1", "3/2")),
            ("F435FE", ("189/59", "414/59")),
            ("F5XTDF", ("33/13", "77/13")),
            ("F52LUJG", ("55/23", "127/23")),
            ("E63YF4H", ("14/11", "30/11")),
            ("F63EZQM", ("2/1", "26/7")),
            ("I4BYJK", ("1475/432", "214/27")),
            ("I48ZCX", ("19/8", "547/96")),
            ("I48ZCX_S", ("3/2", "9/4")),
            ("D48DUU", ("83/33", "62/11")),
            ("I46CVW", ("271/96", "385/64")),
            ("I46CVW_S", ("1/1", "3/1")),
            ("F64IK3Y", ("430/131", "1092/131")),
            ("F63GEKB", ("129/40", "479/60")),
            ("C52MT5C", ("2/1", "29/8")),
            ("C52MT5C_N", ("91/24", "2321/240")),
            ("C51RIIQ", ("35/18", "71/18")),
            ("C51RIIQ_N", ("2959/720", "3523/360")),
            ("I65A0OX", ("41/20", "613/120")),
            ("I65A0OX_S", ("1/1", "1/1")),
            ("FC_USA_250", ("17/10", "4/1")),
            ("FC_USA_250_S", ("1/1", "1/1")),
            ("C5MR03", ("5/2", "27/5")),
            ("C5MR03_N", ("21757/4800", "3439/300")),
            ("I4CDU0", ("2327/648", "5347/648")),
            ("I4CDU0_S", ("25/9", "41/9")),
            ("I64L26L", ("22279/5040", "241019/20160")),
            ("I64L26L_S", ("5/2", "163/28")),
            ("C4643N_N", ("11/6", "34/9")),
            ("A52F7E1_N", ("32/15", "293/60")),
            ("C5HCBJ_N", ("39/20", "177/40")),
            ("B63YRW4_N", ("0/1", "0/1")),
            ("C630YVB_N", ("15/8", "1201/240")),
            ("I4BYJK_S", ("29/18", "73/18")),
            ("1_N", ("1/1", "5/2")),
            ("2_N", ("75/28", "40/7")),
        ]
    )
)
def test_capitulate_ans_gap_heuristic(p_id, expected_cost):
    get_problem_and_compare_output(
        p_id,
        expected_cost,
        consider_end_round_early=False,
        capitulate=True,
        heuristic_func_index=2
    )

@pytest.mark.parametrize(
    ("p_id", "expected_cost"),
    pid_val_to_param_list(
        [
            ("1", ("1/1", "1/1")),
            ("2", ("12/7", "24/7")),
            ("F6380QQ", ("339/115", "823/115")),
            ("F65D9IV", ("181/68", "429/68")),
            ("C4643N", ("1/1", "5/3")),
            ("A52F7E1", ("1/1", "5/3")),
            ("C5HCBJ", ("1/1", "9/4")),
            ("B63YRW4", ("0/1", "0/1")),
            ("C630YVB", ("1/1", "3/2")),
            ("F435FE", ("190/59", "417/59")),
            ("F5XTDF", ("29/13", "68/13")),
            ("F52LUJG", ("58/23", "126/23")),
            ("E63YF4H", ("14/11", "30/11")),
            ("F63EZQM", ("2/1", "26/7")),
            ("I4BYJK", ("175/54", "3233/432")),
            ("I48ZCX", ("43/16", "119/24")),
            ("I48ZCX_S", ("3/2", "9/4")),
            ("D48DUU", ("83/33", "188/33")),
            ("I46CVW", ("35/12", "101/16")),
            ("I46CVW_S", ("1/1", "3/1")),
            ("F64IK3Y", ("438/131", "1084/131")),
            ("F63GEKB", ("199/60", "481/60")),
            ("C52MT5C", ("2/1", "29/8")),
            ("C52MT5C_N", ("2397/640", "1153/120")),
            ("C51RIIQ", ("35/18", "71/18")),
            ("C51RIIQ_N", ("2239/540", "499/48")),
            ("I65A0OX", ("8/5", "11/3")),
            ("I65A0OX_S", ("1/1", "1/1")),
            ("FC_USA_250", ("17/10", "4/1")),
            ("FC_USA_250_S", ("1/1", "1/1")),
            ("C5MR03", ("23/10", "26/5")),
            ("C5MR03_N", ("10823/2400", "17869/1600")),
            ("I4CDU0", ("575/162", "2665/324")),
            ("I4CDU0_S", ("67/27", "115/27")),
            ("I64L26L", ("5261/1260", "37951/3360")),
            ("I64L26L_S", ("16/7", "73/14")),
            ("C4643N_N", ("11/6", "34/9")),
            ("A52F7E1_N", ("43/20", "79/15")),
            ("C5HCBJ_N", ("21/10", "41/10")),
            ("B63YRW4_N", ("0/1", "0/1")),
            ("C630YVB_N", ("15/8", "1201/240")),
            ("I4BYJK_S", ("29/18", "71/18")),
            ("1_N", ("1/1", "7/3")),
            ("2_N", ("75/28", "40/7")),
        ]
    )
)
def test_capitulate_3_heuristic(p_id, expected_cost):
    get_problem_and_compare_output(
        p_id,
        expected_cost,
        consider_end_round_early=False,
        capitulate=True,
        heuristic_func_index=3
    )
