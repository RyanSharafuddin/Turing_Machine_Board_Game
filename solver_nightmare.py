from solver import *

def get_set_r_unique_ids_vs_from_cwas_set_representation(
        cwas_set_representation,
        rcs_list: list[list[Rule]]
    ) ->  list[set[int]]:
    """
    Given a full_cwas iterable, returns a list, where list[i] contains a set of the unique_ids for all possible rules for verifier i. WARN: only call this if n_mode is on
    """
    num_vs = len(rcs_list)
    # TODO: consider optimizing the 'sets' belows w/ bitsets or something.
    possible_rule_ids_by_verifier = [set() for _ in range(num_vs)]
    for cwa in cwas_set_representation:
        (c, p) = (cwa[0], cwa[1])
        for (v_index, corresponding_rc) in enumerate(p):
            corresponding_set = possible_rule_ids_by_verifier[v_index]
            possible_card_index = c[corresponding_rc]
            unique_id = rcs_list[corresponding_rc][possible_card_index].unique_id
            corresponding_set.add(unique_id)
    return(possible_rule_ids_by_verifier)

def calculate_minimal_vs_list(rcs_list, num_rcs, game_state: Game_State) -> list[set[int]]: 
    # TODO: print this out to make sure it works
    minimal_vs_list: list[set[int]] = []
    r_unique_ids_by_verifier = get_set_r_unique_ids_vs_from_cwas_set_representation(
        game_state.fset_cwa_indexes_remaining,
        rcs_list
    )
    for v_index in range(num_rcs):
        is_isomorphic_to_previous_verifier = False
        for (v_set_index, v_set) in enumerate(minimal_vs_list):
            for arbitrary_v_set_member in v_set:
                break
            if(r_unique_ids_by_verifier[v_index] == r_unique_ids_by_verifier[arbitrary_v_set_member]):
                is_isomorphic_to_previous_verifier = True
                break
        if(is_isomorphic_to_previous_verifier):
            minimal_vs_list[v_set_index].add(v_index)
        else:
            minimal_vs_list.append(set([v_index]))
    return(minimal_vs_list)

def nightmare_get_and_apply_moves(
        game_state: Game_State,
        qs_dict: dict[int:dict[int:Query_Info]],
        minimal_vs_list: list[set[int]]
    ):
    # TODO: step through with a debugger to understand how the minimal vs_list is working.
    num_combos_currently = len(game_state.fset_cwa_indexes_remaining)
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
    def __init__(self, problem: Problem):
        Solver.__init__(self, problem)

    def calculate_best_move(
        self,
        qs_dict,
        game_state: Game_State,
        minimal_vs_list: list[set[int]] = None,

    ):
        # self.called_calculate += 1
        if(game_state in self.evaluations_cache):
            # self.cache_hits += 1
            return(self.evaluations_cache[game_state])
        if(one_answer_left(game_state.fset_cwa_indexes_remaining)):
            if(config.CACHE_END_STATES):
                self.evaluations_cache[game_state] = Solver.null_answer
            return(Solver.null_answer)
        best_node_cost = Solver.initial_best_cost
        if(game_state.proposal_used_this_round is None):
            minimal_vs_list = calculate_minimal_vs_list(self.rcs_list, self.num_rcs, game_state)

        found_moves = False
        # moves_list = list(nightmare_get_and_apply_moves(game_state, qs_dict, minimal_vs_list))
        # For testing purposes, make the entire moves_list before examining any moves.
        for move_info in nightmare_get_and_apply_moves(game_state, qs_dict, minimal_vs_list):
            (move, mcost, gs_tup, p_tup) = move_info
            gs_false_node_cost = self.calculate_best_move(
                qs_dict, gs_tup[0],
                minimal_vs_list
            )[3]
            gs_true_node_cost = self.calculate_best_move(
                qs_dict,
                gs_tup[1],
                minimal_vs_list
            )[3]
            gss_costs = (gs_false_node_cost, gs_true_node_cost)
            node_cost_tup = self.cost_calulator(mcost, p_tup, gss_costs)
            if(node_cost_tup < best_node_cost):
                found_moves = True
                best_node_cost = node_cost_tup
                best_move = move
                best_mov_cost = mcost
                best_gs_tup = gs_tup
                if(
                    (node_cost_tup == (0, 1)) or
                    ((node_cost_tup == (1, 1)) and (game_state.proposal_used_this_round is None))
                ):
                    # can solve within 1 query and 0 rounds, or 1 query and all queries cost a round, so return early
                    break
        if(found_moves):
            answer = (best_move, best_mov_cost, best_gs_tup, best_node_cost)
        else:
            # don't have to recalculate minimal_vs_list here; the next invocation will do that.
            new_gs = Game_State(
                num_queries_this_round=0,
                proposal_used_this_round=None,
                fset_cwa_indexes_remaining=game_state.fset_cwa_indexes_remaining
            )
            answer = self.calculate_best_move(
                qs_dict=qs_dict,
                game_state=new_gs,
            )
        self.evaluations_cache[game_state] = answer
        return(answer)