import numpy as np
from .solver import *

class Solver_Nightmare(Solver):
    worst_eval = (inf, inf)
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

    # TODO: delete entirely and put functionality in same place as converting to cache game state before canonical.
    def _calculate_minimal_vs_list(self, game_state: Game_State) -> list[set[int]]:
        minimal_vs_list: list[set[int]] = []
        r_unique_ids_by_verifier = get_set_r_unique_ids_vs_from_cwas_set_representation(
            self.full_cwas_list,
            game_state.cwa_set,
            self.num_rcs,
            n_mode=True,
        )
        for v_index in range(self.num_rcs):
            for v_set in minimal_vs_list:
                for arbitrary_v_set_member in v_set:
                    break
                if(r_unique_ids_by_verifier[v_index] == r_unique_ids_by_verifier[arbitrary_v_set_member]):
                    v_set.add(v_index)
                    break
            else:
                minimal_vs_list.append(set([v_index]))
        return minimal_vs_list

    def _validate_move_info_list(self, move_info_list, gs):
        """
        Validates that all move_infos in the `move_info_list` are not None and are correct (i.e., the gs_tup that results from applying the move in a move_info on `gs` agrees with the gs_tup in the move_info). Only for use in _test_equivalence.
        """
        for mi in move_info_list:
            assert (mi is not None)
            (move, cost, gs_tup, p_tup) = mi
            assert (gs_tup == self.apply_move_to_state(move, gs))

    def _min_v_sets_by_proposal(self, move_list, min_vs_l: list[set[int]]) -> dict:
        """
        Given a list of minimal vs sets (`min_vs_l`) and a list of moves, return a dictionary where the keys are the proposals of each move, and d[proposal] = an integer representing which v_set indexes were covered by the moves in move_list. Only for use in _test_equivalence.
        """
        d = dict()
        for (proposal, verifier) in move_list:
            v_sets_covered_int = d.get(proposal, 0)
            for (v_set_index, v_set) in enumerate(min_vs_l):
                if (verifier not in v_set):
                    continue
                # verifier is in v_set
                v_sets_covered_int |= (1 << v_set_index)
                break
            else: # the inner for loop was not broken out of.
                raise ValueError(f"The min vs list doesn't contain a set which contains verifier {verifier}!")
            d[proposal] = v_sets_covered_int
        return d

    def _test_equivalence(self, move_func_1, move_func_2, gs, qs_dict, min_vs_l):
        """
        Not for use in 'production'. A function to test whether 2 different move_generator functions both cover the min_vs_list on the game state gs in the same way.
        """
        move_info_lists = [list(move_func(gs, qs_dict, min_vs_l)) for move_func in (move_func_1, move_func_2)]
        for mi_list in move_info_lists:
            self._validate_move_info_list(mi_list, gs)
        move_lists = [[move_info[0] for move_info in move_info_list] for move_info_list in move_info_lists]
        if (set(move_lists[0]) != set(move_lists[1])):
            print(
                "Heyy, the move_funcs returned a different set of moves! This is fine, but breakpoint here and inspect with debugging to learn more."
            )
            exit()
        resultant_ds = [self._min_v_sets_by_proposal(ml, min_vs_l) for ml in move_lists]
        assert (resultant_ds[0] == resultant_ds[1])

    @staticmethod
    def get_and_apply_moves(
        game_state: Game_State,
        qs_dict: dict[int:dict[int:Query_Info]],
        minimal_vs_list: list[set[int]],
        force_set_intersect=False
    ):
        # NEW
        # cwa_set representation_change Will have to implement a function to get length of set
        num_combos_currently = len(game_state.cwa_set)
        if game_state.proposal_used_this_round is None:
            cost = (1, 1)
            next_num_queries = 1
            for (proposal, inner_dict) in qs_dict.items():
                for v_set in minimal_vs_list:
                    # hit the v_set or exhaust it. MUST hit or exhaust.
                    for verifier_index in v_set:
                        corresponding_q_info = inner_dict.get(verifier_index)
                        if corresponding_q_info is not None:
                            # verifier_index is in inner dict
                            move = (proposal, verifier_index)
                            move_info = create_move_info(
                                num_combos_currently,
                                game_state,
                                next_num_queries,
                                corresponding_q_info,
                                move,
                                cost,
                                force_set_intersect=force_set_intersect
                            )
                            # TODO: get rid of the force_set_intersect argument and remove the not None check.
                            # see the Small Improvements section of your todo document for more info.
                            if move_info is not None:
                                yield move_info
                            break # break outside if is okay b/c min_vs_list updated every begin-round state.
            return
        cost = (0, 1)
        next_num_queries = (game_state.num_queries_this_round + 1) % 3
        inner_dict_this_proposal = qs_dict.get(game_state.proposal_used_this_round)
        if inner_dict_this_proposal is None:
            return
        for v_set in minimal_vs_list:
            # hit or exhaust v_set
            for verifier_index in v_set:
                corresponding_q_info = inner_dict_this_proposal.get(verifier_index)
                if corresponding_q_info is not None:
                    move = (game_state.proposal_used_this_round, verifier_index)
                    move_info = create_move_info(
                        num_combos_currently,
                        game_state,
                        next_num_queries,
                        corresponding_q_info,
                        move,
                        cost,
                        force_set_intersect=force_set_intersect
                    )
                    if move_info is not None:
                        yield move_info
                        break # TODO: Once start updating minimal_vs_list on *every* call, can break outside of this if statement.

    def _convert_wgs_to_cache_gs_NO_reorder(self, working_game_state):
        """
        Given a working game_state, convert it into a cache game state WITHOUT reordering it into canonical form. Only for use to aid in debugging.
        """
        cache_state_without_reordering_func = (
            solver_utils._convert_working_gs_to_cache_gs_standard_int if self.bitset_type is int else
            solver_utils._convert_working_gs_to_cache_gs_standard_nparray
        )
        cache_state_without_reordering = cache_state_without_reordering_func(
            working_game_state,
            self.all_cwa_bitsets
        )
        return cache_state_without_reordering

    def _print_canonical_form_info(self, game_state, cache_game_state, max_num_forms):
        if ('num_forms' not in globals()):
            global num_forms
            num_forms = 0
        else:
            num_forms += 1
        if not(num_forms < max_num_forms):
            return
        console.rule()
        cache_state_without_reordering = self._convert_wgs_to_cache_gs_NO_reorder(game_state)
        permutation = solver_utils.get_permutation(self, game_state)
        rearranged_colors = [config.VERIFIER_COLORS[num] for num in permutation]
        if not np.array_equal(np.array([i for i in range(self.num_rcs)]), permutation):
            form_equal_string = ("Canonical form [red]not[/red] equal!")
        else:
            form_equal_string = ("Canonical form [green]is[/green] equal!")
        console.print(f"Table # {num_forms + 1:,}. {form_equal_string}\n", justify="center")
        self.sd.print_cache_game_state(
            cache_state_without_reordering,
            "Original",
            config.VERIFIER_COLORS
        )
        print()
        self.sd.print_cache_game_state(
            cache_game_state,
            "Canonical",
            rearranged_colors,
            include_round_info=False,
        )

    def _calculate_best_move(
        # WARN: changing these arguments will require changing the function _const_args_to_calc in this class, as well as the portion of iterative_deepen that updates the new args.
        self,
        qs_dict,
        game_state: Game_State,
        cache_game_state: Game_State,
        pre_existing_result,
        check_one_answer: bool,
        minimal_vs_list: list[set[int]],
        working_cwa_set_convert_cache,
        depth,
        round_depth,
    ):
        # self.called_calculate += 1
        if check_one_answer and one_answer_left(self.full_cwas_list, game_state.cwa_set):
            if config.CACHE_END_STATES:
                self._evaluations_cache[cache_game_state] = Solver.end_game_eval
            return Solver.end_game_eval
        is_begin_round_state = game_state.proposal_used_this_round is None
        if is_begin_round_state:
            if (round_depth == 0):
                self._evaluations_cache[cache_game_state] = Solver.round_depth_cutoff
                return Solver.round_depth_cutoff
            working_cwa_set_convert_cache = dict()
            minimal_vs_list = self._calculate_minimal_vs_list(game_state)
            qs_dict = solver_utils.full_filter(qs_dict, game_state.cwa_set)
            round_depth -= 1

        ######################################## DEBUGGING ###################################################
        # self._print_canonical_form_info(game_state, cache_game_state, max_num_forms=500)
        ######################################## DEBUGGING ###################################################

        search_best_rqd = pre_existing_result[1]
        search_curr_evdepth_LB_rqd = Solver.triple_inf
        found_moves = False
        min_round_depth = inf
        evdepth_infinity = False
        best_move = None
        move_iterable = self.tasks_initialize(
            depth,
            self.get_and_apply_moves(game_state, qs_dict, minimal_vs_list)
        )
        # self._test_equivalence(
        #     self.get_and_apply_moves, self.get_and_apply_moves_OLD, game_state, qs_dict, minimal_vs_list
        # )
        for move_info in move_iterable:
            found_moves = True
            (move, mcost, (f_state_Wgs, t_state_Wgs), p_tup) = move_info
            f_state_Cgs = self.convert_working_gs_to_cache_gs(
                self,
                f_state_Wgs,
                working_cwa_set_convert_cache
            )
            t_state_Cgs = self.convert_working_gs_to_cache_gs(
                self,
                t_state_Wgs,
                working_cwa_set_convert_cache
            )
            f_result = self._evaluations_cache.get(f_state_Cgs, self.neg1_titz)
            t_result = self._evaluations_cache.get(t_state_Cgs, self.neg1_titz)
            f_lower_bound = f_result[-1]
            t_lower_bound = t_result[-1]
            currnode_lower_bound_rqd = self._cost_calculator(
                mcost, p_tup, (f_lower_bound, t_lower_bound)
            )
            if solver_utils.roughly_geq_rqd(currnode_lower_bound_rqd, search_best_rqd):
                # if solver_utils.roughly_lt_rqd(currnode_lower_bound_rqd, search_curr_evdepth_LB_rqd):
                #     search_curr_evdepth_LB_rqd = currnode_lower_bound_rqd
                if depth < self.num_concurrent_tasks:
                    self.progress.update(self.depth_to_tasks_l[depth], advance=1)
                continue
            f_evdepth = f_result[0]
            if (f_evdepth < round_depth):
                f_result = self._calculate_best_move(
                    qs_dict                       = qs_dict,
                    game_state                    = f_state_Wgs,
                    cache_game_state              = f_state_Cgs,
                    pre_existing_result           = f_result,
                    check_one_answer              = (f_evdepth < 0),
                    minimal_vs_list               = minimal_vs_list,
                    working_cwa_set_convert_cache = working_cwa_set_convert_cache,
                    depth                         = depth+1,
                    round_depth                   = round_depth,
                )
                f_evdepth = f_result[0]
                f_lower_bound = f_result[-1]
                currnode_lower_bound_rqd = self._cost_calculator(
                    mcost, p_tup, (f_lower_bound, t_lower_bound)
                )
                if solver_utils.roughly_geq_rqd(currnode_lower_bound_rqd, search_best_rqd):
                    # if solver_utils.roughly_lt_rqd(currnode_lower_bound_rqd, search_curr_evdepth_LB_rqd):
                    #     search_curr_evdepth_LB_rqd = currnode_lower_bound_rqd
                    if depth < self.num_concurrent_tasks:
                        self.progress.update(self.depth_to_tasks_l[depth], advance=1)
                    continue

            t_evdepth = t_result[0]
            if (t_evdepth < round_depth):
                t_result = self._calculate_best_move(
                    qs_dict                       = qs_dict,
                    game_state                    = t_state_Wgs,
                    cache_game_state              = t_state_Cgs,
                    pre_existing_result           = t_result,
                    check_one_answer              = (t_evdepth < 0),
                    minimal_vs_list               = minimal_vs_list,
                    working_cwa_set_convert_cache = working_cwa_set_convert_cache,
                    depth                         = depth+1,
                    round_depth                   = round_depth,
                )
                t_evdepth = t_result[0]
                t_lower_bound = t_result[-1]
                currnode_lower_bound_rqd = self._cost_calculator(
                    mcost, p_tup, (f_lower_bound, t_lower_bound)
                )
                if solver_utils.roughly_geq_rqd(currnode_lower_bound_rqd, search_best_rqd):
                    # if solver_utils.roughly_lt_rqd(currnode_lower_bound_rqd, search_curr_evdepth_LB_rqd):
                    #     search_curr_evdepth_LB_rqd = currnode_lower_bound_rqd
                    if depth < self.num_concurrent_tasks:
                        self.progress.update(self.depth_to_tasks_l[depth], advance=1)
                    continue

            if (f_evdepth < min_round_depth):
                min_round_depth = f_evdepth
            if (t_evdepth < min_round_depth):
                min_round_depth = t_evdepth

            currnode_best_known_rqd = (
                currnode_lower_bound_rqd
                if ((f_evdepth == inf) and (t_evdepth == inf))
                else self._cost_calculator(mcost, p_tup, (f_result[1], t_result[1]))
            )
            if solver_utils.roughly_lt_rqd(currnode_lower_bound_rqd, search_curr_evdepth_LB_rqd):
                search_curr_evdepth_LB_rqd = currnode_lower_bound_rqd

            if solver_utils.roughly_lt_rqd(currnode_best_known_rqd, search_best_rqd):
                search_best_rqd = currnode_best_known_rqd
                best_move = move
                if (currnode_best_known_rqd[0] == is_begin_round_state):
                    evdepth_infinity = True
                    assert (round_depth == 0), round_depth
                    if (currnode_best_known_rqd[1] == 1):
                        break

            if depth < self.num_concurrent_tasks:
                self.progress.update(self.depth_to_tasks_l[depth], advance=1)
            # move_rqd_tups.append((move, node_cost_tup_no_evdepth)) # TODO: delete
        assert (
            (search_curr_evdepth_LB_rqd is self.triple_inf)
            or solver_utils.roughly_geq_rqd(search_best_rqd, search_curr_evdepth_LB_rqd)
            ), f"\nlower bound: {search_curr_evdepth_LB_rqd}\nbest so far: {search_best_rqd}\n{game_state}"


        if found_moves:
            if (
                evdepth_infinity
                or solver_utils.roughly_geq_rqd(search_curr_evdepth_LB_rqd, search_best_rqd)
            ):
                evdepth = inf
                answer = (evdepth, search_best_rqd)
            else:
                evdepth = min_round_depth + is_begin_round_state
                assert (evdepth != inf) # TODO: delete this assert statement.
                answer = (evdepth, search_best_rqd, search_curr_evdepth_LB_rqd)
            self.best_move = best_move
        else: # START COMMENT OUT TO CONSIDER EARLY END ROUND
            new_gs = Game_State(
                num_queries_this_round=0,
                proposal_used_this_round=None,
                cwa_set=game_state.cwa_set
            )
            new_gs_cache_state = Game_State(
                num_queries_this_round=0,
                proposal_used_this_round=None,
                cwa_set=cache_game_state.cwa_set
            )
            new_gs_result = self._evaluations_cache.get(new_gs_cache_state, self.neg1_titz)
            if (new_gs_result[0] >= round_depth):
                answer = new_gs_result
            else:
                answer = self._calculate_best_move(
                    qs_dict                       = qs_dict,
                    game_state                    = new_gs,
                    cache_game_state              = new_gs_cache_state,
                    pre_existing_result           = new_gs_result,
                    check_one_answer              = False,
                    minimal_vs_list               = None, # next invocation will recalculate minimal_vs_list.
                    working_cwa_set_convert_cache = None, # next invocation will create a new one
                    depth                         = depth+1,
                    round_depth                   = round_depth,
                ) # END COMMENT OUT TO CONSIDER EARLY END ROUND

        # TODO: code to consider ending a round early despite having useful moves.
        self._evaluations_cache[cache_game_state] = answer
        return answer

    def _const_args_to_calc(self, working_gs: Game_State) -> dict[str: object]:
        cache_state = self._easy_working_gs_to_cache_gs(working_gs)
        minimal_vs_list = self._calculate_minimal_vs_list(working_gs)
        return {
            "qs_dict"          : self.qs_dict,
            "game_state"       : working_gs,
            "cache_game_state" : cache_state,
            "check_one_answer" : False,
            "depth"            : 0,
            # Additional args specific to nightmare solvers.
            "minimal_vs_list"               : minimal_vs_list,
            "working_cwa_set_convert_cache" : dict(),
        }

    def _easy_working_gs_to_cache_gs(self, working_game_state: Game_State):
        """
        A convenience function for converting a `working_game_state` to a cache_game_state (no permutation info needed). This is used by filter_cache.
        """
        return self.convert_working_gs_to_cache_gs(self, working_game_state, dict())

    def exist_moves(self, curr_working_gs):
        """
        Return True if there are any potentially useful moves to be made in this state with the current proposal_used_this_round. If said proposal is none, return True if there are useful moves to be made this round using any proposal.
        """
        minimal_vs_list = self._calculate_minimal_vs_list(curr_working_gs)
        for mi in self.get_and_apply_moves(
            curr_working_gs,
            self.qs_dict,
            minimal_vs_list,
            force_set_intersect=True
        ):
            return True
        return False

    def _easy_get_list_move_infos(self, working_gs):
        min_vs_list = [set([i]) for i in range(self.num_rcs)]
        return list(self.get_and_apply_moves(working_gs, self.qs_dict, min_vs_list, force_set_intersect=True))

    def _move_rqd_tups_from_working_gs(self, working_gs, sort=True):
        raise NotImplementedError()
        return []

    def _experiment(self):
        return
