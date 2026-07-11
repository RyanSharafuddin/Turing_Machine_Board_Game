import numpy as np
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
        for v_set in minimal_vs_list:
            for arbitrary_v_set_member in v_set:
                break
            if(r_unique_ids_by_verifier[v_index] == r_unique_ids_by_verifier[arbitrary_v_set_member]):
                v_set.add(v_index)
                break
        else:
            minimal_vs_list.append(set([v_index]))
    return minimal_vs_list

def _nightmare_get_and_apply_moves(
        game_state: Game_State,
        qs_dict: dict[int:dict[int:Query_Info]],
        minimal_vs_list: list[set[int]],
        force_set_intersect=False
    ):
    # TODO: step through with a debugger to understand how the minimal vs_list is working.
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
                            # else: # TODO This entire else block can be deleted
                            #     from .import display
                            #     console.print(display.get_move_text(move))
                            #     exit()
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
                        # else: # TODO this entire else block can be deleted
                        #     from . import display
                        #     console.print(display.get_move_text(move))
                        #     console.print(v_set)
                        #     cache_state_without_reordering_func = (
                        #         solver_utils._convert_working_gs_to_cache_gs_standard_int if config.NIGHTMARE_BITSET_TYPE is int else
                        #         solver_utils._convert_working_gs_to_cache_gs_standard_nparray
                        #     )
                        #     cache_state_without_reordering = cache_state_without_reordering_func(
                        #         game_state,
                        #         all_cwa_bitsets
                        #     )
                        #     sd.print_game_state(game_state, "State with ineffective move:")
                        #     sd.print_cache_game_state(cache_state_without_reordering)
                        #     exit()
                    break

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
        "index_function",
    )
    def __init__(self, problem: Problem):
        Solver.__init__(self, problem)

        # WARN TODO: delete the next 2 lines
        # #################################################
        # global all_cwa_bitsets
        # all_cwa_bitsets = self.all_cwa_bitsets
        #################################################################################################

        if not self.full_cwas_list: # invalid problem with no solutions
            return
        self.num_possible_rules = len(self.possible_rules_by_verifier[0])
        self.int_verifier_bit_mask = (1 << self.num_possible_rules) - 1
        self.shift_amounts = [v_index * self.num_possible_rules for v_index in range(self.num_rcs)]
        self.convert_working_gs_to_cache_gs = solver_utils.get_convert_working_to_cache_gs_nightmare(
            self.bitset_type
        )
        self.index_function = solver_utils.get_index_function(self.bitset_type)
        # NOTE: below is only for testing purposes.
        initial_cache_gs = self.convert_working_gs_to_cache_gs(
            self.initial_game_state,
            self.all_cwa_bitsets,
            dict(),
            self.shift_amounts,
            self.int_verifier_bit_mask
        )[0]
        initial_bitset_int = solver_utils.bitset_to_int(initial_cache_gs.cwa_set)
        self.max_hex_length = len(hex(initial_bitset_int).upper()[2:])
        self.max_decimal_length = len(f'{initial_bitset_int:,}')
        testing_stuff(self) # TODO: delete
        sd = display.Solver_Displayer(self)
        sd.print_cache_game_state(initial_cache_gs, "Initial State")

    def _print_canonical_form_info(self, game_state, cache_game_state, permutation, max_num_forms):
        if ('num_forms' not in globals()):
            global num_forms
            num_forms = 0
        else:
            num_forms += 1
        if(num_forms < max_num_forms):
            console.rule()
            rearranged_colors = [config.VERIFIER_COLORS[num] for num in permutation]
            cache_state_without_reordering_func = (
                solver_utils._convert_working_gs_to_cache_gs_standard_int if self.bitset_type is int else
                solver_utils._convert_working_gs_to_cache_gs_standard_nparray
            )
            cache_state_without_reordering = cache_state_without_reordering_func(
                game_state,
                self.all_cwa_bitsets
            )
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
            console.print(f"Permutation: {permutation}", justify="center", sep=" ", end="")

    def _calculate_best_move(
        self,
        qs_dict,
        game_state: Game_State,
        minimal_vs_list: list[set[int]] = None,
        depth = 0,
        working_cwa_set_convert_cache = None,
    ):
        # self.called_calculate += 1
        if game_state.proposal_used_this_round is None:
            working_cwa_set_convert_cache = dict()
            (cache_game_state, permutation) = self.convert_working_gs_to_cache_gs(
                game_state,
                self.all_cwa_bitsets,
                working_cwa_set_convert_cache,
                self.shift_amounts,
                self.int_verifier_bit_mask,
            )
            ###################################### DEBUGGING #################################################
            # self._print_canonical_form_info(game_state, cache_game_state, permutation, max_num_forms=5)
            ###################################### DEBUGGING #################################################
            result = self._evaluations_cache.get(cache_game_state.cwa_set)
            if result is not None:
                # self.cache_hits += 1
                return result
        if one_answer_left(self.full_cwas_list, game_state.cwa_set):
            # if config.CACHE_END_STATES:
            #     self._evaluations_cache[cache_game_state] = Solver.double_zero
            return Solver.double_zero
        best_node_cost = Solver.initial_best_cost
        if game_state.proposal_used_this_round is None:
            minimal_vs_list = _calculate_minimal_vs_list(
                self.num_rcs, game_state, self.full_cwas_list
            )
            # WARN: line below is new and not fully tested/stepped through/debugged in nightmare mode.
            qs_dict = solver_utils.full_filter(qs_dict, game_state.cwa_set) # FILTER

        found_moves = False
        # moves_list = list(nightmare_get_and_apply_moves(game_state, qs_dict, minimal_vs_list))
        # For testing purposes, make the entire moves_list before examining any moves.
        move_iterable = self.tasks_initialize(
            depth,
            _nightmare_get_and_apply_moves(game_state, qs_dict, minimal_vs_list)
        )
        for move_info in move_iterable:
            (move, mcost, gs_tup, p_tup) = move_info
            gs_false_node_cost = self._calculate_best_move(
                qs_dict=qs_dict,
                game_state=gs_tup[0],
                minimal_vs_list=minimal_vs_list,
                depth=depth + 1,
                working_cwa_set_convert_cache=working_cwa_set_convert_cache,
            )
            if (self._cost_calculator(mcost, p_tup, (gs_false_node_cost, (0, 0))) >= best_node_cost):
                # The false node alone would make this move not better than the best move, so don't need to search the true node.
                if depth < self.num_concurrent_tasks:
                    progress.update(self.depth_to_tasks_l[depth], advance=1)
                continue
            gs_true_node_cost = self._calculate_best_move(
                qs_dict=qs_dict,
                game_state=gs_tup[1],
                minimal_vs_list=minimal_vs_list,
                depth=depth + 1,
                working_cwa_set_convert_cache=working_cwa_set_convert_cache,
            )
            gss_costs = (gs_false_node_cost, gs_true_node_cost)
            node_cost_tup = self._cost_calculator(mcost, p_tup, gss_costs)
            if(node_cost_tup < best_node_cost):
                found_moves = True
                best_node_cost = node_cost_tup
                if(
                    (node_cost_tup == (0, 1)) or
                    ((node_cost_tup == (1, 1)) and (game_state.proposal_used_this_round is None))
                ):
                    # can solve within 1 query and 0 rounds, or 1 query and 1 round and all queries cost a round, so return early
                    break
            if depth < self.num_concurrent_tasks:
                progress.update(self.depth_to_tasks_l[depth], advance=1)
        if not found_moves:
            # don't have to recalculate minimal_vs_list here; the next invocation will do that.
            new_gs = Game_State(
                num_queries_this_round=0,
                proposal_used_this_round=None,
                cwa_set=game_state.cwa_set
            )
            best_node_cost = self._calculate_best_move(
                qs_dict=qs_dict,
                game_state=new_gs,
                depth=depth+1
            )
        if game_state.proposal_used_this_round is None:
            self._evaluations_cache[cache_game_state.cwa_set] = best_node_cost
        return best_node_cost

    def _easy_working_gs_to_cache_gs(self, working_game_state: Game_State):
        """
        A convenience function for converting a `working_game_state` to a cache_game_state (no permutation info needed). This is used by filter_cache.
        """
        cache_gs = self.convert_working_gs_to_cache_gs(
            working_game_state,
            self.all_cwa_bitsets,
            dict(),
            self.shift_amounts,
            self.int_verifier_bit_mask
        )[0] # TODO: delete the '[0]' when update to not calculate permutation anymore.
        return cache_gs

    def _get_best_move_and_ncost_from_cache(self, working_game_state: Game_State, default=(None, None)):
        """
        Given a working game state, return the best move, and the cost of the game_state, or default if the game state is not in the cache. This function helps get_move_mcost_gs_ncost_from_cache.

        Returns
        -------
        (best_move, node_evaluation)
        """
        return self._evaluations_cache.get(working_game_state, default)

    def _reconstruct_round(
            self,
            begin_round_working_gs: Game_State,
            desired_eval: tuple[float, float],
            new_cache: dict,
            stack: list[Game_State]
        ):
        """
        Given a working game state that occurs at the beginning of a round, put every (state -> (move, evaluation)) pair that comes up in the best move tree during this round into the `new_cache`. Furthermore, put all the states that begin rounds later in the tree directly after this round into the `stack`. If any move in the best move tree this round involves starting a new round early (currently, that would only be because there are no more useful moves to make this round with the current proposal, though in the future, the program might change to searching the moves that end a round early even if there are still useful moves to make this round with the current proposal), then put all moves from that new round into the `new_cache` too, and the "down-tree" begin round states of that round into the `stack`. Repeat this process as many times as needed until all the down-tree states put into the `stack` are begin-round states. NOTE: Could perhaps consider changing the handling of when new rounds are started early, by putting the non-begin round state that ends this round into the stack, and then filter_cache, which currently asserts that the states it draws from the stack are begin-round states, would instead realize that this state requires making a round-ending move early, and handle the new cache accordingly. This would involve giving _reconstruct_round another argument, perhaps called non_begin_round_working_gs, so that it could take care of putting the move in. Think on how this would change if you change the program to consider round-ending moves early.

        Parameters
        ----------

        begin_round_working_gs:
            the working game state at the beginning of the round that was drawn from the stack by filter_cache. (Or the artificially made begin_round equivalent for a move that ends the round early).

        desired_eval:
            the node cost of `begin_round_working_gs`, obtained by filter_cache from self._evaluations_cache.

        new_cache:
            the new evaluations cache that filter_cache is building up.

        stack:
            A stack of the working game states that end the current round that filter_cache must explore next. Currently all begin-round states, but see discussion above on how that could change.
        """
        intermediate_cache : dict[Game_State, tuple] = dict() # state -> (move, eval)
        qs_dict = solver_utils.full_filter(self.qs_dict, begin_round_working_gs.cwa_set)
        minimal_vs_list = _calculate_minimal_vs_list(
            self.num_rcs, begin_round_working_gs, self.full_cwas_list
        )
        self._reconstruct_round_helper_r(
            qs_dict,
            begin_round_working_gs,
            intermediate_cache,
            desired_eval,
            minimal_vs_list,
            dict()
        )
        intermediate_stack: list[Game_State] = [begin_round_working_gs]
        while intermediate_stack:
            curr_working_gs = intermediate_stack.pop()
            if (
                (curr_working_gs in new_cache) or
                one_answer_left(
                    self.full_cwas_list, curr_working_gs.cwa_set
                )
            ):
                continue
            (move, eval_cost) = intermediate_cache.get(curr_working_gs, (None, None))
            if move is None:
                # 2 possibilities: either had to end round early, so proposal is not None and there are no moves, or this is a new round and should be added to original stack.
                if (curr_working_gs.proposal_used_this_round is None):
                    stack.append(curr_working_gs)
                else:
                    # for debugging purposes, assert that there are no more moves to make:
                    # TODO: delete below
                    console.print(
                        "[#ff6200]The best move tree includes a round where you must end early![/#ff6200]"
                    )
                    minimal_vs_list = _calculate_minimal_vs_list(
                        self.num_rcs, curr_working_gs, self.full_cwas_list
                    )
                    useful_moves = list(
                        _nightmare_get_and_apply_moves(
                            curr_working_gs,
                            qs_dict,
                            minimal_vs_list,
                            force_set_intersect=True
                        )
                    )
                    assert not useful_moves
                    # handle this game state where you have to start a new round early.
                    new_round_early_working_gs = Game_State(
                        num_queries_this_round=0,
                        proposal_used_this_round=None,
                        cwa_set=curr_working_gs.cwa_set
                    )
                    minimal_vs_list = _calculate_minimal_vs_list(
                        self.num_rcs, new_round_early_working_gs, self.full_cwas_list
                    )
                    new_round_early_qs_dict = solver_utils.full_filter(
                        qs_dict, new_round_early_working_gs.cwa_set
                    )
                    self._reconstruct_round_helper_r(
                        new_round_early_qs_dict,
                        new_round_early_working_gs,
                        intermediate_cache,
                        eval_cost,
                        minimal_vs_list,
                        dict()
                    )
                    (begin_round_early_move, begin_round_early_cost) = intermediate_cache[
                        new_round_early_working_gs
                    ]
                    assert begin_round_early_cost == eval_cost
                    new_cache[curr_working_gs] = (begin_round_early_move, begin_round_early_cost)
                    (gs_false, gs_true) = self.apply_move_to_state(begin_round_early_move, curr_working_gs)
                    intermediate_stack.append(gs_false)
                    intermediate_stack.append(gs_true)
            else:
                new_cache[curr_working_gs] = (move, eval_cost)
                (gs_false, gs_true) = self.apply_move_to_state(move, curr_working_gs)
                intermediate_stack.append(gs_false)
                intermediate_stack.append(gs_true)

    def _reconstruct_round_helper_r(
            self,
            qs_dict,
            working_gs: Game_State,
            intermediate_cache: dict,
            desired_eval,

            minimal_vs_list: list[set[int]],
            working_cwa_set_convert_cache: dict
    ):
        """
        The initial invocation of this function should be called on a begin-round `working_gs` with a `desired_eval` picked up from self._evaluations_cache and a fully filtered `qs_dict`. This function will then put every state: (move, evaluation) pair that occurs in this round into `intermediate_cache` (note that states that are not part of the best move tree may have an evaluation of (inf, inf)). States with one answer left and the begin-round states that come after this current round will not be in the cache. A state where there are no more useful moves to be made with the current proposal and the only option is to end the round early may appear in the cache with a move of None. If said state is in the best move tree, it will certainly appear in the cache with a correct evaluation, otherwise it may appear with an evaluation of (inf, inf).
        NOTE: this function will need to be changed if the program is changed to search for moves that end a round early even when there is still useful information to be discovered with the current proposal.

        Parameters
        ----------
        qs_dict:
            The dictionary of queries. WARN: on the initial invocation of this function, the qs_dict must be fully filtered before passed into this function.

        working_gs:
            The game state this function is evaluating and returning the (move, evaluation) pair for. Note that on the initial invocation of this function, working_gs should be a begin-round game state.

        intermediate_cache:
            The dictionary that this function puts its results in. Supplied by initial caller.

        desired_eval:
            A (rounds, queries) tup. The initial invocation of this function should supply the evaluation of the working_gs as supplied by self._evaluations_cache. Subsequent (recursive) invocations should provide a None value for this.
        """
        if one_answer_left(self.full_cwas_list, working_gs.cwa_set):
            return (None, Solver.double_zero)
        cache_gs = self._easy_working_gs_to_cache_gs(working_gs)
        if ((not desired_eval) and (working_gs.proposal_used_this_round is None)):
            evaluation = self._evaluations_cache.get(cache_gs.cwa_set, Solver.initial_best_cost)
            return (None, evaluation)
        intermediate_cache_result = intermediate_cache.get(working_gs)
        if (intermediate_cache_result is not None):
            return intermediate_cache_result
        best_node_cost = Solver.initial_best_cost
        best_move = None
        for move_info in _nightmare_get_and_apply_moves(working_gs, qs_dict, minimal_vs_list):
            (move, mcost, gs_tup, p_tup) = move_info
            gs_false_node_cost = self._reconstruct_round_helper_r(
                qs_dict,
                gs_tup[0],
                intermediate_cache,
                desired_eval=None,
                minimal_vs_list=minimal_vs_list,
                working_cwa_set_convert_cache=working_cwa_set_convert_cache
            )[1]
            if (self._cost_calculator(mcost, p_tup, (gs_false_node_cost, (0, 0))) >= best_node_cost):
                continue
            gs_true_node_cost = self._reconstruct_round_helper_r(
                qs_dict,
                gs_tup[1],
                intermediate_cache,
                desired_eval=None,
                minimal_vs_list=minimal_vs_list,
                working_cwa_set_convert_cache=working_cwa_set_convert_cache
            )[1]
            gss_costs = (gs_false_node_cost, gs_true_node_cost)
            node_cost_tup = self._cost_calculator(mcost, p_tup, gss_costs)
            if (node_cost_tup == desired_eval):
                # (prop, working_v_index) = move
                # answer = ((prop, self.index_function(permutation, working_v_index)), node_cost_tup)
                answer = (move, node_cost_tup)
                intermediate_cache[working_gs] = answer
                return answer
            if ((not desired_eval) and (node_cost_tup < best_node_cost)):
                best_node_cost = node_cost_tup
                best_move = move
                answer = (move, node_cost_tup)
                if(
                    (node_cost_tup == (0, 1)) or
                    ((node_cost_tup == (1, 1)) and (working_gs.proposal_used_this_round is None))
                ):
                    break
        if best_move is None:
            if (desired_eval is not None):
                self._filter_cache_warn_show(
                    working_gs,
                    cache_gs,
                    "ERROR! Did not find a move on this begin round state which leads to the desired eval. Perhaps floating point error is to blame?",
                    end=True
                )
            # Need to start a new round early, b/c no more useful moves left this round.
            new_gs = Game_State(
                num_queries_this_round=0,
                proposal_used_this_round=None,
                cwa_set=working_gs.cwa_set
            )
            # No need to filter the qs dict for the next call, b/c new_gs's proposal_used_this_round is None and the desired_eval is None, so the next call is not going to attempt to calculate the evaluation itself or find a best move; it will instead use the if block near the beginning of the function to get the evaluation from self._evaluations_cache. Ditto minimal_vs_list and working_cwa_set_convert_cache.
            answer = self._reconstruct_round_helper_r(
                qs_dict,
                new_gs,
                intermediate_cache,
                desired_eval=None,
                minimal_vs_list=minimal_vs_list,
                working_cwa_set_convert_cache=working_cwa_set_convert_cache
            )
        # NOTE: if the program is changed to search for early round-ending moves, then at this point, will need to do the new_gs stuff here, even if best_move is not None (so, outside the above if block). Also note that the qs dict will have to be full-filtered here and passed into the recursive call, since that call *will* attempt to find the best move on that state. Or maybe should just return the move as None (so, no need to filter the qs_dict) and calculate the move on the next invocation of this function by reconstruct_round, who will call it on the new game state with a desired evaluation it pulls from _evaluations_cache, if there is one.
        intermediate_cache[working_gs] = answer
        return answer

    def _filter_cache(self):
        """
        Return a new cache that *only* contains the information needed to play the problem perfectly. Useful because pickling is very slow.
        """
        new_evaluations_cache = dict()
        stack : list[Game_State] = [self.initial_game_state]
        while stack:
            curr_working_gs = stack.pop()
            curr_cache_gs = self._easy_working_gs_to_cache_gs(curr_working_gs)
            assert curr_working_gs.proposal_used_this_round is None
            if(
                (curr_working_gs in new_evaluations_cache) or # NOTE: nightmare puts working gs into new cache
                one_answer_left(self.full_cwas_list, curr_working_gs.cwa_set)
            ):
                continue
            gs_evaluation_result: tuple[float, float] = self._evaluations_cache.get(curr_cache_gs.cwa_set)
            if (gs_evaluation_result is None):
                message = (
                    "[red]WARN[/red]: The following game state is in the best game tree path and is a round begin state, but it is not present in the evaluations_cache."
                )
                self._filter_cache_warn_show(curr_working_gs, curr_cache_gs, message, end=False)
                # a bit janky, but set depth high to avoid re-showing progress bar, since progress bar is the only thing depth is currently used for.
                gs_evaluation_result = self._calculate_best_move(self.qs_dict, curr_working_gs, depth=50)
            self._reconstruct_round(curr_working_gs, gs_evaluation_result, new_evaluations_cache, stack)
        return new_evaluations_cache