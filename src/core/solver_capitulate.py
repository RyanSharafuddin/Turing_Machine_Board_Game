from .solver import *

def fset_answers_from_cwa_set(cwa_set):
    # cwa_set representation_change TODO!!
    return(frozenset([cwa[-1] for cwa in cwa_set]))

def _choose_best_move_depth_one(moves_list):
    # cwa_set representation_change TODO!!
    best_expected_result = Solver.initial_best_cost # number of answers left, number of combos left.
    for(move, mcost, gs_tuple, p_tuple) in moves_list:
        (p_false, p_true) = p_tuple
        (gs_false_answers_left, gs_true_answers_left) = [
            len(fset_answers_from_cwa_set(gs.fset_cwa_indexes_remaining)) for gs in gs_tuple
        ]
        (gs_false_combos_left, gs_true_combos_left) = [
            len(gs.fset_cwa_indexes_remaining) for gs in gs_tuple
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
    return(answer)

def _calculate_actual_expected_for_capitulation(evaluations_cache, game_state: Game_State):
    # cwa_set representation_change TODO!!
    if(not game_state in evaluations_cache):
        return((0, 0))
    (best_move, best_mcost, best_gs_tup, answer_combo_cost) = evaluations_cache[game_state]
    (gs_false, gs_true) = best_gs_tup
    p_false = len(gs_false.fset_cwa_indexes_remaining) / len(game_state.fset_cwa_indexes_remaining)
    p_true = len(gs_true.fset_cwa_indexes_remaining) / len(game_state.fset_cwa_indexes_remaining)
    cost_false = _calculate_actual_expected_for_capitulation(evaluations_cache, gs_false)
    cost_true = _calculate_actual_expected_for_capitulation(evaluations_cache, gs_true)
    actual_expected_cost = solver_utils.calculate_expected_cost(best_mcost, (p_false, p_true), (cost_false, cost_true))
    evaluations_cache[game_state] = (best_move, best_mcost, best_gs_tup, actual_expected_cost)
    return(actual_expected_cost)

class Solver_Capitulate(Solver):
    def __init__(self, problem: Problem):
        Solver.__init__(self, problem)

    # NOTE: calculate_best_move must be able to be started with
    #       calculate_best_move(self.qs_dict, self.initial_game_state)
    def _calculate_best_move(self, qs_dict, game_state):
        """ A capitulation """
        stack = [self.initial_game_state]
        while(stack):
            current_gs = stack.pop()
            if not(one_answer_left(self.full_cwas_list, current_gs.fset_cwa_indexes_remaining)):
                moves_list = list(get_and_apply_moves(current_gs, self.qs_dict))
                if not(moves_list):
                    new_game_state = Game_State(
                        proposal_used_this_round=None,
                        num_queries_this_round=0,
                        fset_cwa_indexes_remaining=current_gs.fset_cwa_indexes_remaining
                    )
                    moves_list = list(get_and_apply_moves(new_game_state, self.qs_dict))
                answer = _choose_best_move_depth_one(moves_list)
                self._evaluations_cache[current_gs] = answer
                (best_move, best_mcost, best_gs_tup, best_expected_result) = answer
                stack.append(best_gs_tup[0])
                stack.append(best_gs_tup[1])
        _calculate_actual_expected_for_capitulation(self._evaluations_cache, self.initial_game_state)
