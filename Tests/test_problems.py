from fractions import Fraction
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

class Test_Standard:
    # TODO: Make a test for i4byjk under end round early. (see if can leave end round early code always in play in Solver, and send Solver a variable to its constructor that determines whether it considers ending the round early. Also ensure for at least one or two other problems that their answers are still correct under considering end round early).
    def test_zero_query(self):
        """
        Tests that the zero_query problem takes zero queries and rounds to solve.
        """
        get_problem_and_compare_output("b63yrw4", (Fraction(0), Fraction(0)))

    def test_2(self):
        get_problem_and_compare_output("2", (Fraction(9, 7), Fraction(20, 7)))

    def test_I4BYJK_S_no_ere(self):
        get_problem_and_compare_output(
            "I4BYJK_S",
            (Fraction("29/18"), Fraction("71/18")),
            consider_end_round_early=False
        )

    def test_c630yvb(self):
        get_problem_and_compare_output("c630yvb", (Fraction(1), Fraction(3, 2)))

    def test_i64l26l_s(self):
        get_problem_and_compare_output("i64l26l_s", (Fraction(12, 7), Fraction(129, 28)))

class Test_Extreme:
    def test_f52(self):
        get_problem_and_compare_output("f52lujg", (Fraction(40, 23), Fraction(113, 23)))

    def test_f5x(self):
        get_problem_and_compare_output("f5xtdf", (Fraction(73, 39), Fraction(135, 26)))

    def test_f43(self):
        get_problem_and_compare_output("f435fe", (Fraction(382, 177), Fraction(349, 59)))

    def test_f63gekb(self):
        raise NotImplementedError("Waiting for both")
        get_problem_and_compare_output("f63gekb", ("55/24", "131/20"))


class Test_End_Round_Early:
    def test_I4BYK_S_ere(self):
        get_problem_and_compare_output(
            "I4BYJK_S",
            (Fraction("29/18"), Fraction("67/18")), # 4/18 less queries than without considering ere.
            consider_end_round_early=True
        )

    # tree is isomorphic to i4byjk_s's
    def test_c51riiq_ere(self):
        get_problem_and_compare_output(
            "c51riiq",
            (Fraction("29/18"), Fraction("67/18")), # 4/18 less queries than without considering ere.
            consider_end_round_early=True
        )

    def test_2_ere(self):
        get_problem_and_compare_output(
            "2",
            (Fraction("9/7"), Fraction("20/7")), # Does not benefit from ere.
            consider_end_round_early=True
        )

    def test_f5xtdf_ere(self):
        raise NotImplementedError("Waiting for before iterative deepening")
        get_problem_and_compare_output(
            "f5xtdf",
            ("73/39", "135/26"),
            consider_end_round_early=True
        )


class Test_Nightmare:
    # TODO: make a test for a 6-verifier short nightmare problem, and 1 of the longest nightmare problems the program is capable of solving thus far. Get their values from before iterative deepening, after applying the perfect Fraction commit to it.
    def test_zero_query_nightmare(self):
        get_problem_and_compare_output("b63yrw4_N", (Fraction(0), Fraction(0)))

    def test_1_N(self): # 4 verifier
        get_problem_and_compare_output("1_N", (Fraction(1), Fraction(7, 3)))

    def test_2_N(self):
        raise NotImplementedError("waiting for before iterative deepening")
        # 127/56 and 1031/168 from commit before cache bitsets.
        get_problem_and_compare_output("2_N", (2.267857142857143, 6.136904761904762))

    def test_I48Z(self):
        raise NotImplementedError("waiting for before iterative deepening")
        # 13/6 and 283/48 from commit before cache bitsets.
        get_problem_and_compare_output("i48zcx", (2.1666666666666665, 5.895833333333333))

    def test_A52F7E1_N(self): # 5 verifier
        raise NotImplementedError("waiting for before iterative deepening")
        # 53/30 and 61/15 from commit before cache bitsets.
        get_problem_and_compare_output("A52F7E1_N", (Fraction(1), Fraction(7, 3)))