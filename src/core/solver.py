import time, sys
from rich import progress
from . import rules, config, solver_utils
from .definitions import *

def make_initial_game_state(full_cwas_list):
    # cwa_set representation_change
    cwa_set = frozenset(list(range(len(full_cwas_list))))
    initial_game_state = Game_State(num_queries_this_round=0, proposal_used_this_round=None, cwa_set=cwa_set)
    return initial_game_state

def one_answer_left(full_cwas_list, working_cwa_set):
    """
    Given a set of CWA as stored in the working game state object (as opposed to the cache game state object), returns a boolean according to whether or not there is exactly one unique answer remaining in the CWA set. Faster than just making the entire answer set and calling len() on it, b/c instead of going through every CWA, this returns the moment it finds a second answer.
    """
    # cwa_set representation_change
    # TODO: see if using answer block intersection helps or hurts.
    # TODO: see which of sorting/not sorting the full cwas list in solver_utils.make_full_cwas_list is better.
    # See comments in definitions.Game_State for the format game_state_cwa_set is in.
    # May not be a literal Python set object.
    iterator = iter(working_cwa_set)
    zeroth_cwa_representation = next(iterator)
    zeroth_answer = full_cwas_list[zeroth_cwa_representation][-1]
    current_cwa_representation = next(iterator, None)

    while (current_cwa_representation is not None):
        if (full_cwas_list[current_cwa_representation][-1] != zeroth_answer):
            return False
        current_cwa_representation = next(iterator, None)
    return True

def get_set_r_unique_ids_vs_from_cwas_set_representation(
        full_cwas_list,
        cwas_set_representation,
        num_vs,
        n_mode: bool,
    ) ->  list[set[int]]:
    """
    Given a cwas_set, returns a list, where list[i] contains a set of the unique_ids for all possible rules for verifier i.
    """
    # cwa_set representation_change
    # TODO: consider optimizing the 'sets' in possible_rule_ids_by_verifier w/ bitsets or ints or numpy packed bits or bools or something.
    possible_rule_ids_by_verifier = [set() for _ in range(num_vs)]
    # NOTE: if replace the output of this with a numpy packed bits, then instead of doing a slow Python loop
    # here over every CWA, can store a numpy array containing the possible rules by verifier bits for every possible CWA, and replace this with a fast vectorized numpy bitwise OR.
    # for example, let's say that the first CWA assigns some rules to some verifiers that look
    # like this: 00110010 (a numpy array representing which rules are assigned to which verifiers for the zeroth CWA)
    # Then, the next CWA may be 11001010.
    # If you make a numpy double array (an array of arrays) where the double array corresponds to the whole
    # CWA list, and each array within it corresponds to the rules assigned to verifiers for that specific CWA,
    # then, you can get the index the full CWA list double array by which CWAs are present now, and then
    # numpy bitwise OR that indexed list together, for speed gainz. See if you can index a numpy array with a packed bit array; otherwise will have to unpack to booleans. And pay attention to endianness.
    for cwa_index in cwas_set_representation:
        cwa = full_cwas_list[cwa_index]
        (c, p) = (cwa[0], cwa[1])
        for v_index in range(num_vs):
            corresponding_set = possible_rule_ids_by_verifier[v_index]
            rc_index_for_this_v = p[v_index] if(n_mode) else v_index
            unique_id = c[rc_index_for_this_v].unique_id
            corresponding_set.add(unique_id)
    return possible_rule_ids_by_verifier
# TODO: define a length method if switch to another set representation

