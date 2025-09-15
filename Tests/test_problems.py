import controller
from src.core.definitions import console as console
from src.core.solver import Solver as Solver
from src.problems.problems import get_best_time as get_best_time
# problems, solver
# import math
# NOTE: run .venv/bin/pytest --capture=tee-sys to see code output in real-time, rather than having it all captured.
class TestProblems:
    @staticmethod
    def get_problem_and_compare_output(p_id, expected_cost):
        """
        Assert that the solver produces the same evaluation cost as before, and within a reasonable amount of time.
        """
        p = controller.get_requested_problem(p_id=p_id)
        console.print(f"\nNow testing problem {p.identity}")
        s : Solver = controller.get_or_make_solver(p, no_pickles=True, force_overwrite=False)[0]
        assert (s.expected_cost == expected_cost)
        previous_best_time = get_best_time(p)
        assert (s.seconds_to_solve <= min(previous_best_time + 10, previous_best_time * 1.15))
        console.print(f"Previous best time: {previous_best_time}. Time this run: {s.seconds_to_solve}.")

    def test_zero_query(self):
        """
        Tests that the zero_query problem takes zero queries and rounds to solve.
        """
        TestProblems.get_problem_and_compare_output("b63yrw4", (0,0))

    def test_f43(self):
        TestProblems.get_problem_and_compare_output("f435fe", (2.1581920903954797, 5.977401129943503))

    def test_2_N(self):
        TestProblems.get_problem_and_compare_output("2_N", (2.267857142857143, 6.136904761904762))

    def test_f52(self):
        TestProblems.get_problem_and_compare_output("f52lujg", (1.7391304347826086, 4.913043478260869))

    def test_f5x(self):
        TestProblems.get_problem_and_compare_output("f5xtdf", (1.8717948717948716, 5.282051282051283))

    def test_I48Z(self):
        TestProblems.get_problem_and_compare_output("i48zcx", (2.1666666666666665, 5.895833333333333))