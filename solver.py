import math, itertools, time
import rules
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
            for (rc_index, q_info) in inner_dict_this_proposal.items():
                move = (game_state.proposal_used_this_round, rc_index)
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
        for (rc_index, q_info) in inner_dict.items():
            move = (proposal, rc_index)
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
    def __init__(self, problem):
        self.problem            = problem
        self.evaluations_cache  = dict()
        self.rcs_list           = rules.make_rcs_list(problem)
        self.flat_rule_list     = rules.make_flat_rule_list(self.rcs_list)
        self.full_cwa           = make_full_cwa(problem, self.rcs_list)
        self.initial_game_state = Game_State(0, None, fset_cwa_indexes_remaining_from_full_cwa(self.full_cwa))
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

    # see get_moves docstring for definitions of move and cost.
    # NOTE: don't use the class's qs_dict just yet. Keep passing it down, in case you want to make new ones in the future. See todo.txt.
    def calculate_best_move(self, qs_dict, game_state):
        """
        Returns a tuple (best move in this state, mov_cost_tup, gs_tup, expected cost to win from game_state (this is a tuple of (expected rounds, expected total queries))).
        best_move_tup is a tup of (proposal, rc_index)
        """
        if(game_state in self.evaluations_cache):
            return(self.evaluations_cache[game_state])
        # TODO: consider replacing with a function (outside the class) called one_answer_left(cwa_indexes_remaining) that merely returns a boolean for whether there's exactly one answer left. May save time over making an entire set, b/c can stop once encounter the first repeat. Can use line profiler to see if this change saves you time. Maybe use numpy arrays and see if that provides any speedup? i.e. each cwa_indexes remaining is just a numpy array of booleans of length (len(full_cwa)), and the boolean at index i is true if the ith cwa is still there, and false otherwise, and can then use np.and to intersect sets and np.count (or something) to see if there's one left? Profile and see if this saves time.
        if(len(fset_answers_from_cwa_iterable(game_state.fset_cwa_indexes_remaining)) == 1):
            # don't bother filling up the cache with already-won states.
            return( (None, None, None, (0,0)) )
        best_expected_cost = (float('inf'), float('inf'))
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
            gs_false_expected_cost = self.calculate_best_move(qs_dict, gs_tup[0])[3]
            gs_true_expected_cost = self.calculate_best_move(qs_dict, gs_tup[1])[3]
            gss_costs = (gs_false_expected_cost, gs_true_expected_cost)
            expected_cost_tup = calculate_expected_cost(mcost, p_tup, gss_costs)
            if(expected_cost_tup < best_expected_cost):
                if(expected_cost_tup[0] == 0):
                    found_zero_more_round_sol = True
                best_expected_cost = expected_cost_tup
                best_move = move
                best_mov_cost = mcost
                best_gs_tup = gs_tup
                if((expected_cost_tup == (0, 1)) or ((expected_cost_tup == (1, 1)) and game_state.proposal_used_this_round is None)): # can solve within 1 query and 0 rounds, or 1 query and all queries cost a round, so return early
                    break
        answer = (best_move, best_mov_cost, best_gs_tup, best_expected_cost)
        self.evaluations_cache[game_state] = answer
        return(answer)

    def solve(self):
        """
        Sets up evaluations_cache with the evaluations of all necessary game states.
        """
        start = time.time()
        self.calculate_best_move(qs_dict = self.qs_dict, game_state = self.initial_game_state)
        end = time.time()
        self.seconds_to_solve = int(end - start)

    def full_cwa_from_game_state(self, gs):
        return([self.rc_indexes_cwa_to_full_combos_dict[cwa] for cwa in gs.fset_cwa_indexes_remaining])
