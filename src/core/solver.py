import time, sys
from . import rules, config, solver_utils
from .definitions import *

def make_initial_game_state(full_cwas_list):
    # cwa_set representation_change
    cwa_set = frozenset(list(range(len(full_cwas_list))))
    initial_game_state = Game_State(num_queries_this_round=0, proposal_used_this_round=None, cwa_set=cwa_set)
    return(initial_game_state)

def one_answer_left(full_cwas_list, cwa_set):
    """
    Given a set of CWA as stored in the game state object, returns a boolean according to whether or not there is exactly one unique answer remaining in the CWA set. Faster than just making the entire answer set and calling len() on it, b/c instead of going through every CWA, this returns the moment it finds a second answer.
    """
    # cwa_set representation_change
    # TODO: see if using answer block intersection helps or hurts.
    # TODO: see which of sorting/not sorting the full cwas list in solver_utils.make_full_cwas_list is better.
    seen_answer_set = set()
    # See comments in definitions.Game_State for the format game_state_cwa_set is in.
    # May not be a literal Python set object.
    iterator = iter(cwa_set)
    zeroth_cwa_representation = next(iterator)
    seen_answer_set.add(full_cwas_list[zeroth_cwa_representation][-1])
    current_cwa_representation = next(iterator, None)

    while(current_cwa_representation is not None):
        if(full_cwas_list[current_cwa_representation][-1] not in seen_answer_set):
            return(False)
        current_cwa_representation = next(iterator, None)
    return(True)

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
    return(possible_rule_ids_by_verifier)
# TODO: define a length method if switch to another set representation

# useless_queries = 0
# useful_queries = 0
def create_move_info(
        num_combos_currently,
        game_state: Game_State,
        num_queries_this_round,
        q_info: Query_Info,
        move,
        cost
    ):
    """
    num_queries_this_round is the number there will be after making this move.
    WARN: could be None
    """
    # cwa_set representation_change
    # will need the function to intersect two sets as well as to see if a set is nonempty.
    # NOTE: According to Python docs, if you mix a frozenset and a set in a binary operation, the result's
    # type will match the type of the first operand.
    # See https://docs.python.org/3/library/stdtypes.html#frozenset:~:text=Binary%20operations%20that%20mix%20set%20instances%20with%20frozenset%20return%20the%20type%20of%20the%20first%20operand.%20For%20example%3A%20frozenset(%27ab%27)%20%7C%20set(%27bc%27)%20returns%20an%20instance%20of%20frozenset.
    # Therefore, all of the game states' cwa_sets created below are frozensets.
    if(game_state.proposal_used_this_round is not None):
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
    num_combos_remaining_true = len(cwa_set_if_true)
    p_true = num_combos_remaining_true / num_combos_currently
    p_false = 1 - p_true
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
    return(move_info)

