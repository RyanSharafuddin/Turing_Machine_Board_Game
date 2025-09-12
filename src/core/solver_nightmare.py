from .solver import *

def _calculate_minimal_vs_list(num_rcs, game_state: Game_State, full_cwas_list) -> list[set[int]]:
    # TODO: print this out to make sure it works
    minimal_vs_list: list[set[int]] = []
    r_unique_ids_by_verifier = get_set_r_unique_ids_vs_from_cwas_set_representation(
        full_cwas_list,
        game_state.cwa_set,
        num_rcs,
        n_mode=True,
    )
    for v_index in range(num_rcs):
        for (v_set_index, v_set) in enumerate(minimal_vs_list):
            for arbitrary_v_set_member in v_set:
                break
            if(r_unique_ids_by_verifier[v_index] == r_unique_ids_by_verifier[arbitrary_v_set_member]):
                v_set.add(v_index)
                break
        else:
            minimal_vs_list.append(set([v_index]))
    return(minimal_vs_list)

def _nightmare_get_and_apply_moves(
        game_state: Game_State,
        qs_dict: dict[int:dict[int:Query_Info]],
        minimal_vs_list: list[set[int]]
    ):
    # TODO: step through with a debugger to understand how the minimal vs_list is working.
    # cwa_set representation_change Will have to implement a function to get length of set
    num_combos_currently = len(game_state.cwa_set)
    if(game_state.proposal_used_this_round is None):
        cost = (1, 1)
        next_num_queries = 1
        for (proposal, inner_dict) in qs_dict.items():
            num_v_sets_left_to_hit = len(minimal_vs_list)
            list_hit_v_sets = [False] * num_v_sets_left_to_hit
            for (verifier_to_query, q_info) in inner_dict.items():
                move = (proposal, verifier_to_query)
                for (v_set_index, v_set) in enumerate(minimal_vs_list):
                    if(verifier_to_query in v_set):
                        if(not(list_hit_v_sets[v_set_index])):
                            # try it out
                            move_info = create_move_info(
                                num_combos_currently,
                                game_state,
                                next_num_queries,
                                q_info,
                                move,
                                cost
                            )
                            if(move_info is not None):
                                list_hit_v_sets[v_set_index] = True
                                num_v_sets_left_to_hit -= 1
                                yield(move_info)
                        break
                if(not num_v_sets_left_to_hit):
                    break
    else:
        cost = (0, 1)
        next_num_queries = (game_state.num_queries_this_round + 1) % 3
        inner_dict_this_proposal = qs_dict.get(game_state.proposal_used_this_round, None)
        if(inner_dict_this_proposal is None):
            return
        num_v_sets_left_to_hit = len(minimal_vs_list)
        list_hit_v_sets = [False] * num_v_sets_left_to_hit
        for (verifier_to_query, q_info) in inner_dict_this_proposal.items():
            move = (game_state.proposal_used_this_round, verifier_to_query)
            for (v_set_index, v_set) in enumerate(minimal_vs_list):
                if(verifier_to_query in v_set):
                    if(not(list_hit_v_sets[v_set_index])):
                        # try it out
                        move_info = create_move_info(
                            num_combos_currently,
                            game_state,
                            next_num_queries,
                            q_info,
                            move,
                            cost
                        )
                        if(move_info is not None):
                            list_hit_v_sets[v_set_index] = True
                            num_v_sets_left_to_hit -= 1
                            yield(move_info)
                            if(not num_v_sets_left_to_hit):
                                return
                    break

