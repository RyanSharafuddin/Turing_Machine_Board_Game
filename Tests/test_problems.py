import controller
from src.core.definitions import console as console
from src.core.solver import Solver as Solver
from src.problems.problems import get_best_time as get_best_time
import src.problems.problems as problems
from src.core.solver_utils import fp_eq_tup
# problems, solver
# import math
# NOTE: run .venv/bin/pytest --capture=tee-sys to see code output in real-time, rather than having it all captured.
def get_problem_and_compare_output(p_id, expected_cost):
    """
    Assert that the solver produces the same evaluation cost as before (within floating point error), and within a reasonable amount of time.
    """
    p = problems.get_requested_problem(p_id=p_id)
    console.print(f"\nNow testing problem {p.identity}")
    s : Solver = controller.get_or_make_solver(p, no_pickles=True, force_overwrite=False)[0]
    assert fp_eq_tup(s.expected_cost, expected_cost), s.expected_cost
    previous_best_time = get_best_time(p)
    assert (s.seconds_to_solve <= min(previous_best_time + 10, previous_best_time * 1.15))
    console.print(
        f"Previous best time: {previous_best_time:,}. Time this run: {s.seconds_to_solve:,}."
    )

class Test_Standard:
    def test_zero_query(self):
        """
        Tests that the zero_query problem takes zero queries and rounds to solve.
        """
        get_problem_and_compare_output("b63yrw4", (0,0))

class Test_Extreme:
    def test_f5x(self):
        get_problem_and_compare_output("f5xtdf", (1.8717948717948718, 5.1923076923076925))

    def test_f43(self):
        get_problem_and_compare_output("f435fe", (2.15819209039548, 5.915254237288137))

    def test_f52(self):
        get_problem_and_compare_output("f52lujg", (1.7391304347826086, 4.913043478260869))

class Test_Nightmare:
    def test_I48Z(self):
        get_problem_and_compare_output("i48zcx", (2.1666666666666665, 5.895833333333333))

    def test_2_N(self):
        get_problem_and_compare_output("2_N", (2.267857142857143, 6.136904761904762))