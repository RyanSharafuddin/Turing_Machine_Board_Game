from .solver import *

def fset_answers_from_cwa_set(all_cwas, cwa_set):
    # cwa_set representation_change TODO!!
    return(frozenset([all_cwas[cwa][-1] for cwa in cwa_set]))

class Solver_Capitulate(Solver):
    def __init__(self, problem: Problem):
        Solver.__init__(self, problem)
        self.num_concurrent_tasks = 0
        self.convert_working_gs_to_cache_gs = solver_utils._do_not_convert_gs

    def _choose_best_move_depth_one(self, move_infos:list):
        # cwa_set representation_change TODO!!
        best_expected_result = Solver.initial_best_cost # number of answers left, number of combos left.
        for(move, mcost, gs_tuple, p_tuple) in move_infos:
            (p_false, p_true) = p_tuple
            (gs_false_answers_left, gs_true_answers_left) = [
                len(fset_answers_from_cwa_set(self.full_cwas_list, gs.cwa_set)) for gs in gs_tuple
            ]
            (gs_false_combos_left, gs_true_combos_left) = [
                len(gs.cwa_set) for gs in gs_tuple
            ]
            expected_answers_left = (p_false * gs_false_answers_left) + (p_true * gs_true_answers_left)
            expected_combos_left = (p_false * gs_false_combos_left) + (p_true * gs_true_combos_left)
            expected_result = (expected_answers_left, expected_combos_left)
            if(expected_result < best_expected_result):
                best_expected_result = expected_result
                best_move = move
                best_mcost = mcost
                best_gs_tup = gs_tuple
        answer = (best_move, best_mcost, best_gs_tup, best_expected_result)
        return answer

    # NOTE: calculate_best_move must be able to be started with
    #       calculate_best_move(self.qs_dict, self.initial_game_state)
    def _calculate_best_move(self, qs_dict, game_state):
        """ A capitulation """
        stack = [game_state]
        while stack:
            current_gs = stack.pop()
            if current_gs in self._evaluations_cache:
                continue
            if not one_answer_left(self.full_cwas_list, current_gs.cwa_set):
                move_infos = list(get_and_apply_moves(current_gs, qs_dict, force_set_intersect=True))
                if not move_infos:
                    new_game_state = Game_State(
                        proposal_used_this_round=None,
                        num_queries_this_round=0,
                        cwa_set=current_gs.cwa_set
                    )
                    move_infos = list(
                        get_and_apply_moves(new_game_state, self.qs_dict, force_set_intersect=True)
                    )
                answer = self._choose_best_move_depth_one(move_infos)
                (best_move, best_mcost, best_gs_tup, best_expected_result) = answer
                self._evaluations_cache[current_gs] = (best_move, best_expected_result)
                stack.append(best_gs_tup[0])
                stack.append(best_gs_tup[1])

    def _calculate_actual_expected_for_capitulation(self, game_state: Game_State, new_ev_cache: dict):
        if game_state in new_ev_cache:
            return new_ev_cache[game_state]
        if not game_state.cwa_set:
            print(game_state)
            exit()
        if one_answer_left(self.full_cwas_list, game_state.cwa_set):
            return((None, (0, 0)))
        if game_state not in self._evaluations_cache:
            print(game_state)
            exit()
        (best_move, answer_combo_cost) = self._evaluations_cache[game_state]
        (gs_false, gs_true) = self.apply_move_to_state(best_move, game_state)
        p_false = len(gs_false.cwa_set) / len(game_state.cwa_set)
        p_true = len(gs_true.cwa_set) / len(game_state.cwa_set)
        (_, cost_false) = self._calculate_actual_expected_for_capitulation(gs_false, new_ev_cache)
        (_, cost_true) = self._calculate_actual_expected_for_capitulation(gs_true, new_ev_cache)
        move_cost = (Solver.does_move_cost_round(best_move, game_state), 1)
        actual_expected_cost = solver_utils.calculate_expected_cost(
            move_cost, (p_false, p_true), (cost_false, cost_true)
        )
        answer = (best_move, actual_expected_cost)
        new_ev_cache[game_state] = answer
        return answer

    def _get_best_move_and_ncost_from_cache(self, working_game_state: Game_State, default=(None, None)):
        """
        Given a working game state, return the best move, and the cost of the game_state, or default if the game state is not in the cache. This function helps get_move_mcost_gs_ncost_from_cache.

        Returns
        -------
        (best_move, node_evaluation)
        """
        return self._evaluations_cache.get(working_game_state, default)

    def _filter_cache(self):
        new_ev_cache = dict()
        self._calculate_actual_expected_for_capitulation(self.initial_game_state, new_ev_cache)
        return new_ev_cache