# useless_queries = 0
# useful_queries = 0
def create_move_info(
        num_combos_currently,
        game_state: Game_State,
        num_queries_this_round,
        q_info: Query_Info,
        move,
        cost,
        force_set_intersect: bool
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
        cwa_set_if_false = game_state.cwa_set &  q_info.cwa_set_false
        if not (bool(cwa_set_if_false) and bool(cwa_set_if_true)):
            return None # not a useful query
    else:
        # if the game_state.proposal_used_this_round is None, then can pull the cwa_sets directly from the q_info, as they were just updated at the beginning of the round when filtering the query dict.
        cwa_set_if_true = q_info.cwa_set_true
        cwa_set_if_false = q_info.cwa_set_false

    # this is a useful query.
    # cwa_set representation_change Will need a function to get the length of a set.
    p_true = len(cwa_set_if_true) / num_combos_currently
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

def testing_stuff(self):
    global display
    from . import display
    global sd
    sd = display.Solver_Displayer(self)
    return sd

progress = solver_utils.progress_initialize()

class Solver:
    double_zero = (0, 0)
    triple_zero = (0, 0, 0)
    inf = float("inf")
    ninf = float("-inf")
    triple_inf = (inf, inf, inf)
    double_inf = (inf, inf)

    end_game_eval = (inf, triple_zero) # (evdepth, best_known_rqd)
    end_game_eval_no_evdepth = triple_zero
    worst_eval = (triple_inf, 0)
    worst_eval_no_evdepth = triple_inf
    round_depth_cutoff = (0, triple_inf, (1, 1, 1))
    result_not_present = (None, ninf) # NOTE: not currently being used
    one_q_zero_r_rqd = (0, 1, 0) # (0 rounds, 1 query, 0 max depth)
    one_q_one_r_rqd = (1, 1, 1)  # (1 round, 1 query, 1 max depth)
    __slots__ = (
        "problem",
        "n_mode",
        "_evaluations_cache",
        "_cost_calculator",
        "rcs_list",
        "num_rcs",
        "flat_rule_list",
        "full_cwas_list",
        "initial_game_state",
        "qs_dict",
        "expected_cost",
        "seconds_to_solve",
        "size_of_evaluations_cache_in_bytes",
        "git_hash",
        "git_message",
        "possible_rules_by_verifier",
        "bitset_type",
        "all_cwa_bitsets",
        "convert_working_gs_to_cache_gs",
        "num_concurrent_tasks",
        "depth_to_tasks_l",

        "biggest_avg_difference_info",
        "biggest_begin_round_avg_difference_info",
        "biggest_depth_difference_info",

        "best_move",
        "put_cache_gs_in_new_ev_cache",
    )
    def __init__(self, problem: Problem):
        self.problem            = problem
        self.n_mode             = (problem.mode == NIGHTMARE)
        self._evaluations_cache = dict()
        self._cost_calculator   = solver_utils.calculate_expected_with_depth_cost
        self.rcs_list           = rules.make_rcs_list(problem)
        self.num_rcs            = len(self.rcs_list)
        self.flat_rule_list     = rules.make_flat_rule_list(self.rcs_list)
        self.full_cwas_list     = solver_utils.make_full_cwas_list(self.n_mode, self.rcs_list)
        self.initial_game_state = make_initial_game_state(self.full_cwas_list)
        self.best_move          = None
        self.qs_dict            = solver_utils.make_useful_qs_dict(self, self.initial_game_state)
        self.put_cache_gs_in_new_ev_cache = True
        if not self.full_cwas_list: # invalid problem with no solutions.
            return
        self.possible_rules_by_verifier = [
            [self.flat_rule_list[r_index] for r_index in sorted(set_r_unique_ids)]
            for set_r_unique_ids in
            solver_utils.get_set_r_unique_ids_vs_from_full_cwas(self.full_cwas_list, self.n_mode)
        ]
        # NOTE: the flat_rule_list is *all* rules; not just all possible rules.
        self.bitset_type        = config.NIGHTMARE_BITSET_TYPE if self.n_mode else config.STANDARD_BITSET_TYPE
        self.all_cwa_bitsets    = solver_utils.get_cwa_bitsets(self)
        self.convert_working_gs_to_cache_gs = solver_utils.get_convert_working_to_cache_gs_standard(
            self.bitset_type
        )
        ############################### PROGRESS WERK ########################################################
        progress_bars_dict = (
            config.N_MODE_PROGRESS_BARS_DICT if self.n_mode else config.S_MODE_PROGRESS_BARS_DICT
        )
        default_progress_bars = (
            config.N_MODE_DEFAULT_PROGRESS_BARS if self.n_mode else config.S_MODE_DEFAULT_PROGRESS_BARS
        )
        self.num_concurrent_tasks = progress_bars_dict.get(self.num_rcs, default_progress_bars)
        self.depth_to_tasks_l     = [
            progress.add_task(f"Calculating depth {depth}:", total=0, visible=False)
            for depth in range(self.num_concurrent_tasks)
        ]
        ############################### PROGRESS WERK ########################################################
        # expected cost is the expected cost to to solve the problem from the initial state.
        self.expected_cost                      = None # have not called solve() yet.
        self.seconds_to_solve                   = -1 # have not called solve() yet.
        self.size_of_evaluations_cache_in_bytes = -1 # have not called solve() yet.
        self.git_hash                           = None
        self.git_message                        = None
        testing_stuff(self) # WARN TODO: delete

        # (bigest_difference, move_cost_tups, game_state, min_depth_move)
        self.biggest_avg_difference_info        = ((self.ninf,) * 2,) + (None,) * 3
        self.biggest_begin_round_avg_difference_info = self.biggest_avg_difference_info
        self.biggest_depth_difference_info        =  (self.ninf,) + (None,) * 3

    @staticmethod
    def get_and_apply_moves(game_state : Game_State, qs_dict: dict, force_set_intersect=False):
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
                    move_info = create_move_info(
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
                    # else:
                    #     pass # not a useful query

        else:
            # There is an existing proposal that you've used in this game state that you can use again without incurring a round cost.
            inner_dict_this_proposal = qs_dict.get(game_state.proposal_used_this_round)
            if(not(inner_dict_this_proposal is None)): # If this proposal still has potentially useful queries
                cost = (0, 1) # considering all queries that don't incur a round cost
                next_num_queries = (game_state.num_queries_this_round + 1) % 3
                for (verifier_to_query, q_info) in inner_dict_this_proposal.items():
                    move = (game_state.proposal_used_this_round, verifier_to_query)
                    move_info = create_move_info(
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
                    # else:
                    #     pass # not a useful query. See other comments.

    def tasks_initialize(self, depth, move_generator):
        if(depth < self.num_concurrent_tasks):
            move_iterable = list(move_generator)
            total = len(move_iterable)
            task_id = self.depth_to_tasks_l[depth]
            progress.reset(task_id, total=total, visible=True)
        else:
            move_iterable = move_generator
        return move_iterable

    def _print_debug_info(
            self,
            condition: bool,
            game_state: Game_State,
            qs_dict_1: dict,
            qs_dict_2=None
        ):
        """
        Print out debug info (partition info about the queries dicts and game state) if `condition` is True.
        """
        if not condition:
            return
        global printed_table_num
        if('printed_table_num' not in globals()):
            printed_table_num = 1
        else:
            printed_table_num += 1
        # Print out an id for each game state so you can easily find it again while scrolling.
        game_state_name = display.Text.assemble(
            f' Printed Game State # ',
            sd.get_problem_id_text(),
            (f' {printed_table_num:,}', "#FF69D7"),
            ".",
        )
        sd.print_game_state(game_state, name=game_state_name)
        # console.print(repr(game_state))
        # for s_to_print in solver_utils.iso_filter_list_to_print:
        #     console.print(s_to_print)
        print(f"Some queries have been eliminated.")
        console.print(
            f'{solver_utils.get_num_queries_in_qs_dict(qs_dict_2)} -> {solver_utils.get_num_queries_in_qs_dict(qs_dict_1)} queries'
        )
        verifiers_to_sort_by=[A]
        if(qs_dict_2 is not None):
            sd.print_useful_qs_dict_info(
                qs_dict_2,
                game_state.cwa_set,
                title=display.Text.assemble(("Original Qs", "bright_white"),),
                verifier_indexes=None,
                proposals_to_examine=None,
                short=True,
                verifiers_to_sort_by=verifiers_to_sort_by
            )
            print()
        sd.print_useful_qs_dict_info(
            qs_dict_1,
            game_state.cwa_set,
            title=display.Text.assemble(("Updated Qs", "bright_white"),),
            verifier_indexes=None,
            proposals_to_examine=None,
            short=True,
            verifiers_to_sort_by=verifiers_to_sort_by
        )
        console.rule()
        return
    def _qs_dict_debugging(self, original_qs_dict, current_qs_dict, gs: Game_State):
        len_before = solver_utils.get_num_queries_in_qs_dict(original_qs_dict)
        len_now = solver_utils.get_num_queries_in_qs_dict(current_qs_dict)
        self._print_debug_info(
            len_now < len_before,
            gs,
            qs_dict_1=current_qs_dict,
            qs_dict_2=original_qs_dict,
        )
    # called_calculate = 0
    # cache_hits = 0

    def get_current_lower_bound(self, gs: Game_State):
        result = self._evaluations_cache.get(gs)
        if result is None:
            return self.triple_zero
        return result[-1]

    def _calculate_best_move(
            self,
            qs_dict,
            game_state: Game_State,
            depth=0,
            round_depth = inf,
        ):
        """
        Return (cost_tup, worst_round_depth)
        """
        # self.called_calculate += 1
        cache_game_state = self.convert_working_gs_to_cache_gs(game_state, self.all_cwa_bitsets)
        result = self._evaluations_cache.get(cache_game_state)
        if result is None:
            # NOTE: at this point, the rqd may actually be (0, 0, 0), but this is fine, since these variables
            #       won't be used until after one_answer_left is checked.
            best_rqd_so_far = self.triple_inf
        else:
            # result is (evdepth, best_known_rqd, optional_lower_bound_rqd)
            if (result[0] >= round_depth):
                # self.cache_hits += 1
                return result
            best_rqd_so_far = result[1]
        if one_answer_left(self.full_cwas_list, game_state.cwa_set):
            return self.end_game_eval
        is_begin_round_state = game_state.proposal_used_this_round is None
        if is_begin_round_state:
            # original_qs_dict = qs_dict                                     # uncomment to debug qs dict
            qs_dict = solver_utils.full_filter(qs_dict, game_state.cwa_set)  # KEEP this line always
            # self._qs_dict_debugging(original_qs_dict, qs_dict, game_state) # uncomment to debug qs dict
            if (round_depth == 0):
                # TODO: consider not storing this result in the cache (but still return worst eval)
                # Should save some memory and cost very little time to not store this.
                self._evaluations_cache[cache_game_state] = self.round_depth_cutoff
                return self.round_depth_cutoff # refuse to search more rounds
            round_depth -= 1

        found_moves = False
        min_round_depth = self.inf
        evdepth_infinity = False
        best_move = None # NOTE: keep this, b/c if there are moves, but none of them are evaluated deeply enough to yield an answer, then the line that assigns to self.best_move will reference best_move before the latter has been assigned to.
        # move_rqd_tups = [] # TODO: delete
        current_evdepth_lower_bound_rqd = None
        move_iterable = self.tasks_initialize(depth, self.get_and_apply_moves(game_state, qs_dict))
        for move_info in move_iterable:
            found_moves = True
            (move, mcost, (f_state, t_state), p_tup) = move_info
            f_curr_lower_bound = self.get_current_lower_bound(f_state)
            t_curr_lower_bound = self.get_current_lower_bound(t_state)
            if (
                self._cost_calculator(mcost, p_tup, (f_curr_lower_bound, t_curr_lower_bound)) >=
                best_rqd_so_far
            ):
                if depth < self.num_concurrent_tasks:
                    progress.update(self.depth_to_tasks_l[depth], advance=1)
                continue
            f_result = self._calculate_best_move(
                qs_dict,
                f_state,
                depth+1,
                round_depth
            )
            f_evdepth = f_result[0]
            f_best_known_rqd = f_result[1]
            assert (f_evdepth >= round_depth)
            if (f_evdepth < min_round_depth):
                min_round_depth = f_evdepth
            f_evdepth_is_inf = (f_evdepth == inf)
            f_curr_evdepth_lower_bound = f_result[-1]
            # # TODO: smarter pruning. Also, make a dedicated single-state cost calculator rather than using the regular 2-state cost calculator and setting one of the states to 0 cost, as you're doing now.
            # TODO: maybe don't also compare depth? i.e. only compare tuple[0:2] for rq? See effect on timing/mem usage.
            if (
                self._cost_calculator(
                    mcost, p_tup, (f_curr_evdepth_lower_bound, self.end_game_eval_no_evdepth)
                ) >= best_rqd_so_far # only compare (rounds, queries, depth) for pruning purposes
            ):
                if depth < self.num_concurrent_tasks:
                    progress.update(self.depth_to_tasks_l[depth], advance=1)
                continue

            t_result = self._calculate_best_move(
                qs_dict,
                t_state,
                depth+1,
                round_depth
            )
            t_evdepth = t_result[0]
            t_best_known_rqd = t_result[1]
            assert (t_evdepth >= round_depth)
            if (t_evdepth < min_round_depth):
                min_round_depth = t_evdepth
            t_evdepth_is_inf = (t_evdepth == inf)
            if not (f_evdepth_is_inf and t_evdepth_is_inf):
                t_curr_evdepth_lower_bound = t_result[-1]
                gss_costs_lower_bound = (f_curr_evdepth_lower_bound, t_curr_evdepth_lower_bound)
                currnode_lower_bound_rqd = self._cost_calculator(mcost, p_tup, gss_costs_lower_bound)
                if currnode_lower_bound_rqd >= best_rqd_so_far:
                    continue
                if (
                    (current_evdepth_lower_bound_rqd is None) or
                    (currnode_lower_bound_rqd < current_evdepth_lower_bound_rqd)
                ):
                    current_evdepth_lower_bound_rqd = currnode_lower_bound_rqd
            gss_costs_best_known_rqd = (f_best_known_rqd, t_best_known_rqd)
            best_known_currnode_cost_rqd = self._cost_calculator(mcost, p_tup, gss_costs_best_known_rqd)
            if(best_known_currnode_cost_rqd < best_rqd_so_far):
                best_rqd_so_far = best_known_currnode_cost_rqd
                best_move = move
                if (best_known_currnode_cost_rqd[0] == is_begin_round_state):
                    evdepth_infinity = True
                    # TODO: turn this on when try iterative deepening.
                    # assert (round_depth == is_begin_round_state) # if this fails, understand why.
                    if (best_known_currnode_cost_rqd[1] == 1):
                        break
            if depth < self.num_concurrent_tasks:
                progress.update(self.depth_to_tasks_l[depth], advance=1)
            # move_rqd_tups.append((move, node_cost_tup_no_evdepth)) # TODO: delete
        if found_moves:
            evdepth = (
                inf
                if (evdepth_infinity or (current_evdepth_lower_bound_rqd is None))
                else min_round_depth + is_begin_round_state
            )
            answer = (
                (evdepth, best_rqd_so_far)
                if (evdepth is inf)
                else (evdepth, best_rqd_so_far, current_evdepth_lower_bound_rqd)
            )
            self.best_move = best_move
        else:
            new_gs = Game_State(
                num_queries_this_round=0,
                proposal_used_this_round=None,
                cwa_set=game_state.cwa_set
            )
            answer = self._calculate_best_move(qs_dict, new_gs, depth+1, round_depth)

        # comment out else block above and uncomment this to try starting new rounds early as well.
        # WARN: If do below, will have to remember what current self.best_move is, and, if the end_round_early_rqd does not beat the best_node_cost_no_evdepth, will have to set self.best_move back to what it was before.
        # if not is_begin_round_state:
        #     new_gs = Game_State(
        #         num_queries_this_round=0,
        #         proposal_used_this_round=None,
        #         cwa_set=game_state.cwa_set
        #     )
        #     (end_round_early_rqd, end_round_early_evdepth) = self._calculate_best_move(
        #       qs_dict, new_gs, depth+1, round_depth
        #     )
        #     if(end_round_early_rqd < NEED_TO_REPLACE):
        #         # breakpoint here to see if there are situations where ending the round early is better.
        #         # can even label the evaluations result with this info,
        #         # and see if that node makes it into the best move tree.
        #         best_node_cost = (end_round_early_rqd, end_round_early_evdepth)
        #     else:
        #         self.best_move = best_move

        # self.update_biggest_counterexamples(move_rqd_tups, game_state) # TODO: delete if not visualizing
        self._evaluations_cache[cache_game_state] = answer # NOTE: keep this
        return answer

    def iterative_deepen(self, qs_dict, gs: Game_State):
        evdepth = 0
        received_evdepth = 0
        while (received_evdepth != inf):
            evdepth += 1
            result = self._calculate_best_move(qs_dict, gs, 0, evdepth)
            received_evdepth = result[0]
            print()

    def iterative_deepen_root(self):
        evdepth = 0
        received_evdepth = 0
        # moves_to_examine = list(self.get_and_apply_moves(self.initial_game_state, self.qs_dict))
        while (received_evdepth != inf):
            evdepth += 1
            console.print(f"Calculating root to depth: {evdepth:,}")
            if self.num_concurrent_tasks:
                progress.start()
            result = self._calculate_best_move(self.qs_dict, self.initial_game_state, 0, evdepth)
            if self.num_concurrent_tasks:
                progress.stop()
            console.print(f"Received evdepth: {result[0]:,}")
            console.print(f"Best known cost : {result[1]}")
            if (len(result) > 2):
                console.print(f"Best lower bound: {result[2]}")
            received_evdepth = result[0]
            print()

    # Same for all solvers.
    def solve(self):
        """
        Sets up evaluations_cache with the evaluations of all necessary game states.
        """
        # if self.num_concurrent_tasks:
        #     progress.start()
        start = time.time()
        # self.initial_calc_best_move()
        # if self.num_concurrent_tasks:
        #     progress.stop()
        self.iterative_deepen_root()
        print("Cleaning up evaluations dictionary . . .")
        filtered_cache = self._filter_cache()
        end = time.time()
        self.seconds_to_solve = int(end - start)
        self.post_solve_printing()
        self.display_biggest_counterexamples()
        self._experiment()
        self._evaluations_cache = filtered_cache
        self.expected_cost = self.get_move_mcost_gs_ncost_from_cache(self.initial_game_state, ((0,0),))[-1]
        self.post_filter_printing()

    # Happens for all solvers; other solvers may add their own additional statements in their own versions.
    def post_filter_printing(self):
        """
        NOTE: happens even on solvers retrieved from pickles.
        """
        if self.n_mode:
            console.print(
                f"There are {len(self.full_cwas_list):,} total possible combos (including rearrangement)."
            )
        console.print(
            f"{self.expected_cost[0]:0.3f}  {self.expected_cost[1]:0.3f} : Expected cost to solve from start"
        )

    # May be overriden by other solvers.
    def post_solve_printing(self):
        """
        Define what you would like to print after solving. Only called on newly solve()d solvers; not on pre-existing pickled solvers. capitulate solver has its own version of this function.
        """
        print(f"Finished.")
        console.print(f"It took {self.seconds_to_solve:,} seconds.")
        try:
            if one_answer_left(self.full_cwas_list, self.initial_game_state.cwa_set):
                initial_evdepth = self.inf
            else:
                initial_state_res = self._evaluations_cache.get(self.initial_game_state)
                (initial_evdepth, (r, q, d)) = initial_state_res[0:2]
            console.print(
                "Depth the initial state was evaluated to:",
                display.Text(f"{initial_evdepth}", style="b cyan")
            )
        except TypeError: # couldn't unpack the (rqd, evdepth) tuple.
            console.print("Could not determine initial evdepth.")
        from .display import Solver_Displayer
        sd = Solver_Displayer(self)

        if(config.PRINT_POST_SOLVE_DEBUG_INFO):
            # NOTE: post solve debug info is based on original (pre-filter) cache.
            # global asizeof
            # from pympler.asizeof import asizeof # only import this if printing post solve debug info.
            # # WARN: The line below itself uses up a lot of memory and time.
            # # Make sure PRINT_POST_SOLVE_DEBUG_INFO is off when doing memory-intensive problems.
            # self.size_of_evaluations_cache_in_bytes = asizeof(self._evaluations_cache)
            # sd.print_eval_cache_size()
            # self.print_eval_cache_stats()
            # self.print_cache_by_size()
            # # console.print(f"{useless_queries:,} useless queries")
            # # console.print(f"{useful_queries:,} useful queries")
            # # console.print(f"Called calculate: {self.called_calculate:,}.\nCache hits: {self.cache_hits:,}.\nNumber of objects in cache: {len(self.evaluations_cache):,}")
            print("\nCalculating post-solve debug information.")
            gs: Game_State
            num_begin_round_states = 0
            for gs in self._evaluations_cache:
                num_begin_round_states += (gs.proposal_used_this_round is None)
            print(f"Number of begin round states: {num_begin_round_states:,}")
            print(f"Total number of states: {len(self._evaluations_cache):,}")
            if len(self._evaluations_cache):
                print(
                    f"Percent of states that are begin round: {100 * num_begin_round_states / len(self._evaluations_cache):0.2f}%."
                )
        sys.stdout.flush()


    ############################### SAME FOR ALL SOLVERS ###############################
    def _get_best_move_and_ncost_from_cache(self, working_game_state: Game_State, default=(None, None)):
        """
        Given a working game state, return the best move, and the cost of the game_state, or default if the game state is not in the cache. This function helps get_move_mcost_gs_ncost_from_cache. Used on *post-filtered* caches.

        Returns
        -------
        (best_move, node_evaluation)
        """
        gs_in_cache = (
            self._easy_working_gs_to_cache_gs(working_game_state)
            if self.put_cache_gs_in_new_ev_cache
            else working_game_state
        )
        return self._evaluations_cache.get(gs_in_cache, default)
    def get_move_mcost_gs_ncost_from_cache(self, working_game_state: Game_State, default=None):
        """
        Given a working game state, return the best move, the cost of the best move, the resulting (gs_false, gs_true) tuple, and the cost of the game_state, or default if the game state is not in the cache. This function makes it so that solvers can easily change what they put in the evaluations cache for their own purposes, without necessitating changes to controller.py or display.py. Applies to *post-filtered* caches.

        Returns
        -------
        (best_move, best_move_cost, gs_tuple, node_evaluation)
        """
        (best_move, node_evaluation) = self._get_best_move_and_ncost_from_cache(working_game_state)
        if node_evaluation is None:
            return default
        best_mcost = ((Solver.does_move_cost_round(best_move, working_game_state)), 1)
        gs_tuple = self.apply_move_to_state(best_move, working_game_state)
        constructed_answer = (best_move, best_mcost, gs_tuple, node_evaluation)
        return constructed_answer
    def apply_move_to_state(self, move, gs: Game_State) -> tuple[Game_State, Game_State]:
        """ WARN: Do not use this for anything performance sensitive. Return (gs_false, gs_true). Note: these are working states this function is dealing with."""
        (proposal, v_index) = move
        (q_info_true, q_info_false) = self.qs_dict[proposal][v_index]
        (cwa_set_false, cwa_set_true) = (
            self.intersect_gscwa_qinfocwa(gs.cwa_set, q_info_false),
            self.intersect_gscwa_qinfocwa(gs.cwa_set, q_info_true)
        )
        num_queries_this_round = (
            1 if Solver.does_move_cost_round(move, gs) else (
                (gs.num_queries_this_round + 1) % 3
            )
        )
        proposal_used_this_round = (None if(num_queries_this_round == 0) else proposal)
        gs_false = Game_State(
            num_queries_this_round=num_queries_this_round,
            proposal_used_this_round=proposal_used_this_round,
            cwa_set=cwa_set_false
        )
        gs_true = Game_State(
            num_queries_this_round=num_queries_this_round,
            proposal_used_this_round=proposal_used_this_round,
            cwa_set=cwa_set_true
        )
        return((gs_false, gs_true))
    @staticmethod
    def does_move_cost_round(move, gs: Game_State) -> bool:
        proposal = move[0]
        # if num_queries_this_round is 0, then gs.proposal_used.. should be None
        return(gs.proposal_used_this_round != proposal)
    def default_cwa_sort_key(self, full_cwa):
        """
        Sort by answer, then by the unique_ids of the combo.
        """
        (c, p, a) = (full_cwa[0], full_cwa[1], full_cwa[-1])
        unique_id_in_c_tup = tuple([r.unique_id for r in c])
        if(self.n_mode):
            return((a, unique_id_in_c_tup, p))
        # not nightmare mode
        return( (a, unique_id_in_c_tup) )
    def full_cwa_list_from_cwa_set(self, working_cwa_set):
        # cwa_set representation_change
        """
        Given a working_cwa_set, return a list of the complete cwas in it. They are sorted in a consistent order.
        """
        full_cwa_list = [self.full_cwas_list[cwa_index] for cwa_index in working_cwa_set]
        # sort the list in a consistent way so that printouts when debugging are consistent.
        full_cwa_list.sort(key=self.default_cwa_sort_key)
        return(full_cwa_list)
    def full_cwa_list_from_game_state(self, working_gs: Game_State):
        """ A convenience function for getting the full cwa list directly from a working game state """
        return(self.full_cwa_list_from_cwa_set(working_gs.cwa_set))
    def intersect_gscwa_qinfocwa(self, gs_cwa_set, q_info_cwa_set):
        """
        Given a working cwa_set from a game state (as opposed to a cache cwa_set) and a cwa_set from a q_info (either True or False), return a working cwa_set that could be used to construct the working game state that results from using the query info on the gs_cwa_set.

        Parameters
        ----------
        gs_cwa_set
            The working cwa_set that came from a game_state (not the cache cwa_set).

        q_info_cwa_set
            The cwa set from a query info

        Returns
        -------
        A cwa_set that could be used to construct another working game state.
        """
        # working cwa_set representation_change
        return(gs_cwa_set & q_info_cwa_set)
    def print_cache_by_size(self):
        #TODO cache_gs: reconsider this function entirely in light of cache bitsets.
        for gs in self._evaluations_cache:
            break
        if type(gs.cwa_set) is not frozenset:
            console.print(
                f"print_cache_by_size not implemented for cache cwa sets of type {type(gs.cwa_set)}. Skipping."
            )
            return
        console.rule()
        console.print(f"\nNumber of game states in evaluations cache by size:", justify="center")
        l = [0] * (len(self.full_cwas_list))
        for gs in self._evaluations_cache:
            l[len(gs.cwa_set) - 1] += 1
        for (size, num) in enumerate(l, start=1):
            console.print(f"{size:>{4},}: {num:>{len(f'{max(l):,}')},}", justify="center")
        console.rule()
    def print_eval_cache_stats(self):
        """ Prints the number of cwa_sets in the evaluations cache that are duplicated and wasting memory. """
        from pympler.asizeof import asizeof # only import this if using it.
        cache_cwa_sets = dict()
        cache_gs_with_same_cwas = dict()
        unnecesary_duplicated_cwa_sets = 0
        wasted_memory = 0
        duplicates_with_same_identity = 0
        for game_state in self._evaluations_cache:
            game_state: Game_State
            if(game_state.cwa_set in cache_cwa_sets):
                previously_seen_list = cache_cwa_sets[game_state.cwa_set]
                cache_gs_with_same_cwas[game_state.cwa_set].append(game_state)
                for previously_seen_item in previously_seen_list:
                    if(previously_seen_item is game_state.cwa_set):
                        duplicates_with_same_identity += 1
                        break
                else:
                    unnecesary_duplicated_cwa_sets += 1
                    previously_seen_list.append(game_state.cwa_set)
                    wasted_memory += asizeof(game_state.cwa_set)
            else:
                cache_cwa_sets[game_state.cwa_set] = [game_state.cwa_set]
                cache_gs_with_same_cwas[game_state.cwa_set] = [game_state]
        list_dups = []
        for previously_seen_list in cache_cwa_sets.values():
            list_dups += previously_seen_list
        console.print(f"Number of unnecessary duplicates          : {unnecesary_duplicated_cwa_sets:,}")
        console.print(f"Number of bytes they waste                : {wasted_memory:,}")
        console.print(f"Alternate number of bytes they waste      : {asizeof(list_dups) - asizeof([None] * len(list_dups)):,}")
        console.print(f"duplicates with same identity             : {duplicates_with_same_identity:,}")
        # for gs_list in cache_gs_with_same_cwas.values():
        #     if(len(gs_list) < 2):
        #         continue
        #     console.rule()
        #     for gs in gs_list:
        #         sd.print_evaluations_cache_info(gs, print_succeeding_game_states=False)
    ############################### SAME FOR ALL SOLVERS ###############################

    ############################### SAME FOR NIGHTMARE AND STANDARD ###############################
    def _get_og_cost_from_state_and_move(self, working_gs: Game_State, move):
        """
        Given a working game state and a move, return a 2-tup of (avg round cost, avg query cost) of solving the state if you have to start with making the given move.

        Returns
        -------
        (round cost, query cost)
        """
        # cwa_set representation_change (change method to calculate length)
        mcost = (int(Solver.does_move_cost_round(move, working_gs)), 1)
        (false_gs, true_gs) = self.apply_move_to_state(move, working_gs)
        p_false = len(false_gs.cwa_set) / len(working_gs.cwa_set)
        p_true = len(true_gs.cwa_set) / len(working_gs.cwa_set)
        p_tup = (p_false, p_true)
        false_cost = self._filter_calculate_best_move(false_gs)
        true_cost = self._filter_calculate_best_move(true_gs)
        false_cost_og = self.new_res_to_og_res(false_cost)
        true_cost_og = self.new_res_to_og_res(true_cost)
        og_cost = solver_utils.calculate_expected_cost(mcost, p_tup, (false_cost_og, true_cost_og))
        return og_cost

    def _filter_cache(self, alternate_first_move=None, alternate_first_state=None):
        """
        Return a new cache that *only* contains the information needed to play the problem perfectly i.e. `cache[state] = (best_move, (avg_rounds, avg_queries))`. Useful because pickling is very slow. The current evaluations cache does not contain best moves, only cache states and their evaluations. Therefore, this filter cache will reconstruct the best moves from the evaluations.
        WARN: using an alternate first state will change self.initial_game_state. If want to restore it later, be sure to save and restore.
        """
        filtered_cache = dict()
        if alternate_first_state is not None:
            self.initial_game_state = alternate_first_state
        if not alternate_first_move:
            stack : list[Game_State] = [self.initial_game_state]
        else:
            # NOTE: self.initial_game_state may now be a different state.
            (gsf, gst) = self.apply_move_to_state(alternate_first_move, self.initial_game_state)
            stack : list[Game_State] = [gsf, gst]
            og_cost = self._get_og_cost_from_state_and_move(self.initial_game_state, alternate_first_move)
            gs_to_put_in_cache = (
                self._easy_working_gs_to_cache_gs(self.initial_game_state)
                if self.put_cache_gs_in_new_ev_cache
                else self.initial_game_state
            )
            filtered_cache[gs_to_put_in_cache] = (alternate_first_move, og_cost)
        while stack:
            curr_working_gs = stack.pop()
            curr_cache_gs = self._easy_working_gs_to_cache_gs(curr_working_gs)
            gs_to_put_in_cache = curr_cache_gs if self.put_cache_gs_in_new_ev_cache else curr_working_gs
            if(
                (gs_to_put_in_cache in filtered_cache) or
                one_answer_left(self.full_cwas_list, curr_working_gs.cwa_set)
            ):
                continue
            self.handle_state(curr_working_gs, curr_cache_gs, gs_to_put_in_cache, stack, filtered_cache)
        self.validate_filtered_cache(filtered_cache, alternate_first_state=alternate_first_state)
        return filtered_cache

    def handle_state(self, curr_working_gs, curr_cache_gs, gs_to_put_in_cache, stack, new_ev_cache):
        if not self.exist_moves(curr_working_gs):
            self.handle_delete_eval(curr_working_gs, curr_cache_gs)
            curr_cache_gs = Game_State(
                proposal_used_this_round=None,
                num_queries_this_round=0,
                cwa_set=curr_cache_gs.cwa_set
            )
        self._handle_state_helper(curr_working_gs, curr_cache_gs, gs_to_put_in_cache, stack, new_ev_cache)

    def _handle_state_helper(self, curr_working_gs, curr_cache_gs, gs_to_put_in_cache, stack, new_ev_cache):
            prev_gs_eval = self.handle_delete_eval(curr_working_gs, curr_cache_gs)
            current_gs_eval = self._filter_calculate_best_move(curr_working_gs)
            self.filter_compare_evals(prev_gs_eval, current_gs_eval, curr_working_gs, curr_cache_gs)
            new_ev_cache[gs_to_put_in_cache] = (self.best_move, self.new_res_to_og_res(current_gs_eval))
            (gs_false, gs_true) = self.apply_move_to_state(self.best_move, curr_working_gs)
            stack.append(gs_false)
            stack.append(gs_true)

    def _filter_cache_error_show(self, working_gs, cache_gs, message, end_program=False):
        console.print(message)
        sd.print_game_state(working_gs, "Working Game State")
        try:
            if cache_gs is not None:
                sd.print_cache_game_state(cache_gs, title="Cache Game State")
        except Exception:
            pass
        print(working_gs)
        print(cache_gs)
        (move_rqd_tups, move_infos) = self.move_rqd_tups_from_working_gs(
            working_gs,
            sort=True,
            round_depth=config.INITIAL_EVAL_DEPTH - 1
        )
        for (index, (move, rqd)) in enumerate(move_rqd_tups):
            console.print(f"{index:>3}", display.get_move_text(move), rqd, end=" ")
        if end_program:
            console.print("Exiting.", style=config.BIG_WARN)
            exit()

    def validate_filtered_cache(self, filtered_cache, alternate_first_state=None):
        """
        Note: expects the cache to be filtered to have 2-tups as cost. So, *post-filtered* cache.
        """
        first_state = self.initial_game_state if (alternate_first_state is None) else alternate_first_state
        self.validate_fcache_helper(filtered_cache, first_state)

    def validate_fcache_helper(self, fcache: dict, wgs: Game_State):
        """
        Returns a 2 tup for cost (avg rounds, avg queries). Use on *post-filtered* caches that store 2-tups.
        """
        if one_answer_left(self.full_cwas_list, wgs.cwa_set):
            return Solver.double_zero # do not change
        cache_gs = self._easy_working_gs_to_cache_gs(wgs) if self.put_cache_gs_in_new_ev_cache else wgs
        (best_move, purported_cost) = fcache.get(cache_gs, (None, Solver.double_inf))
        (gs_false, gs_true) = self.apply_move_to_state(best_move, wgs)
        # cwa_set representation_change
        gsf_prob = len(gs_false.cwa_set) / len(wgs.cwa_set)
        gst_prob = len(gs_true.cwa_set) / len(wgs.cwa_set)
        p_tup = (gsf_prob, gst_prob)
        fcost = self.validate_fcache_helper(fcache, gs_false)
        tcost = self.validate_fcache_helper(fcache, gs_true)
        cost_tup = (fcost, tcost)
        mcost = (int(Solver.does_move_cost_round(best_move, wgs)), 1)
        actual_cost = solver_utils.calculate_expected_cost(mcost, p_tup, cost_tup)
        self.validate_filter_compare_evals(purported_cost, actual_cost, wgs)
        fcache[cache_gs] = (best_move, actual_cost)
        return actual_cost

    def update_biggest_counterexamples(self, move_rqd_tups, game_state):
        (
            is_counterexample, min_depth_move, depth_difference, avg_cost_difference, min_depth_index
        ) = solver_utils.overall_depth_handler(move_rqd_tups) # this function sorts for you.
        if not is_counterexample:
            return
        info_last_3 = (move_rqd_tups, game_state, min_depth_move)
        current_biggest_avg_cost_difference = self.biggest_avg_difference_info[0]
        if avg_cost_difference > current_biggest_avg_cost_difference:
            self.biggest_avg_difference_info = (avg_cost_difference,) + info_last_3
        if game_state.proposal_used_this_round is None:
            current_biggest_begin_round_avg_cost_difference = self.biggest_begin_round_avg_difference_info[0]
            if avg_cost_difference > current_biggest_begin_round_avg_cost_difference:
                self.biggest_begin_round_avg_difference_info = (avg_cost_difference,) + info_last_3
        current_biggest_depth_difference = self.biggest_depth_difference_info[0]
        if depth_difference > current_biggest_depth_difference:
            self.biggest_depth_difference_info = (depth_difference,) + info_last_3

    def display_biggest_counterexamples(self):
        items = (
            self.biggest_avg_difference_info,
            self.biggest_begin_round_avg_difference_info,
            self.biggest_depth_difference_info
        )
        compares = ((self.ninf, self.ninf), (self.ninf, self.ninf), self.ninf)
        messages = (
            "\nShowing the min depth counterexample with the biggest avg difference:",
            "\nShowing the begin round min depth counterexample with the biggest avg difference:",
            "\nShowing the min depth counterexample with the biggest depth difference:"
        )
        for (item, compare, message) in zip(items, compares, messages, strict=True):
            sd.display_counterexample(item, compare, message)

    ############################### SAME FOR NIGHTMARE AND STANDARD ###############################

    ######################### MAY BE DIFFERENT B/T NIGHTMARE AND STANDARD #########################
    def _easy_working_gs_to_cache_gs(self, working_game_state: Game_State):
        """
        A convenience function for converting a `working_game_state` to a cache_game_state (no permutation info needed). This is used by filter_cache.
        """
        return self.convert_working_gs_to_cache_gs(working_game_state, self.all_cwa_bitsets)

    def initial_calc_best_move(self):
        """
        Each solver defines their own way to initially calculate everything. Could even use iterative deepening here.
        """
        self._calculate_best_move(
            qs_dict     = self.qs_dict,
            game_state  = self.initial_game_state,
            depth       = 0,
            round_depth = config.INITIAL_EVAL_DEPTH,
        )

    def _filter_calculate_best_move(self, curr_working_gs, round_depth=config.INITIAL_EVAL_DEPTH):
        return self._calculate_best_move(
            qs_dict     = self.qs_dict,
            game_state  = curr_working_gs,
            depth       = 0,
            round_depth = round_depth
            # TODO: Think about whether a value of 1 works here.
            # I don't think it does, due to pruning. Consider tracking the evdepth to go in the stack in filter cache and passing it as an argument to this function.
        )

    def new_res_to_og_res(self, new_cache_result):
        """
        Converts a cost tuple as stored in solver._evaluations_cache before any processing into an (avg_rounds, avg_queries) cost tuple.
        """
        # evdepth = new_cache_result[0]
        (r, q, d) = new_cache_result[1]
        if len(new_cache_result) > 2:
            console.print("O NOES from new_res_to_og_res!", style=config.BIG_WARN)
        return (r, q)

    def exist_moves(self, curr_working_gs):
        """
        Return True if there are any potentially useful moves to be made in this state with the current proposal_used_this_round. If said proposal is None, return True if there are useful moves to be made this round using any proposal.
        """
        for mi in self.get_and_apply_moves(curr_working_gs, self.qs_dict, force_set_intersect=True):
            return True
        return False

    def _easy_get_list_move_infos(self, working_gs:Game_State):
        return list(self.get_and_apply_moves(working_gs, self.qs_dict, force_set_intersect=True))

    def handle_delete_eval(self, working_gs: Game_State, cache_gs: Game_State):
        """
        Deletes the evaluation of the cache_gs from the cache if it is in the cache and returns the result. Displays warning messages as appropriate.
        """
        if cache_gs in self._evaluations_cache:
            result = self._evaluations_cache[cache_gs]
            del self._evaluations_cache[cache_gs]
            return result
        # not in cache:
        console.print("WARN!!", style=config.BIG_WARN)
        message = (
            "The following game state was expected to be on the path of the best game tree, but it is not present in the evaluations_cache."
        )
        self._filter_cache_error_show(working_gs, cache_gs, message, end_program=False)
        return None

    def filter_compare_evals(self, old_eval, new_eval, wgs: Game_State, cgs: Game_State):
        """
        Used on *pre-filter* costs.

        Params
        -----

        old_eval: a cost
            The old cost. May be None.

        new_eval: a cost.
            Guaranteed to not be None.

        wgs: working Game_State

        cgs: cache Game_State
        """
        if (old_eval is None):
            return
        (old_evdepth, (old_r, old_q, old_d)) = old_eval[0:2]
        (new_evdepth, (new_r, new_q, new_d)) = new_eval[0:2]

        if new_evdepth < old_evdepth:
            console.print("WARN!!", style=config.BIG_WARN)
            print("The new evaluation depth is somehow less than the old evaluation depth.")
            console.print(f"old: {old_eval}\nnew: {new_eval}")
            self._filter_cache_error_show(wgs, cgs, message="", end_program=False)

        if not solver_utils.roughly_geq_2tup((old_r, old_q), (new_r, new_q)):
            console.print("WARN!!", style=config.BIG_WARN)
            print("The new evaluation is somehow strictly worse than the old evaluation!")
            console.print(f"old: {old_eval}\nnew: {new_eval}")
            self._filter_cache_error_show(wgs, cgs, message="", end_program=False)
        elif not (solver_utils.fp_eq(old_r, new_r) and solver_utils.fp_eq(old_q, new_q)):
            console.print("Note:", style=config.SMALL_WARN)
            print(
                "The new evaluation is strictly less than the old evaluation. This is acceptable."
            )
            console.print(f"old: {old_eval}\nnew: {new_eval}")

    def validate_filter_compare_evals(self, old_eval, new_eval, wgs: Game_State):
        """
        Although this function may look similar to self.filter_compare_evals, this one is used on *post-filter* costs, unlike the previous one.

        Params
        -----

        old_eval: a cost
            The old cost. Guaranteed to not be None.

        new_eval: a cost.
            Guaranteed to not be None.

        wgs: working Game_State
        """
        if not solver_utils.roughly_geq_2tup(old_eval, new_eval):
            console.print("WARN!!", style=config.BIG_WARN)
            print("The new evaluation is somehow strictly worse than the old evaluation!")
            console.print(f"old: {old_eval}\nnew: {new_eval}")
            self._filter_cache_error_show(wgs, None, message="", end_program=False)
        elif not (solver_utils.fp_eq_tup(old_eval, new_eval)):
            console.print("Note:", style=config.SMALL_WARN)
            print(
                "The new evaluation is strictly less than the old evaluation. This is acceptable."
            )
            console.print(f"old: {old_eval}\nnew: {new_eval}")

    # TODO: update
    def move_rqd_tups_from_working_gs(
            self, working_gs: Game_State, sort=True, round_depth=config.INITIAL_EVAL_DEPTH
        ):
        """
        Given a working game state, returns `(move_rqd_tups, move_infos)`. WARN: do not use for performance-sensitive calculations. Used on *pre-filter* cache.

        Args
        ----
        working_gs: Game_State
            The game state to get the move_cost_tups for
        sort: bool
            If this is true, the move_cost_tups will be sorted by ascending cost.

        Returns
        ------
        move_rqd_tups: list
            A list of (move, rqd) tuples. cost from *pre-filtered* cache.
        move_infos: list
            A list of move_infos corresponding to the move_cost_tups
        """
        move_rqd_tups = []
        move_infos = self._easy_get_list_move_infos(working_gs)
        for mi in move_infos:
            (move, mcost, (gsf, gst), p_tup) = mi
            (false_rqd, false_evdepth) = self._filter_calculate_best_move(gsf, round_depth)
            (true_rqd, true_evdepth) = self._filter_calculate_best_move(gst, round_depth)
            move_rqd = self._cost_calculator(mcost, p_tup, (false_rqd, true_rqd))
            move_rqd_tups.append((move, move_rqd))
        if (sort and bool(move_rqd_tups)):
            mvrqd_mi_combined = list(zip(move_rqd_tups, move_infos, strict=True))
            # mvrqd_mi_combined = [(mvrqd, mi), (mvrqd, mi)]
            mvrqd_mi_combined.sort(key = lambda x: x[0][1])
            (move_rqd_tups, move_infos) = zip(*mvrqd_mi_combined)
        return (move_rqd_tups, move_infos)

    # TODO: update
    def _experiment(self):
        pass
        # sd = testing_stuff(self)
        # (move_rqd_tups, move_infos) = self.move_rqd_tups_from_working_gs(
        #     self.initial_game_state,
        #     sort=True,
        #     round_depth=config.INITIAL_EVAL_DEPTH - 1
        # )
        # movrqd_filtered_to_unique = []
        # seen_rqds = set()
        # for move_rqd_tup in move_rqd_tups:
        #     (move, rqd) = move_rqd_tup
        #     rqd_str = solver_utils.rqd_to_str(rqd)
        #     if (rqd_str not in seen_rqds):
        #         movrqd_filtered_to_unique.append(move_rqd_tup)
        #         seen_rqds.add(rqd_str)
        # sd.print_table_move_rqd_tups(movrqd_filtered_to_unique)
        # console.print("Lowest expected query move highlighted in light blue.")
        # message = "\nTop-level depth counterexamples:"
        # (is_counterexample, _, _, _, min_depth_index) = solver_utils.overall_depth_handler(
        #     movrqd_filtered_to_unique
        # )
        # if is_counterexample:
        #     sd.print_min_depth_counterexample_table(movrqd_filtered_to_unique, min_depth_index, message)