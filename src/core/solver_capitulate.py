from .solver import *

def fset_answers_from_cwa_set(all_cwas, cwa_set):
    # cwa_set representation_change TODO!!
    return(frozenset([all_cwas[cwa][-1] for cwa in cwa_set]))

class Solver_Capitulate(Solver):
    worst_eval = (inf, inf)
    __slots__ = ()
    def __init__(self, problem: Problem):
        Solver.__init__(self, problem)
        self.num_concurrent_tasks = 0
        self.convert_working_gs_to_cache_gs = solver_utils._do_not_convert_gs
        self.put_cache_gs_in_new_ev_cache   = False

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
        # will need the function to intersect two sets as well as to see if a set is nonempty.
        # NOTE: According to Python docs, if you mix a frozenset and a set in a binary operation, the result's
        # type will match the type of the first operand.
        # See https://docs.python.org/3/library/stdtypes.html#frozenset:~:text=Binary%20operations%20that%20mix%20set%20instances%20with%20frozenset%20return%20the%20type%20of%20the%20first%20operand.%20For%20example%3A%20frozenset(%27ab%27)%20%7C%20set(%27bc%27)%20returns%20an%20instance%20of%20frozenset.
        # Therefore, all of the game states' cwa_sets created below are frozensets.
        if((game_state.proposal_used_this_round is not None) or force_set_intersect):
            cwa_set_if_true = game_state.cwa_set & q_info.cwa_set_true
            # NOTE: bc working game states' cwa_sets are currently of type frozenset, taking the length of a cwa set is less expensive than taking their intersection, which is why true_cwa_set_len is calculated first and its value is used to potentially 'short-circuit' (return early, before doing the set intersection for cwa_set_if_false). If change type from frozenset to Python integer bitset or numpy Hashable array, this may no longer be true (will have to look into the performance of a numpy array 'population count', or see if there's an efficient way to get the population count of a Python integer). If getting the population count is more costly in that case, then you could do the set intersection first, and compare both the ints/numpy arrays to 0 (or the all 0 array) in order to short circuit out of doing a population count.
            true_cwa_set_len = len(cwa_set_if_true)
            if not ((0 < true_cwa_set_len) and (true_cwa_set_len < num_combos_currently)):
                return None # not a useful query
            cwa_set_if_false = game_state.cwa_set & q_info.cwa_set_false
        else:
            # if the game_state.proposal_used_this_round is None, then can pull the cwa_sets directly from the q_info, as they were just updated at the beginning of the round when filtering the query dict.
            cwa_set_if_true = q_info.cwa_set_true
            cwa_set_if_false = q_info.cwa_set_false
            true_cwa_set_len = len(cwa_set_if_true)

        # this is a useful query.
        # cwa_set representation_change Will need a function to get the length of a set.
        p_true = true_cwa_set_len / num_combos_currently
        p_false = 1 - p_true
        # p_false = len(cwa_set_if_false) / num_combos_currently
        p_tuple = (p_false, p_true)
        proposal_used_this_round = None if(num_queries_this_round == 0) else move[0]
        game_state_false = Game_State(
            num_queries_this_round = num_queries_this_round,
            proposal_used_this_round = proposal_used_this_round,
            cwa_set = cwa_set_if_false,
        )
        game_state_true = Game_State(
            num_queries_this_round = num_queries_this_round,
            proposal_used_this_round = proposal_used_this_round,
            cwa_set = cwa_set_if_true,
        )
        gs_tuple = (game_state_false, game_state_true)
        move_info = (move, cost, gs_tuple, p_tuple)
        return move_info

    # giving Solver_Capitulate its own get_and_apply_moves()
    # so changes to Solver's get_and_apply_moves don't affect this.
    def get_and_apply_moves(self, game_state : Game_State, qs_dict: dict, force_set_intersect=False):
        """
        yields from a list of [(move, cost, (game_state_false, game_state_true), (p_false, p_true))].
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
        # cwa_set representation_change TODO!!
        best_expected_result = self.worst_eval # number of answers left, number of combos left.
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
                move_infos = list(self.get_and_apply_moves(current_gs, qs_dict, force_set_intersect=True))
                if not move_infos:
                    new_game_state = Game_State(
                        proposal_used_this_round=None,
                        num_queries_this_round=0,
                        cwa_set=current_gs.cwa_set
                    )
                    move_infos = list(
                        self.get_and_apply_moves(new_game_state, self.qs_dict, force_set_intersect=True)
                    )
                answer = self._choose_best_move_depth_one(move_infos)
                (best_move, best_mcost, best_gs_tup, best_expected_result) = answer
                self._evaluations_cache[current_gs] = (best_move, best_expected_result)
                stack.append(best_gs_tup[0])
                stack.append(best_gs_tup[1])

    def _calculate_actual_expected_for_capitulation(self, game_state: Game_State, new_ev_cache: dict):
        if game_state in new_ev_cache:
            return new_ev_cache[game_state]
        assert bool(game_state.cwa_set)
        if one_answer_left(self.full_cwas_list, game_state.cwa_set):
            return((None, (0, 0)))
        assert (game_state in self._evaluations_cache)
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

    def _experiment(self):
        return

    def _final_printing(self, original_cache: dict, filtered_cache: dict):
        # Overrides _final_printing in Solver. Needs to keep same function signature.
        (best_cost, underperformance) = self._get_perfect_and_underperformance()
        self.sd.capitulate_final_printing(best_cost, underperformance)

    def get_num_begin_round_states(self):
        raise NotImplementedError("You should not be calling this on a capitulate solver.")

    def get_total_states(self):
        raise NotImplementedError("You should not be calling this on a capitulate solver.")