class Solver_Nightmare(Solver):
    __slots__ = (
        "num_possible_rules",
        "int_verifier_bit_mask",
        "shift_amounts",
    )
    def __init__(self, problem: Problem):
        Solver.__init__(self, problem)
        self.num_possible_rules = len(self.possible_rules_by_verifier[0])
        self.int_verifier_bit_mask = (1 << self.num_possible_rules) - 1
        self.shift_amounts = [v_index * self.num_possible_rules for v_index in range(self.num_rcs)]
        self.convert_working_gs_to_cache_gs = solver_utils.get_convert_working_to_cache_gs_nightmare(
            self.bitset_type
        )

    def _calculate_best_move(
        self,
        qs_dict,
        game_state: Game_State,
        minimal_vs_list: list[set[int]] = None,
    ):
        # self.called_calculate += 1
        (cache_game_state, permutation) = self.convert_working_gs_to_cache_gs(
            game_state,
            self.all_cwa_bitsets,
            self.shift_amounts,
            self.int_verifier_bit_mask
        )
        if(cache_game_state in self._evaluations_cache):
            # self.cache_hits += 1
            return(self._evaluations_cache[cache_game_state])
        if(one_answer_left(self.full_cwas_list, game_state.cwa_set)):
            if(config.CACHE_END_STATES):
                self._evaluations_cache[cache_game_state] = Solver.null_answer
            return(Solver.null_answer)
        best_node_cost = Solver.initial_best_cost
        if(game_state.proposal_used_this_round is None):
            minimal_vs_list = _calculate_minimal_vs_list(
                self.num_rcs, game_state, self.full_cwas_list
            )
            # WARN: line below is new and not fully tested/stepped through/debugged in nightmare mode.
            qs_dict = solver_utils.full_filter(qs_dict, game_state.cwa_set) # FILTER

        found_moves = False
        # moves_list = list(nightmare_get_and_apply_moves(game_state, qs_dict, minimal_vs_list))
        # For testing purposes, make the entire moves_list before examining any moves.
        for move_info in _nightmare_get_and_apply_moves(game_state, qs_dict, minimal_vs_list):
            (move, mcost, gs_tup, p_tup) = move_info
            gs_false_node_cost = self._calculate_best_move(
                qs_dict,
                gs_tup[0],
                minimal_vs_list
            )[1]
            gs_true_node_cost = self._calculate_best_move(
                qs_dict,
                gs_tup[1],
                minimal_vs_list
            )[1]
            gss_costs = (gs_false_node_cost, gs_true_node_cost)
            node_cost_tup = self._cost_calculator(mcost, p_tup, gss_costs)
            if(node_cost_tup < best_node_cost):
                found_moves = True
                best_node_cost = node_cost_tup
                best_move = move
                if(
                    (node_cost_tup == (0, 1)) or
                    ((node_cost_tup == (1, 1)) and (game_state.proposal_used_this_round is None))
                ):
                    # can solve within 1 query and 0 rounds, or 1 query and 1 round and all queries cost a round, so return early
                    break
        if(found_moves):
            (best_proposal, best_v_index) = best_move
            best_move = (best_proposal, permutation[best_v_index])
            answer = (best_move, best_node_cost)
        else:
            # don't have to recalculate minimal_vs_list here; the next invocation will do that.
            new_gs = Game_State(
                num_queries_this_round=0,
                proposal_used_this_round=None,
                cwa_set=game_state.cwa_set
            )
            answer = self._calculate_best_move(qs_dict=qs_dict, game_state=new_gs)
        self._evaluations_cache[cache_game_state] = answer
        return(answer)

    def get_move_mcost_gs_ncost_from_cache(self, game_state: Game_State, default=None):
        """
        Given a game state, return the best move, the cost of the best move, the resulting (gs_false, gs_true) tuple, and the cost of the game_state, or default if the game state is not in the cache. This function makes it so that solvers can easily change what they put in the evaluations cache for their own purposes, without necessitating changes to controller.py or display.py.

        Returns
        -------
        (best_move, best_move_cost, gs_tuple, node_evaluation)
        """
        #TODO cache_gs: take into account how to find a state in the cache and how to use the best move.
        (cache_game_state, permutation) = self.convert_working_gs_to_cache_gs(
            game_state,
            self.all_cwa_bitsets,
            self.shift_amounts,
            self.int_verifier_bit_mask
            )
        if not(cache_game_state in self._evaluations_cache):
            return(default)
        (best_move, node_evaluation) = (
            self._evaluations_cache[cache_game_state][0], self._evaluations_cache[cache_game_state][-1]
        )
        (best_proposal, best_v_index) = best_move
        best_move = (best_proposal, np.argwhere(permutation == best_v_index)[0, 0])
        best_mcost = ((Solver.does_move_cost_round(best_move, game_state)), 1)
        gs_tuple = self.apply_move_to_state(best_move, game_state)
        constructed_answer = (best_move, best_mcost, gs_tuple, node_evaluation)
        return(constructed_answer)

    def filter_cache(self):
        """
        Replace the current self._evaluations_cache with one that *only* contains the information needed to play the problem perfectly. Useful because pickling is very slow.
        NOTE: This function is almost exactly the same as the corresponding function in solver.py; the only difference is in the invocation of self.convert_working_gs_to_cache_gs and the arguments given to it. Perhaps can refactor this so that this function does not need to be written twice.
        """
        if(self._evaluations_cache is None):
            return
        new_evaluations_cache = dict()
        stack : list[Game_State] = [self.initial_game_state]
        added_game_states_set = set()
        while(stack):
            curr_working_gs = stack.pop()
            (curr_cache_gs, permutation) = self.convert_working_gs_to_cache_gs(
                curr_working_gs,
                self.all_cwa_bitsets,
                self.shift_amounts,
                self.int_verifier_bit_mask
            ) #TODO cache_gs
            if(
                (curr_cache_gs not in added_game_states_set) and
                (not one_answer_left(self.full_cwas_list, curr_working_gs.cwa_set))
            ):
                gs_evaluation_result = self.get_move_mcost_gs_ncost_from_cache(curr_working_gs)
                if(gs_evaluation_result is None):
                    console.print("Huh. Why is the evaluation result of the following game state None?")
                    console.print("Working game state: ", curr_working_gs)
                    console.print("Cache game state: ", curr_cache_gs)
                    console.print("Exiting.")
                    exit()
                (working_gs_false, working_gs_true) = gs_evaluation_result[2]
                curr_cache_gs_result = self._evaluations_cache[curr_cache_gs]
                new_evaluations_cache[curr_cache_gs] = curr_cache_gs_result
                stack.append(working_gs_false)
                stack.append(working_gs_true)
                added_game_states_set.add(curr_cache_gs)
        self._evaluations_cache = new_evaluations_cache