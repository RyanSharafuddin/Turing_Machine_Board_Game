import controller, problems, solver
import math

class TestProblems:
    def test_zero_query(self):
        """
        Tests that the zero_query problem takes zero queries and 0 seconds (rounded down to nearest int) to solve.
        """
        zero_query = problems.get_problem_by_id("B63YRW4")
        s = controller.get_or_make_solver(zero_query, no_pickles=True)[0]
        assert (len(solver.fset_answers_from_cwa_set(s.initial_game_state.fset_cwa_indexes_remaining)) == 1)
        assert(s.seconds_to_solve == 0)