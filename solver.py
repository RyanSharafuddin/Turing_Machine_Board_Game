from line_profiler import profile
import math, itertools, time
import rules, config
from definitions import *
# from rich import print as rprint

def get_all_rules_combinations(rcs_list):
    """ Returns all combinations of rules from the rules cards, whether possible or not. """
    num_rules_cards = len(rcs_list)
    rcs_lengths = [len(rules_card) for rules_card in rcs_list]
    total_num_combinations = math.prod(rcs_lengths)
    rules_combos = [
        [
            rcs_list[rc_index][
                (combo_num // math.prod(rcs_lengths[rc_index + 1:])) % rcs_lengths[rc_index]
            ]
            for rc_index in range(num_rules_cards)
        ] for combo_num in range(total_num_combinations)
    ]
    # print all combos, possible or not.
    # for (combo_num, combo) in enumerate(rules_combos, start=1):
    #     print(f'{combo_num}: {[rule.name for rule in combo]}')
    return(rules_combos)

def is_combo_possible(combo):
    """
    WARN: can return None.
    In Turing Machine, there are 2 requirements that any valid combination of verifiers/rules must satisfy:
    1) There must be exactly one possible answer.
    2) Each verifier eliminates at least one possibility that is not eliminated by any other verifier.
    If the rules in combo satisfy those requirements, this function will return the one answer that satisfies all verifiers. Otherwise, this function will return None.
    """
    reject_sets = [rule.reject_set for rule in combo]
    reject_sets_unions = set.union(*reject_sets)
    if(len(reject_sets_unions) != (len(all_125_possibilities_set) - 1)):
        return(None)
    answer = (all_125_possibilities_set - reject_sets_unions).pop()
    for (i, reject_set) in enumerate(reject_sets):
        all_other_reject_sets = reject_sets[0 : i] + reject_sets[i + 1 :]
        other_reject_sets_union = set.union(*all_other_reject_sets)
        if(not(reject_set - other_reject_sets_union)):
            return(None) # means that this rule is redundant.
    return(answer)

def get_possible_rules_combos_with_answers(rules_cards_list):
    all_rules_combos = get_all_rules_combinations(rules_cards_list)
    return([(c, a) for (c,a) in [(c, is_combo_possible(c)) for c in all_rules_combos] if(a is not None)])

def one_answer_left(game_state_cwa_set):
    """
    Given a set of CWA as stored in the game state object, returns a boolean according to whether or not there is exactly one unique answer remaining in the CWA set. Faster than just making the entire answer set and calling len() on it, b/c instead of going through every CWA, this returns the moment it finds a second answer.
    NOTE: if you change the game_state cwa sets to be implemented using a set of integers, or a list of booleans, or numpy bit pack, or a single long integer, or something else, will need to change the parameters: will need to add full_cwa as a parameter of this function.
    """
    seen_answer_set = set()
    # See comments in definitions.Game_State for the format game_state_cwa_set is in.
    # May not be a literal Python set object.
    iterator = iter(game_state_cwa_set)
    zeroth_cwa_representation = next(iterator)
    seen_answer_set.add(zeroth_cwa_representation[-1])
    current_cwa_representation = next(iterator, None)

    while(current_cwa_representation is not None):
        if(current_cwa_representation[-1] not in seen_answer_set):
            return(False)
        current_cwa_representation = next(iterator, None)
    return(True)

def get_set_r_unique_ids_vs_from_full_cwas(full_cwas, n_mode: bool):
    """
    Given a full_cwas iterable, returns a list, where list[i] contains a set of the unique_ids for all possible rules for verifier i.
    """
    num_vs = len(full_cwas[0][0])
    # TODO: consider optimizing the 'sets' belows w/ bitsets or something.
    possible_rule_ids_by_verifier = [set() for _ in range(num_vs)]
    for cwa in full_cwas:
        (c, p) = (cwa[0], cwa[1])
        for (v_index, rule) in enumerate(c):
            corresponding_set = possible_rule_ids_by_verifier[v_index]
            possible_rule = c[p[v_index]] if(n_mode) else rule
            corresponding_set.add(possible_rule.unique_id)
    return(possible_rule_ids_by_verifier)

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

def make_useful_qs_dict(all_125_possibilities_set, possible_combos_with_answers, flat_rule_list, n_mode):
    useful_queries_dict = dict()
    rules_by_verifier = get_set_r_unique_ids_vs_from_full_cwas(possible_combos_with_answers, n_mode)
    for (unsolved_verifier_index, possible_rule_ids_this_verifier) in enumerate(rules_by_verifier):
        if(len(possible_rule_ids_this_verifier) < 2):
            continue # this verifier is solved and has no useful queries, so on to the next one
        possible_rules_this_verifier = [flat_rule_list[r_id] for r_id in possible_rule_ids_this_verifier]
        for proposal in all_125_possibilities_set:
            rejecting_rules_ids = set()
            for possible_rule in possible_rules_this_verifier:
                if(proposal in possible_rule.reject_set):
                    rejecting_rules_ids.add(possible_rule.unique_id)
            if(0 < len(rejecting_rules_ids) < len(possible_rules_this_verifier)): # useful query
                possible_cwa_indexes_set_remaining_if_true = set()
                possible_cwa_indexes_set_remaining_if_false = set()
                for cwa in possible_combos_with_answers:
                    (c, p) = (cwa[0], cwa[1])
                    combo_rule_id = c[(
                        p[unsolved_verifier_index] if(n_mode) else unsolved_verifier_index
                    )].unique_id
                    cwa_index = ((tuple([r.card_index for r in cwa[0]]),) + cwa[1:])
                    if(combo_rule_id in rejecting_rules_ids):
                        possible_cwa_indexes_set_remaining_if_false.add(cwa_index)
                    else:
                        possible_cwa_indexes_set_remaining_if_true.add(cwa_index)

                query_info = Query_Info(
                    possible_cwa_indexes_set_remaining_if_true,
                    possible_cwa_indexes_set_remaining_if_false
                )
                if(proposal in useful_queries_dict):
                    inner_dict = useful_queries_dict[proposal]
                    assert (not(unsolved_verifier_index in inner_dict))
                    inner_dict[unsolved_verifier_index] = query_info
                else:
                    useful_queries_dict[proposal] = {
                        unsolved_verifier_index: query_info
                    }
    return(useful_queries_dict)

def fset_answers_from_cwa_iterable(cwa_iterable):
    return(frozenset([cwa[-1] for cwa in cwa_iterable]))

def create_move_info(num_combos_currently, game_state, num_queries_this_round, q_info, move, cost):
    """
    num_queries_this_round is the number there will be after making this move.
    WARN: could be None
    """
    fset_indexes_cwa_remaining_true = \
        game_state.fset_cwa_indexes_remaining & q_info.set_indexes_cwa_remaining_true
    fset_indexes_cwa_remaining_false = \
        game_state.fset_cwa_indexes_remaining &  q_info.set_indexes_cwa_remaining_false
    if(bool(fset_indexes_cwa_remaining_false) and bool(fset_indexes_cwa_remaining_true)):
        # this is a useful query.
        num_combos_remaining_true = len(fset_indexes_cwa_remaining_true)
        p_true = num_combos_remaining_true / num_combos_currently
        p_false = 1 - p_true
        p_tuple = (p_false, p_true)
        proposal_used_this_round = None if(num_queries_this_round == 0) else move[0]
        game_state_false = Game_State(
            num_queries_this_round = num_queries_this_round,
            proposal_used_this_round = proposal_used_this_round,
            fset_cwa_indexes_remaining = fset_indexes_cwa_remaining_false,
        )
        game_state_true = Game_State(
            num_queries_this_round = num_queries_this_round,
            proposal_used_this_round = proposal_used_this_round,
            fset_cwa_indexes_remaining = fset_indexes_cwa_remaining_true,
        )
        gs_tuple = (game_state_false, game_state_true)
        move_info = (move, cost, gs_tuple, p_tuple)
    else:
        # this is not a useful query. Take move out of the game state frozen set representing remaining moves, if you implement it. Actually, take out all such useless moves before making the next game states. Will require some refactoring.
        move_info = None
    return(move_info)

def nightmare_get_and_apply_moves(
        game_state: Game_State,
        qs_dict: dict[int:dict[int:Query_Info]],
        minimal_vs_list: list[set[int]]
    ):
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


def get_and_apply_moves(game_state, qs_dict):
    """
    yields from a list of [(move, cost, (game_state_false, game_state_true), (p_false, p_true))].
    move is a tuple (proposal tuple, rc_index of verifier to query).
    cost is a tuple (round cost, query cost)
    """
    # calling len() to figure out num_combos_currently here so don't have to do it repeatedly inside loop
    num_combos_currently = len(game_state.fset_cwa_indexes_remaining)
    if (game_state.proposal_used_this_round is not None):
        # There is an existing proposal that you've used in this game state that you can use again without incurring a round cost.
        inner_dict_this_proposal = qs_dict.get(game_state.proposal_used_this_round)
        if(not(inner_dict_this_proposal is None)): # If this proposal still has potentially useful queries
            cost = (0, 1) # considering all queries that don't incur a round cost
            next_num_queries = (game_state.num_queries_this_round + 1) % 3
            for (v_index, q_info) in inner_dict_this_proposal.items():
                move = (game_state.proposal_used_this_round, v_index)
                move_info = create_move_info(num_combos_currently, game_state, next_num_queries, q_info, move, cost)
                if(move_info is not None):
                    yield(move_info)
                else:
                    # TODO: use line profiling to figure out how many times you're hitting this line (as well as the equivalent line in the block below), and get an estimate of how much time you spend on the set intersection operation in create_move_info on useless queries, and, if it's substantial, consider making a new qs_dict with every call to calculate_best_move that doesn't include known useless queries. But maybe before doing this, replace the set_indexes_cwa in game_states and q_infos with simple ints that are indexes into the solver.full possible combos list (not tuples for index, answer; just ints), and make a function called contains_one_answer(cwa_index_list, full_cwa_list). This way, performing set intersection should take substantially less time, which will better inform you if making new qs_dicts with every calculate_best_move call is worth it.
                    pass # not a useful query. See other comments.

    # Have finished yielding all moves that don't incur a round cost (if there were any). Now consider all moves which do incur a round cost.
    cost = (1, 1)
    next_num_queries = 1
    for (proposal, inner_dict) in qs_dict.items():
        if(proposal == game_state.proposal_used_this_round):
            continue # no sense starting a new round when you could have remained on same round.
        for (v_index, q_info) in inner_dict.items():
            move = (proposal, v_index)
            move_info = create_move_info(num_combos_currently, game_state, next_num_queries, q_info, move, cost)
            if(move_info is not None):
                yield(move_info)
            else:
                pass # not a useful query

def calculate_expected_cost(mcost, probs, gss_costs):
    (mcost_rounds, mcost_queries) = mcost
    (p_false, p_true) = probs
    ((gs_false_round_cost, gs_false_query_cost), (gs_true_round_cost, gs_true_query_cost)) = gss_costs
    expected_r_cost = mcost_rounds + (p_false * gs_false_round_cost) + (p_true * gs_true_round_cost)
    expected_q_cost = mcost_queries + (p_false * gs_false_query_cost) + (p_true * gs_true_query_cost)
    return((expected_r_cost, expected_q_cost))

def fset_cwa_indexes_remaining_from_full_cwa(full_cwa):
    fset_cwa_indexes_remaining = frozenset(
            [(tuple([r.card_index for r in cwa[0]]),) + cwa[1:] for cwa in full_cwa]
        )
    return(fset_cwa_indexes_remaining)

def make_full_cwa(problem, rcs_list):
    possible_combos_with_answers = get_possible_rules_combos_with_answers(rcs_list)
    if(problem.mode == NIGHTMARE):
        nightmare_possible_combos_with_answers = []
        vs = list(range(len(rcs_list))) # vs = [0, 1, 2, . . . for number of verifiers]
        verifier_permutations = tuple(itertools.permutations(vs))
        for original_cwa in possible_combos_with_answers:
            for v_permutation in verifier_permutations:
                nightmare_possible_combos_with_answers.append((original_cwa[0], v_permutation, original_cwa[1]))
        possible_combos_with_answers = nightmare_possible_combos_with_answers
        # possible_combos_with_answers is now [(full rule combo, full permutation, answer), ...]
    return(possible_combos_with_answers)

class Solver:
    null_answer = (None, None, None, (0,0))
    initial_best_cost = (float('inf'), float('inf'))
    def __init__(self, problem: Problem):
        self.problem            = problem
        self.n_mode             = (problem.mode == NIGHTMARE)
        self.evaluations_cache  = dict()
        self.rcs_list           = rules.make_rcs_list(problem)
        self.num_rcs            = len(self.rcs_list)
        self.flat_rule_list     = rules.make_flat_rule_list(self.rcs_list)
        self.full_cwa           = make_full_cwa(problem, self.rcs_list)
        self.initial_game_state = Game_State(
                                    0,
                                    None,
                                    fset_cwa_indexes_remaining_from_full_cwa(self.full_cwa)
                                )
        self.calculator         = (
                                    self.nightmare_calculate_best_move if(self.n_mode)
                                    else self.calculate_best_move
                                )
        self.seconds_to_solve   = -1 # have not called solve() yet.
        if(not(self.full_cwa)):
            return

        # self.rc_indexes_cwa_to_full_combos_dict # TODO eliminate (see big optimization)
        self.rc_indexes_cwa_to_full_combos_dict = {
            (tuple([r.card_index for r in cwa[0]]),) + cwa[1:] : cwa for cwa in self.full_cwa
        }


        self.qs_dict        = make_useful_qs_dict(
            all_125_possibilities_set, self.full_cwa, self.flat_rule_list, (problem.mode == NIGHTMARE)
        )
        self.testing_stuff() # WARN TODO: delete

    def testing_stuff(self):
        if(config.PICKLE_DIRECTORY == "Pickles/DreamCatcher"):
            self.calculator = self.nightmare_calculate_best_move
        else:
            self.calculator = self.calculate_best_move
        import display
        global sd
        sd = display.Solver_Displayer(self)

    def calculate_minimal_vs_list(self, game_state: Game_State) -> list[set[int]]:
        """ WARN: only use in nightmare mode. """
        minimal_vs_list: list[set[int]] = []
        r_unique_ids_by_verifier = get_set_r_unique_ids_vs_from_cwas_set_representation(
            game_state.fset_cwa_indexes_remaining,
            self.rcs_list
        )
        # TESTING # TODO
        # full_cwas = self.full_cwa_from_game_state(game_state)
        # full_cwa_r_unique_ids = get_set_r_unique_ids_vs_from_full_cwas(full_cwas, n_mode=True)
        # assert r_unique_ids_by_verifier == full_cwa_r_unique_ids
        # END TESTING
        for v_index in range(self.num_rcs):
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

    # see get_moves docstring for definitions of move and cost.
    # NOTE: don't use the class's qs_dict just yet. Keep passing it down, in case you want to make new ones in the future. See todo.txt.
    @profile
    def calculate_best_move(self, qs_dict, game_state: Game_State):
        """
        Returns a tuple (best move in this state, mov_cost_tup, gs_tup, expected cost to win from game_state (this is a tuple of (expected rounds, expected total queries))).
        best_move_tup is a tup of (proposal, rc_index)
        """
        if(game_state in self.evaluations_cache):
            return(self.evaluations_cache[game_state])
        if(one_answer_left(game_state.fset_cwa_indexes_remaining)):
            if(config.CACHE_END_STATES):
                self.evaluations_cache[game_state] = Solver.null_answer
            return(Solver.null_answer)
        best_node_cost = Solver.initial_best_cost
        found_zero_more_round_sol = False
        exist_moves_that_dont_cost_a_round = False

        for move_info in get_and_apply_moves(game_state, qs_dict):
            (move, mcost, gs_tup, p_tup) = move_info
            if(mcost[0] == 0):
                exist_moves_that_dont_cost_a_round = True
            if((mcost[0] == 1) and (exist_moves_that_dont_cost_a_round or found_zero_more_round_sol)):
                # there are moves that don't cost a new round, so don't consider any moves that cost a round.
                # or have found a 0 round soln, so don't consider any moves that do cost a round.
                # NOTE: although exist_moves_that_dont_cost_a_round significantly prunes the tree, I'm not convinced this will necessarily find a best move.
                break

            gs_false_node_cost = self.calculate_best_move(qs_dict, gs_tup[0])[3]
            gs_true_node_cost = self.calculate_best_move(qs_dict, gs_tup[1])[3]
            gss_costs = (gs_false_node_cost, gs_true_node_cost)
            node_cost_tup = calculate_expected_cost(mcost, p_tup, gss_costs)
            if(node_cost_tup < best_node_cost):
                if(node_cost_tup[0] == 0):
                    found_zero_more_round_sol = True
                best_node_cost = node_cost_tup
                best_move = move
                best_mov_cost = mcost
                best_gs_tup = gs_tup
                if(
                    (node_cost_tup == (0, 1)) or
                    ((node_cost_tup == (1, 1)) and game_state.proposal_used_this_round is None)
                ):
                    # can solve within 1 query and 0 rounds, or 1 query and all queries cost a round, so return early
                    break
        answer = (best_move, best_mov_cost, best_gs_tup, best_node_cost)
        self.evaluations_cache[game_state] = answer
        return(answer)

    def nightmare_calculate_best_move(
        self,
        qs_dict,
        game_state: Game_State,
        minimal_vs_list: list[set[int]] = None,

    ):
        if(game_state in self.evaluations_cache):
            return(self.evaluations_cache[game_state])
        if(one_answer_left(game_state.fset_cwa_indexes_remaining)):
            if(config.CACHE_END_STATES):
                self.evaluations_cache[game_state] = Solver.null_answer
            return(Solver.null_answer)
        best_node_cost = Solver.initial_best_cost
        if(game_state.proposal_used_this_round is None):
            minimal_vs_list = self.calculate_minimal_vs_list(game_state)

        found_moves = False
        # moves_list = list(nightmare_get_and_apply_moves(game_state, qs_dict, minimal_vs_list))
        # For testing purposes, make the entire moves_list before examining any moves.
        for move_info in nightmare_get_and_apply_moves(game_state, qs_dict, minimal_vs_list):
            (move, mcost, gs_tup, p_tup) = move_info
            gs_false_node_cost = self.nightmare_calculate_best_move(
                qs_dict, gs_tup[0],
                minimal_vs_list
            )[3]
            gs_true_node_cost = self.nightmare_calculate_best_move(
                qs_dict,
                gs_tup[1],
                minimal_vs_list
            )[3]
            gss_costs = (gs_false_node_cost, gs_true_node_cost)
            node_cost_tup = calculate_expected_cost(mcost, p_tup, gss_costs)
            if(node_cost_tup < best_node_cost):
                found_moves = True
                best_node_cost = node_cost_tup
                best_move = move
                best_mov_cost = mcost
                best_gs_tup = gs_tup
                if(
                    (node_cost_tup == (0, 1)) or
                    ((node_cost_tup == (1, 1)) and game_state.proposal_used_this_round is None)
                ):
                    # can solve within 1 query and 0 rounds, or 1 query and all queries cost a round, so return early
                    break
        if(found_moves):
            answer = (best_move, best_mov_cost, best_gs_tup, best_node_cost)
        else:
            # recalculate minimal_vs_list and try again
            recalculated_minimal_vs_list = self.calculate_minimal_vs_list(game_state)
            new_gs = Game_State(
                num_queries_this_round=0,
                proposal_used_this_round=None,
                fset_cwa_indexes_remaining=game_state.fset_cwa_indexes_remaining
            )
            answer = self.nightmare_calculate_best_move(
                qs_dict=qs_dict,
                game_state=new_gs,
                minimal_vs_list=recalculated_minimal_vs_list
            )
        self.evaluations_cache[game_state] = answer
        return(answer)

    def solve(self):
        """
        Sets up evaluations_cache with the evaluations of all necessary game states.
        """
        start = time.time()
        self.calculator(qs_dict = self.qs_dict, game_state = self.initial_game_state)
        end = time.time()
        self.seconds_to_solve = int(end - start)

    def full_cwa_from_game_state(self, gs):
        return([self.rc_indexes_cwa_to_full_combos_dict[cwa] for cwa in gs.fset_cwa_indexes_remaining])
