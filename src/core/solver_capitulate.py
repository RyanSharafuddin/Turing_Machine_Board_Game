from .solver import *

class Solver_Capitulate(Solver):
    worst_eval = (inf, inf)
    __slots__ = ()
    def __init__(self, problem: Problem, heuristic_func_index = config.CAPITULATE_HEURISTIC):
        Solver.__init__(self, problem)
        self.num_concurrent_tasks = 0
        self.convert_working_gs_to_cache_gs = solver_utils._do_not_convert_gs
        self.put_cache_gs_in_new_ev_cache   = False
        self._heuristic_func                = self._get_mi_sort_key(heuristic_func_index)
        self.sd.set_heuristic_func_name()

    # giving Solver_Capitulate its own create_move_info so that changes
    # to Solver's create_move_info don't affect it.
    def create_move_info(
            self,
            num_combos_currently,
            game_state: Game_State,
            num_queries_this_round,
            q_info: Query_Info,
            move,
            cost,
            force_set_intersect: bool,
        ):
        """
        `num_queries_this_round`
            the number there will be after making this move.
        `force_set_intersect`
            if this is True, then this function will set intersect the q_info sets with the game state sets in order to determine which cwas are left in each case. (used in the filter_cache function, which does not update the qs_dict). If this is False, then it will only do the set intersect if game_state.proposal_used_this_round is not None. If it is None, it will just pull the cwa_sets straight from the qs dict, b/c the qs_dict was just updated at the beginning of the round.
        WARN: could return None
        """
        # cwa_set representation_change
        if((game_state.proposal_used_this_round is not None) or force_set_intersect):
            cwa_set_T = game_state.cwa_set & q_info.cwa_set_true
            cwa_set_len_T = len(cwa_set_T)
            if not ((0 < cwa_set_len_T) and (cwa_set_len_T < num_combos_currently)):
                return None # not a useful query
            cwa_set_F = game_state.cwa_set & q_info.cwa_set_false
        else:
            # if the game_state.proposal_used_this_round is None, then can pull the cwa_sets directly from the q_info, as they were just updated at the beginning of the round when filtering the query dict.
            cwa_set_T = q_info.cwa_set_true
            cwa_set_F = q_info.cwa_set_false
            cwa_set_len_T = len(cwa_set_T)

        # this is a useful query.
        # cwa_set representation_change Will need a function to get the length of a set.
        p_true = cwa_set_len_T / num_combos_currently
        p_false = 1 - p_true
        # p_false = len(cwa_set_if_false) / num_combos_currently
        p_tuple = (p_false, p_true)
        proposal_used_this_round = None if(num_queries_this_round == 0) else move[0]
        game_state_false = Game_State(num_queries_this_round, proposal_used_this_round, cwa_set_F)
        game_state_true = Game_State(num_queries_this_round, proposal_used_this_round, cwa_set_T)
        gs_tuple = (game_state_false, game_state_true)
        cwa_set_len_F = num_combos_currently - cwa_set_len_T
        sort_key = self._heuristic_func(p_tuple, cwa_set_len_F, cwa_set_len_T, cwa_set_F, cwa_set_T)
        move_info = (move, cost, gs_tuple, p_tuple, sort_key)
        return move_info

    # giving Solver_Capitulate its own get_and_apply_moves()
    # so changes to Solver's get_and_apply_moves don't affect this.
    def get_and_apply_moves(self, game_state : Game_State, qs_dict: dict, force_set_intersect=False):
        """
        yields from a list of [(move, cost, (game_state_false, game_state_true), (p_false, p_true), sort_key)].
        move is a tuple (proposal tuple, rc_index of verifier to query).
        cost is a tuple (round cost, query cost)
        See create_move_info function docstring for what force_set_intersect does.
        """
        # calling len() to figure out num_combos_currently here so don't have to do it repeatedly inside loop
        # cwa_set representation_change Will have to implement a function to get length of set
        num_combos_currently = len(game_state.cwa_set)
        if(game_state.proposal_used_this_round is None):
            # Yield all proposals b/c it's a new round.
            cost = (1, 1)
            next_num_queries = 1
            for (proposal, inner_dict) in qs_dict.items():
                for (verifier_to_query, q_info) in inner_dict.items():
                    move = (proposal, verifier_to_query)
                    move_info = self.create_move_info(
                        num_combos_currently,
                        game_state,
                        next_num_queries,
                        q_info,
                        move,
                        cost,
                        force_set_intersect
                    )
                    if(move_info is not None):
                        yield move_info

        else:
            # There is an existing proposal that you've used in this game state that you can use again without incurring a round cost.
            inner_dict_this_proposal = qs_dict.get(game_state.proposal_used_this_round)
            if(not(inner_dict_this_proposal is None)): # If this proposal still has potentially useful queries
                cost = (0, 1) # considering all queries that don't incur a round cost
                next_num_queries = (game_state.num_queries_this_round + 1) % 3
                for (verifier_to_query, q_info) in inner_dict_this_proposal.items():
                    move = (game_state.proposal_used_this_round, verifier_to_query)
                    move_info = self.create_move_info(
                        num_combos_currently,
                        game_state,
                        next_num_queries,
                        q_info,
                        move,
                        cost,
                        force_set_intersect
                    )
                    if(move_info is not None):
                        yield move_info

    def _choose_best_move_depth_one(self, move_infos:list):
        # console.print(f"\n{self.calculate_call_id = :,}")
        (first_move, _, first_gs_tuple, _, first_sort_key) = move_infos[0]
        best_sort_key = first_sort_key
        answer = (first_move, first_gs_tuple, first_sort_key)
        for(move, mcost, gs_tuple, p_tuple, sort_key) in move_infos:
            # console.print(display.get_move_text(move), ":", f"{sort_key:0.3f}")
            if(sort_key < best_sort_key):
                answer = (move, gs_tuple, best_sort_key)
                best_sort_key = sort_key
        # console.print(f"answer:", display.get_move_text(answer[0]), answer[2])
        return answer

    # NOTE: calculate_best_move must be able to be started with
    #       calculate_best_move(self.qs_dict, self.initial_game_state)
    def _calculate_best_move(self, qs_dict, game_state):
        """ A capitulation """
        stack = [game_state]
        while stack:
            self.calculate_call_id += 1
            current_gs = stack.pop()
            if ((current_gs in self._evaluations_cache) or self.one_answer_left(current_gs)):
                continue
            move_infos = list(self.get_and_apply_moves(current_gs, qs_dict, force_set_intersect=True))
            if not move_infos:
                new_game_state = Game_State(0, None, current_gs.cwa_set)
                move_infos = list(
                    self.get_and_apply_moves(new_game_state, self.qs_dict, force_set_intersect=True)
                )
            answer = self._choose_best_move_depth_one(move_infos)
            (best_move, best_gs_tup, best_sort_key) = answer
            self._evaluations_cache[current_gs] = (best_move, best_sort_key)
            stack.append(best_gs_tup[0])
            stack.append(best_gs_tup[1])

    def _calculate_actual_expected_for_capitulation(self, game_state: Game_State, new_ev_cache: dict):
        if game_state in new_ev_cache:
            return new_ev_cache[game_state]
        assert bool(game_state.cwa_set)
        if self.one_answer_left(game_state):
            return (None, self.double_zero)
        assert (game_state in self._evaluations_cache)
        (best_move, best_sort_key) = self._evaluations_cache[game_state]
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

    def _filter_cache(self):
        filtered_cache = dict()
        self._calculate_actual_expected_for_capitulation(self.initial_game_state, filtered_cache)
        self._validate_filtered_cache(filtered_cache, alternate_first_state=None)
        return filtered_cache

    def _get_perfect_and_underperformance(self):
        """
        Returns
        -------
        (best_cost, underperformance)

        best_cost:
            The cost a perfect solver achieved on this problem, or None if it hasn't been solved yet.

        underperformance:
            The amount the capitulate solver underperformed by, or None if this problem hasn't been solved by a perfect solver.
        """
        from ..problems import problems
        best_solver_info = problems.get_perfect_prob_solver_info(self.problem)
        # NOTE: do not unpack below, for extensibility.
        (best_time, best_cost) = (best_solver_info[0], best_solver_info[1])
        if (best_cost is None):
            return (None, None)
        (bcr, bcq) = best_cost
        (r, q) = self.expected_cost
        underperformance = (r - bcr, q - bcq)
        return (best_cost, underperformance)

    def _called_by_solve(self):
        self._calculate_best_move(
            qs_dict=self.qs_dict,
            game_state=self.initial_game_state
        )

    def _final_printing(self, original_cache: dict, filtered_cache: dict):
        # Overrides _final_printing in Solver. Needs to keep same function signature.
        (best_cost, underperformance) = self._get_perfect_and_underperformance()
        self.sd.capitulate_final_printing(best_cost, underperformance)

    def _calc_post_solve_debug_info(self, original_cache, filtered_cache):
        """ Overrides Solver's _calc_post_solve_debug_info """
        return

    def get_num_begin_round_states(self):
        raise NotImplementedError("You should not be calling this on a capitulate solver.")

    def get_total_states(self):
        raise NotImplementedError("You should not be calling this on a capitulate solver.")