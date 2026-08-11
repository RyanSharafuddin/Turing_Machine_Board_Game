import numpy as np
from .solver import *

def _calculate_minimal_vs_list(num_rcs, game_state: Game_State, full_cwas_list) -> list[set[int]]:
    minimal_vs_list: list[set[int]] = []
    r_unique_ids_by_verifier = get_set_r_unique_ids_vs_from_cwas_set_representation(
        full_cwas_list,
        game_state.cwa_set,
        num_rcs,
        n_mode=True,
    )
    for v_index in range(num_rcs):
        for v_set in minimal_vs_list:
            for arbitrary_v_set_member in v_set:
                break
            if(r_unique_ids_by_verifier[v_index] == r_unique_ids_by_verifier[arbitrary_v_set_member]):
                v_set.add(v_index)
                break
        else:
            minimal_vs_list.append(set([v_index]))
    return minimal_vs_list

def testing_stuff(self):
    global display
    from . import display
    global sd
    sd = display.Solver_Displayer(self)

class Solver_Nightmare(Solver):
    __slots__ = (
        "num_possible_rules",
        "int_verifier_bit_mask",
        "shift_amounts",
    )
    def __init__(self, problem: Problem):
        Solver.__init__(self, problem)
        self.put_cache_gs_in_new_ev_cache = False
        if not self.full_cwas_list: # invalid problem with no solutions
            return
        self.num_possible_rules = len(self.possible_rules_by_verifier[0])
        self.int_verifier_bit_mask = (1 << self.num_possible_rules) - 1
        self.shift_amounts = [v_index * self.num_possible_rules for v_index in range(self.num_rcs)]
        self.convert_working_gs_to_cache_gs = solver_utils.get_convert_working_to_cache_gs_nightmare(
            self.bitset_type
        )
        # NOTE: below is only for testing purposes.
        testing_stuff(self) # TODO: delete

    # NOTE: keep the below in case want to restore standard solver's non-threshold way.
    def tasks_initialize(self, depth, move_infos: list):
        if(depth < self.num_concurrent_tasks):
            total = len(move_infos)
            task_id = self.depth_to_tasks_l[depth]
            progress.reset(task_id, total=total, visible=True)

    @staticmethod
    def get_and_apply_moves(
            game_state: Game_State,
            qs_dict: dict[int:dict[int:Query_Info]],
            minimal_vs_list: list[set[int]],
            force_set_intersect=False
        ):
        # cwa_set representation_change Will have to implement a function to get length of set
        num_combos_currently = len(game_state.cwa_set)
        if game_state.proposal_used_this_round is None:
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
                                    cost,
                                    force_set_intersect=force_set_intersect
                                )
                                if(move_info is not None):
                                    list_hit_v_sets[v_set_index] = True
                                    num_v_sets_left_to_hit -= 1
                                    yield move_info
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
                                cost,
                                force_set_intersect=force_set_intersect
                            )
                            if(move_info is not None):
                                list_hit_v_sets[v_set_index] = True
                                num_v_sets_left_to_hit -= 1
                                yield(move_info)
                                if(not num_v_sets_left_to_hit):
                                    return
                        break

    def _print_canonical_form_info(self, game_state, cache_game_state, max_num_forms):
        if ('num_forms' not in globals()):
            global num_forms
            num_forms = 0
        else:
            num_forms += 1
        if not(num_forms < max_num_forms):
            return
        console.rule()
        cache_state_without_reordering_func = (
            solver_utils._convert_working_gs_to_cache_gs_standard_int if self.bitset_type is int else
            solver_utils._convert_working_gs_to_cache_gs_standard_nparray
        )
        cache_state_without_reordering = cache_state_without_reordering_func(
            game_state,
            self.all_cwa_bitsets
        )
        permutation = solver_utils.get_permutation(self, game_state)
        rearranged_colors = [config.VERIFIER_COLORS[num] for num in permutation]
        if not np.array_equal(np.array([i for i in range(self.num_rcs)]), permutation):
            form_equal_string = ("Canonical form [red]not[/red] equal!")
        else:
            form_equal_string = ("Canonical form [green]is[/green] equal!")
        console.print(f"Table # {num_forms + 1:,}. {form_equal_string}\n", justify="center")
        sd.print_cache_game_state(
            cache_state_without_reordering,
            "Original",
            config.VERIFIER_COLORS
        )
        print()
        sd.print_cache_game_state(
            cache_game_state,
            "Canonical",
            rearranged_colors,
            include_round_info=False,
        )

    def _calculate_best_move(
        self,
        qs_dict,
        game_state: Game_State,
        minimal_vs_list: list[set[int]] = None,
        depth = 0,
        working_cwa_set_convert_cache = None,
        vertical_prune_threshold = Solver.initial_best_cost
    ):
        is_begin_round = int(game_state.proposal_used_this_round is None)
        if is_begin_round:
            working_cwa_set_convert_cache = dict()

        # self.called_calculate += 1
        cache_game_state = self.convert_working_gs_to_cache_gs(
            self,
            game_state,
            working_cwa_set_convert_cache,
        )
        ######################################## DEBUGGING ###################################################
        # self._print_canonical_form_info(game_state, cache_game_state, max_num_forms=500)
        ######################################## DEBUGGING ###################################################
        result = self._evaluations_cache.get(cache_game_state, None)
        if result is not None:
            # self.cache_hits += 1
            (rq, lower_bound) = result
            pruned = solver_utils.roughly_gt_2tup(rq, vertical_prune_threshold)
            # TODO: see corresponding note in standard solver.
            if (pruned or (not lower_bound)):
                return (rq, pruned)


        if one_answer_left(self.full_cwas_list, game_state.cwa_set):
            pruned = solver_utils.roughly_gt_2tup(Solver.double_zero, vertical_prune_threshold)
            return (Solver.double_zero, pruned)

        (vertical_prune_rounds, vertical_prune_queries) = vertical_prune_threshold
        (vpr_lt_begin_round, vpr_eq_begin_round) = solver_utils.fp_cmp(vertical_prune_rounds, is_begin_round)
        vpq_lt_1 = solver_utils.fp_lt(vertical_prune_queries, 1)
        if vpr_lt_begin_round or (vpr_eq_begin_round and vpq_lt_1):
            return ((is_begin_round, 1), True)

        if is_begin_round:
            minimal_vs_list = _calculate_minimal_vs_list(
                self.num_rcs, game_state, self.full_cwas_list
            )
            qs_dict = solver_utils.full_filter(qs_dict, game_state.cwa_set)

        best_node_cost = Solver.initial_best_cost
        beat_vertical_prune_threshold = False
        move_infos = list(self.get_and_apply_moves(game_state, qs_dict, minimal_vs_list))
        exist_non_begin_round_moves = bool(move_infos)
        # TODO: test whether reordering saves or wastes time.
        self._reorder_move_infos_list(move_infos)
        self.tasks_initialize(depth, move_infos)
        for move_info in move_infos:
            (move, mcost, gs_tup, p_tup) = move_info
            (false_p, true_p) = p_tup
            vertical_prune_threshold_nodes = (
                vertical_prune_threshold[0] - is_begin_round,
                vertical_prune_threshold[1] - 1
            )
            vertical_prune_threshold_false = solver_utils.divide_cost_by_probability(
                vertical_prune_threshold_nodes,
                false_p
            )
            (false_rq, false_pruned) = self._calculate_best_move(
                qs_dict=qs_dict,
                game_state=gs_tup[0],
                minimal_vs_list=minimal_vs_list,
                depth=depth + 1,
                working_cwa_set_convert_cache=working_cwa_set_convert_cache,
                vertical_prune_threshold=vertical_prune_threshold_false
            )
            if false_pruned:
                if not beat_vertical_prune_threshold:
                    cost_just_false = self._cost_calculator(mcost, p_tup, (false_rq, Solver.double_zero))
                    if solver_utils.roughly_gt_2tup(best_node_cost, cost_just_false):
                        best_node_cost = cost_just_false
                if depth < self.num_concurrent_tasks:
                    progress.update(self.depth_to_tasks_l[depth], advance=1)
                continue

            vertical_prune_threshold_true_before_divide = (
                vertical_prune_threshold_nodes[0] - (false_p * false_rq[0]),
                vertical_prune_threshold_nodes[1] - (false_p * false_rq[1])
            )
            vertical_prune_threshold_true = solver_utils.divide_cost_by_probability(
                vertical_prune_threshold_true_before_divide,
                true_p
            )
            (true_rq, true_pruned) = self._calculate_best_move(
                qs_dict=qs_dict,
                game_state=gs_tup[1],
                minimal_vs_list=minimal_vs_list,
                depth=depth + 1,
                working_cwa_set_convert_cache=working_cwa_set_convert_cache,
                vertical_prune_threshold=vertical_prune_threshold_true
            )
            gss_costs = (false_rq, true_rq)
            if true_pruned:
                if not beat_vertical_prune_threshold:
                    node_cost_tup = self._cost_calculator(mcost, p_tup, gss_costs)
                    if solver_utils.roughly_gt_2tup(best_node_cost, node_cost_tup):
                        best_node_cost = node_cost_tup
                if depth < self.num_concurrent_tasks:
                    progress.update(self.depth_to_tasks_l[depth], advance=1)
                continue
            node_cost_tup = self._cost_calculator(mcost, p_tup, gss_costs)
            best_node_cost = node_cost_tup
            best_move = move
            beat_vertical_prune_threshold = True
            vertical_prune_threshold = best_node_cost
            if(node_cost_tup == mcost):
                # WARN: be sure not to mix begin-round-early moves w/regular moves for this prune.
                break
            if depth < self.num_concurrent_tasks:
                progress.update(self.depth_to_tasks_l[depth], advance=1)


        pruned = not beat_vertical_prune_threshold
        if beat_vertical_prune_threshold:
            self.best_move = best_move
        if not exist_non_begin_round_moves:
            new_gs = Game_State(
                num_queries_this_round=0,
                proposal_used_this_round=None,
                cwa_set=game_state.cwa_set
            )
            # don't have to recalculate minimal_vs_list here; the next invocation will do that.
            (best_node_cost, pruned) = self._calculate_best_move(
                qs_dict=qs_dict,
                game_state=new_gs,
                depth=depth+1,
                vertical_prune_threshold=vertical_prune_threshold
            )

        answer = (best_node_cost, pruned)
        self._evaluations_cache[cache_game_state] = answer
        return answer

    def _easy_working_gs_to_cache_gs(self, working_game_state: Game_State):
        """
        A convenience function for converting a `working_game_state` to a cache_game_state (no permutation info needed). This is used by filter_cache.
        """
        cache_gs = self.convert_working_gs_to_cache_gs(self, working_game_state, dict())
        return cache_gs

    def _filter_calculate_best_move(self, curr_working_gs):
        minimal_vs_list = _calculate_minimal_vs_list(
            self.num_rcs, curr_working_gs, self.full_cwas_list
        )
        return self._calculate_best_move(
            qs_dict=self.qs_dict,
            game_state=curr_working_gs,
            minimal_vs_list=minimal_vs_list,
            depth=0,
            working_cwa_set_convert_cache=dict()
        )

    def exist_moves(self, curr_working_gs):
        """
        Return True if there are any potentially useful moves to be made in this state with the current proposal_used_this_round. If said proposal is none, return True if there are useful moves to be made this round using any proposal.
        """
        minimal_vs_list = _calculate_minimal_vs_list(
            self.num_rcs, curr_working_gs, self.full_cwas_list
        )
        for mi in self.get_and_apply_moves(
            curr_working_gs,
            self.qs_dict,
            minimal_vs_list,
            force_set_intersect=True
        ):
            return True
        return False