def get_and_apply_moves(game_state : Game_State, qs_dict: dict):
    """
    yields from a list of [(move, cost, (game_state_false, game_state_true), (p_false, p_true))].
    move is a tuple (proposal tuple, rc_index of verifier to query).
    cost is a tuple (round cost, query cost)
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
                    cost
                )
                if(move_info is not None):
                    yield(move_info)
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
                    cost
                )
                if(move_info is not None):
                    yield(move_info)
                # else:
                #     pass # not a useful query. See other comments.

def testing_stuff(self):
    global display
    from . import display
    global sd
    sd = display.Solver_Displayer(self)
    # sd.print_useful_qs_dict_info(self.qs_dict, self.initial_game_state.cwa_set, None, None, False)
    # sd.print_problem(self.rcs_list, self.problem)
    # sd.print_all_possible_answers(
    #     self.full_cwas_list,
    # )
    # exit()

class Solver:
    null_answer = (None, (0,0))
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
        # "testing_stuff",
    )
    initial_best_cost = (float('inf'), float('inf'))
    def __init__(self, problem: Problem):
        self.problem            = problem
        self.n_mode             = (problem.mode == NIGHTMARE)
        self._evaluations_cache = dict()
        self._cost_calculator   = solver_utils.calculate_expected_cost # can also be worst_case_cost
        self.rcs_list           = rules.make_rcs_list(problem)
        self.num_rcs            = len(self.rcs_list)
        self.flat_rule_list     = rules.make_flat_rule_list(self.rcs_list)
        self.full_cwas_list     = solver_utils.make_full_cwas_list(self.n_mode, self.rcs_list)
        self.initial_game_state = make_initial_game_state(self.full_cwas_list)
        self.qs_dict            = solver_utils.make_useful_qs_dict(
            self.full_cwas_list,
            self.initial_game_state.cwa_set,
            self.flat_rule_list,
            self.n_mode,
        )
        # NOTE: the flat_rule_list is *all* rules; not just all possible rules.
        self.expected_cost                      = None # have not called solve() yet.
        self.seconds_to_solve                   = -1 # have not called solve() yet.
        self.size_of_evaluations_cache_in_bytes = -1 # have not called solve() yet.
        self.git_hash                           = None
        self.git_message                        = None
        # expected cost is the expected cost to to solve the problem from the initial state.
        testing_stuff(self) # WARN TODO: delete

    def _print_debug_info(
            self,
            condition: bool,
            game_state: Game_State,
            qs_dict_1: dict,
            qs_dict_2=None
        ):
        """
        Print out debug info (info about the queries dicts and game state) if `condition` is True.
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

    # called_calculate = 0
    # cache_hits = 0
    def _calculate_best_move(self, qs_dict, game_state: Game_State):
        """
        Returns a tuple (best move in this state, expected cost to win from game_state (this is a tuple of (expected rounds, expected total queries))).
        best_move_tup is a tup of (proposal, rc_index)
        """
        # self.called_calculate += 1
        if(game_state in self._evaluations_cache):
            # self.cache_hits += 1
            return(self._evaluations_cache[game_state])
        if(one_answer_left(self.full_cwas_list, game_state.cwa_set)):
            if(config.CACHE_END_STATES):
                self._evaluations_cache[game_state] = Solver.null_answer
            return(Solver.null_answer)
        if(game_state.proposal_used_this_round is None):
            # original_qs_dict = qs_dict                                      # TODO: comment_out testing
            qs_dict = solver_utils.full_filter(qs_dict, game_state.cwa_set)
            ########################## COMMENT OUT THIS SECTION WHEN NOT DEBUGGING ###########################
            # len_before = solver_utils.get_num_queries_in_qs_dict(original_qs_dict)
            # len_now = solver_utils.get_num_queries_in_qs_dict(qs_dict)
            # self._print_debug_info(
            #     len_now < len_before,
            #     game_state,
            #     qs_dict_1=qs_dict,
            #     qs_dict_2=original_qs_dict,
            # )
            ########################## COMMENT OUT THIS SECTION WHEN NOT DEBUGGING ###########################
        best_node_cost = Solver.initial_best_cost
        found_moves = False
        for move_info in get_and_apply_moves(game_state, qs_dict):
            (move, mcost, gs_tup, p_tup) = move_info
            gs_false_node_cost = self._calculate_best_move(qs_dict, gs_tup[0])[1]
            gs_true_node_cost = self._calculate_best_move(qs_dict, gs_tup[1])[1]
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
            answer = (best_move, best_node_cost)
        else:
            new_gs = Game_State(
                num_queries_this_round=0,
                proposal_used_this_round=None,
                cwa_set=game_state.cwa_set
            )
            answer = self._calculate_best_move(qs_dict=qs_dict, game_state=new_gs)

        # comment out else block above and uncomment this to try starting new rounds early as well.
        # if(game_state.num_queries_this_round != 0):
        #     new_gs = Game_State(
        #         num_queries_this_round=0,
        #         proposal_used_this_round=None,
        #         cwa_set=game_state.cwa_set
        #     )
        #     end_round_early_result = self.calculate_best_move(qs_dict=qs_dict, game_state=new_gs)
        #     if(end_round_early_result[1] < best_node_cost):
        #         # breakpoint here to see if there are situations where ending the round early is better.
        #         # can even label the evaluations result with this info, and see if that node makes it into the best move tree.
        #         answer = end_round_early_result

        self._evaluations_cache[game_state] = answer
        return(answer)

    def solve(self):
        """
        Sets up evaluations_cache with the evaluations of all necessary game states.
        """
        start = time.time()
        self._calculate_best_move(qs_dict = self.qs_dict, game_state = self.initial_game_state)
        end = time.time()
        self.seconds_to_solve = int(end - start)
        self.expected_cost = self.get_move_mcost_gs_ncost_from_cache(self.initial_game_state, ((0,0),))[-1]

    def post_solve_printing(self):
        """
        Define what you would like controller to print after solving.
        """
        print(f"Finished.")
        console.print(f"It took {self.seconds_to_solve:,} seconds.")
        from .display import Solver_Displayer
        sd = Solver_Displayer(self)
        sd.print_eval_cache_size()
        if(config.PRINT_POST_SOLVE_DEBUG_INFO):
            global asizeof
            from pympler.asizeof import asizeof # only import this if printing post solve debug info.
            # WARN: The line below itself uses up a lot of memory and time.
            # Make sure PRINT_POST_SOLVE_DEBUG_INFO is off when doing memory-intensive problems.
            self.size_of_evaluations_cache_in_bytes = asizeof(self._evaluations_cache)
            self.print_eval_cache_stats()
            self.print_cache_by_size()
            # console.print(f"{useless_queries:,} useless queries")
            # console.print(f"{useful_queries:,} useful queries")
            # console.print(f"Called calculate: {self.called_calculate:,}.\nCache hits: {self.cache_hits:,}.\nNumber of objects in cache: {len(self.evaluations_cache):,}")
        sys.stdout.flush()

    def get_move_mcost_gs_ncost_from_cache(self, game_state: Game_State, default=None):
        """
        Given a game state, return the best move, the cost of the best move, the resulting (gs_false, gs_true) tuple, and the cost of the game_state, or default if the game state is not in the cache. This function makes it so that solvers can easily change what they put in the evaluations cache for their own purposes, without necessitating changes to controller.py or display.py.

        Returns
        -------
        (best_move, best_move_cost, gs_tuple, node_evaluation)
        """
        if not(game_state in self._evaluations_cache):
            return(default)
        (best_move, node_evaluation) = (
            self._evaluations_cache[game_state][0], self._evaluations_cache[game_state][-1]
        )
        best_mcost = ((Solver.does_move_cost_round(best_move, game_state)), 1)
        gs_tuple = self.apply_move_to_state(best_move, game_state)
        constructed_answer = (best_move, best_mcost, gs_tuple, node_evaluation)
        return(constructed_answer)

    def apply_move_to_state(self, move, gs: Game_State) -> tuple[Game_State, Game_State]:
        """ WARN: Do not use this for anything performance sensitive. Return (gs_false, gs_true) """
        (proposal, v_index) = move
        (q_info_true, q_info_false) = self.qs_dict[proposal][v_index]
        (cwa_set_false, cwa_set_true) = (
            self.intersect_cwa_sets(gs.cwa_set, q_info_false),
            self.intersect_cwa_sets(gs.cwa_set, q_info_true)
        )
        num_queries_this_round = (1 if Solver.does_move_cost_round(move, gs) else (
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
    def does_move_cost_round(move, gs: Game_State):
        proposal = move[0]
        # if num_queries_this_round is 3, then gs.proposal_used.. should be None
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
    def full_cwa_list_from_cwa_set(self, cwa_set):
        # cwa_set representation_change
        """
        Given a cwa_set, return a list of the complete cwas in it. They are sorted in a consistent order.
        """
        full_cwa_list = [self.full_cwas_list[cwa_index] for cwa_index in cwa_set]
        # sort the list in a consistent way so that printouts when debugging are consistent.
        full_cwa_list.sort(key=self.default_cwa_sort_key)
        return(full_cwa_list)

    def full_cwa_list_from_game_state(self, gs: Game_State):
        """ A convenience function for getting the full cwa list directly from a game state """
        return(self.full_cwa_list_from_cwa_set(gs.cwa_set))

    def intersect_cwa_sets(self, cwa_set_1, cwa_set_2):
        """ Used by display.print_useful_qs_dict. """
        # cwa_set representation_change
        return(cwa_set_1 & cwa_set_2)

    def print_cache_by_size(self):
        console.rule()
        console.print(f"\nNumber of game states in evaluations cache by size:", justify="center")
        l = [0] * (len(self.full_cwas_list))
        for gs in self._evaluations_cache:
            # cwa_set representation_change need a function to get length from cwa_set
            # TODO: will need to change significantly once store game state's in the cache with minimal_possible_rules_by_verifier_set s instead of what currently doing.
            l[len(gs.cwa_set) - 1] += 1
        for (size, num) in enumerate(l, start=1):
            console.print(f"{size:>{4},}: {num:>{len(f'{max(l):,}')},}", justify="center")
        console.rule()

    def print_eval_cache_stats(self):
        """ Prints the number of cwa_sets in the evaluations cache that are duplicated and wasting memory. """
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

    def transform_working_gs_to_cache_gs(self, working_gs: Game_State):
        """
        In the future, use this to transform the game states that are used by the program to conduct queries on to the version of the game state that is stored in self._evaluations_cache.
        """
        return(working_gs)

    def filter_cache(self):
        """
        Replace the current self._evaluations_cache with one that *only* contains the information needed to play the problem perfectly. Useful because pickling is very slow.
        """
        if(self._evaluations_cache is None):
            return
        new_evaluations_cache = dict()
        stack : list[Game_State] = [self.initial_game_state]
        added_game_states_set = set()
        while(stack):
            curr_working_gs = stack.pop()
            curr_cache_gs = self.transform_working_gs_to_cache_gs(curr_working_gs)
            if(
                (curr_cache_gs not in added_game_states_set) and
                (not one_answer_left(self.full_cwas_list, curr_working_gs.cwa_set))
            ):
                gs_evaluation_result = self.get_move_mcost_gs_ncost_from_cache(curr_cache_gs)
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