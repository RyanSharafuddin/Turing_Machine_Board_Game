import math
import display, rules
from definitions import *

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

def make_rc_infos(num_rcs, possible_combos_with_answers):
    """ O(n) in length of possible_combos_with_answers """
    rc_infos = [dict() for _ in range(num_rcs)]
    for (c, a) in possible_combos_with_answers:
        for (rc_index, rule) in enumerate(c):
            rc_info_dict = rc_infos[rc_index]
            if(rule.card_index in rc_info_dict):
                this_rule_s_inner_dict = rc_info_dict[rule.card_index]
                if(a) in this_rule_s_inner_dict:
                    this_rule_s_inner_dict[a].append(c)
                else:
                    this_rule_s_inner_dict[a] = [c]
            else:
                rc_info_dict[rule.card_index] = {a: [c]}
    return(rc_infos)

def get_unsolved_rules_card_indices(rc_infos):
    unsolved_rc_indices = [rc_index for (rc_index, rc_info) in enumerate(rc_infos) if(len(rc_info) > 1)]
    return(unsolved_rc_indices)

def populate_useful_qs_dict(rcs_list, all_125_possibilities_set, possible_combos_with_answers):
    useful_queries_dict = dict()
    rc_infos = make_rc_infos(len(rcs_list), possible_combos_with_answers)
    (possible_combos, possible_answers) = zip(*possible_combos_with_answers)
    set_possible_answers = frozenset(possible_answers)
    current_num_possible_combos = len(possible_combos)
    current_num_possible_answers = len(set_possible_answers)
    for unsolved_card_index in get_unsolved_rules_card_indices(rc_infos):
        corresponding_rc = rcs_list[unsolved_card_index]
        corresponding_rc_info = rc_infos[unsolved_card_index]
        possible_rules_this_card = [
            corresponding_rc[possible_rule_index] for possible_rule_index in corresponding_rc_info.keys()
        ]
        for possible_query in all_125_possibilities_set:
            possible_accepting_rules_card_indices = set()
            possible_rejecting_rules_card_indices = set()
            for possible_rule in possible_rules_this_card:
                if(possible_query in possible_rule.reject_set):
                    possible_rejecting_rules_card_indices.add(possible_rule.card_index)
                else:
                    possible_accepting_rules_card_indices.add(possible_rule.card_index)
            if(
                bool(possible_accepting_rules_card_indices) and
                bool(possible_rejecting_rules_card_indices)
            ):
                # TODO: make both of the below sets right off the bat if you're going to make new useful queries dicts while solving the problem. And make them the set of (card_indices_combo, answer) immediately; don't waste time with anything unnecessary, like appending to any lists of full combos or calculating expected info gain. And get rid of the set_answers remaining (NOT the set_cwa_remaining)
                possible_combos_with_answers_remaining_if_true = []
                possible_combos_with_answers_remaining_if_false = []
                for combo_with_answer in possible_combos_with_answers:
                    (possible_combo, possible_answer) = combo_with_answer
                    if (possible_combo[unsolved_card_index].card_index in possible_accepting_rules_card_indices):
                        possible_combos_with_answers_remaining_if_true.append(combo_with_answer)
                    elif(possible_combo[unsolved_card_index].card_index in possible_rejecting_rules_card_indices):
                        possible_combos_with_answers_remaining_if_false.append(combo_with_answer)
                    else:
                        print("Teh program is broken if this happens")
                        exit()

                (combos_remaining_if_true, answers_remaining_if_true) = zip(*possible_combos_with_answers_remaining_if_true)
                # WARN: do not use set_answers_remaining... unless you plan to recalculate q_infos every query.
                set_answers_remaining_if_true = set(answers_remaining_if_true)
                num_combos_remaining_if_true = len(combos_remaining_if_true)
                num_answers_remaining_if_true = len(set_answers_remaining_if_true)

                (combos_remaining_if_false, answers_remaining_if_false) = zip(*possible_combos_with_answers_remaining_if_false)
                # WARN: see warning above
                set_answers_remaining_if_false = set(answers_remaining_if_false)
                num_combos_remaining_if_false = len(combos_remaining_if_false)
                num_answers_remaining_if_false = len(set_answers_remaining_if_false)
                if((num_combos_remaining_if_true + num_combos_remaining_if_false) != current_num_possible_combos):
                    raise Exception("FAIL")

                # NOTE: It's okay if the number of answers remaining when true and when false don't add up to the number of answers currently, because it's not the case that every answer remains only when true or only when false. Every *combo* remains only when true or only when false, but sometimes one answer can have multiple combos, so it it remains when the query is true and when it's false. To see an example of this, uncomment the block below and try on problem [9, 22, 24, 31, 37, 40] ("C63 0YV B" online).
                # if((num_answers_remaining_if_true + num_answers_remaining_if_false) != current_num_possible_answers):
                #     print(f"Failed when considering query: {possible_query} on card {string.ascii_uppercase[unsolved_card_index]}")
                #     display.print_all_possible_answers("Combos remaining if true:", set_answers_remaining_if_true, possible_combos_with_answers_remaining_if_true)
                #     display.print_all_possible_answers("Combos remaining if false:", set_answers_remaining_if_false, possible_combos_with_answers_remaining_if_false)
                #     exit()

                p_true = num_combos_remaining_if_true / current_num_possible_combos
                answer_info_gain_true = math.log2(
                    current_num_possible_answers / num_answers_remaining_if_true
                )
                combo_info_gain_true = math.log2(
                    current_num_possible_combos / num_combos_remaining_if_true
                )
                p_false = num_combos_remaining_if_false / current_num_possible_combos
                answer_info_gain_false = math.log2(
                    current_num_possible_answers / num_answers_remaining_if_false
                )
                combo_info_gain_false = math.log2(
                    current_num_possible_combos / num_combos_remaining_if_false
                )
                expected_answer_info_gain = (
                    (p_true * answer_info_gain_true) + (p_false * answer_info_gain_false)
                )
                expected_combo_info_gain = (
                    (p_true * combo_info_gain_true) + (p_false * combo_info_gain_false)
                )
                query_info = Query_Info(
                    possible_combos_with_answers_remaining_if_true,
                    possible_combos_with_answers_remaining_if_false,
                    p_true,
                    answer_info_gain_true,
                    answer_info_gain_false,
                    expected_answer_info_gain,
                    expected_combo_info_gain,
                    set(
                        [
                            (tuple([r.card_index for r in cwa[0]]), cwa[1]) for cwa in
                            possible_combos_with_answers_remaining_if_true
                        ]
                    ),
                    set(
                        [
                            (tuple([r.card_index for r in cwa[0]]), cwa[1]) for cwa in
                            possible_combos_with_answers_remaining_if_false
                        ]
                    )
                )
                if(possible_query in useful_queries_dict):
                    inner_dict = useful_queries_dict[possible_query]
                    if(unsolved_card_index in inner_dict):
                        print("This shouldn't happen, because you're going over every card/every possible query to that card only once.")
                        exit()
                    else:
                        inner_dict[unsolved_card_index] = query_info
                else:
                    useful_queries_dict[possible_query] = {
                        unsolved_card_index: query_info
                    }
    return(useful_queries_dict)

def fset_answers_from_cwa_iterable(cwa_iterable):
    return(frozenset([cwa[1] for cwa in cwa_iterable]))

def create_move_info(num_combos_currently, game_state, num_queries_this_round, q_info, move, cost):
    """
    num_queries_this_round is the number there will be after making this move.
    WARN: could be None
    """
    fset_indexes_cwa_remaining_true = game_state.fset_cwa_indexes_remaining & q_info.set_indexes_cwa_remaining_true
    fset_indexes_cwa_remaining_false = game_state.fset_cwa_indexes_remaining & q_info.set_indexes_cwa_remaining_false
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

# see get_moves docstring for definitions of move and cost.
# NOTE: do I actually need current_round_num or total_queries_made parameters in args to below? Yes, for pruning purposes. Or is it? See todo item about pruning.
def calculate_best_move(
        qs_dict,
        game_state,
        previous_best,         # NOTE: not used currently
        current_round_num,     # NOTE: not used currently
        total_queries_made,    # NOTE: not used currently
        evaluations_cache
    ):
    """
    Returns a tuple (best move in this state, mov_cost_tup, gs_tup, expected cost to win from game_state (this is a tuple of (expected rounds, expected total queries))).
    best_move_tup is a tup of (proposal, rc_index)
    """
    if(game_state in evaluations_cache):
        return(evaluations_cache[game_state])
    if(len(fset_answers_from_cwa_iterable(game_state.fset_cwa_indexes_remaining)) == 1):
        # don't bother filling up the cache with already-won states.
        return( (None, None, None, (0,0)) )
    best_expected_cost_tup = (float('inf'), float('inf'))
    for move_info in get_and_apply_moves(game_state, qs_dict):
        (move, mcost, gs_tup, p_tup) = move_info
        gs_false_expected_cost = calculate_best_move(
            qs_dict,
            gs_tup[0],
            previous_best,
            current_round_num + mcost[0],
            total_queries_made + 1,
            evaluations_cache=evaluations_cache
        )[3]
        gs_true_expected_cost = calculate_best_move(
            qs_dict,
            gs_tup[1],
            previous_best,
            current_round_num + mcost[0],
            total_queries_made + 1,
            evaluations_cache=evaluations_cache
        )[3]
        gss_costs = (gs_false_expected_cost, gs_true_expected_cost)
        expected_cost_tup = calculate_expected_cost(mcost, p_tup, gss_costs)
        if(expected_cost_tup < best_expected_cost_tup):
            best_expected_cost_tup = expected_cost_tup
            best_move_tup = move
            best_mov_cost_tup = mcost
            best_gs_tup = gs_tup
    answer = (best_move_tup, best_mov_cost_tup, best_gs_tup, best_expected_cost_tup)
    evaluations_cache[game_state] = answer
    return(answer)

def calculate_expected_cost(mcost, probs, gss_costs):
    (mcost_rounds, mcost_queries) = mcost
    (p_false, p_true) = probs
    ((gs_false_round_cost, gs_false_query_cost), (gs_true_round_cost, gs_true_query_cost)) = gss_costs
    expected_r_cost = mcost_rounds + (p_false * gs_false_round_cost) + (p_true * gs_true_round_cost)
    expected_q_cost = mcost_queries + (p_false * gs_false_query_cost) + (p_true * gs_true_query_cost)
    return((expected_r_cost, expected_q_cost))

def solve(rules_cards_nums_list):
    """
    rules_card_nums_list is a list of the names (numbers) of the rules cards in this problem. Solve will print out which queries to perform, and (TBD) either print out what to do in all possible cases, or ask for the answers of the queries and proceed from there.
    """
    # globals for debugging purposes
    global rc_indexes_cwa_to_full_combos_dict # TODO: remove the global modifier on this after debug
    global initial_game_state
    global evaluations_cache

    # TODO: change below for extreme mode. Will also need to change the card_index of each rules in a rules card in extreme mode, since each card is now a combo of 2 cards.
    rcs_list = [rules.rcs_deck[num] for num in rules_cards_nums_list]
    possible_combos_with_answers = get_possible_rules_combos_with_answers(rcs_list)
    if(not(possible_combos_with_answers)):
        display.print_problem(rcs_list)
        print("User error: you have entered a problem which has no valid solutions. Exiting.")
        exit()
    fset_cwa_indexes_remaining = frozenset(
        [(tuple([r.card_index for r in cwa[0]]), cwa[1]) for cwa in possible_combos_with_answers]
    )
    rc_indexes_cwa_to_full_combos_dict = {}
    for cwa in possible_combos_with_answers:
        rc_indexes_cwa_to_full_combos_dict[(tuple([r.card_index for r in cwa[0]]), cwa[1])] = cwa
    fset_possible_answers = fset_answers_from_cwa_iterable(possible_combos_with_answers)

    evaluations_cache = None
    initial_game_state = Game_State(0, None, fset_cwa_indexes_remaining)
    if(len(fset_possible_answers) > 1):
        qs_dict = populate_useful_qs_dict(rcs_list, all_125_possibilities_set, possible_combos_with_answers)
        evaluations_cache = dict()
        calculate_best_move(
            qs_dict = qs_dict,
            game_state = initial_game_state,
            previous_best = float('inf'),
            current_round_num = 0,
            total_queries_made = 0,
            evaluations_cache = evaluations_cache
        )
    return((rcs_list, evaluations_cache, initial_game_state))

def full_cwa_from_game_state(gs):
    return([rc_indexes_cwa_to_full_combos_dict[cwa] for cwa in gs.fset_cwa_indexes_remaining])

def update_query_history(q_history, move, new_round: bool, result: bool):
    if(new_round):
        q_history.append([move[0]])
    q_history[-1].append((move[1], result))
    if(move[0] != q_history[-1][0]):
        print("ERROR! The current move's proposal does not match up with the proposal used this round, and so this should have been a new round, but it isn't.")
        exit()

def play(rc_nums_list):
    (rcs_list, evaluations_cache, initial_game_state) = solve(rc_nums_list)
    current_gs = initial_game_state
    # NOTE: below line for display purposes only
    rules.max_rule_name_length = max([max([len(r.name) for r in rc]) for rc in rcs_list])
    display.print_problem(rcs_list, active=True)
    possible_combos_with_answers = full_cwa_from_game_state(current_gs)
    display.print_all_possible_answers("\nAll possible answers:", possible_combos_with_answers)
    current_round_num = 0
    total_queries_made = 0
    query_history = [] # each round is: [proposal, (verifier, result), . . .]
    while(len(fset_answers_from_cwa_iterable(current_gs.fset_cwa_indexes_remaining)) > 1):
        (best_move_tup, mcost_tup, gs_tup, expected_cost_tup) = evaluations_cache[current_gs]
        possible_combos_with_answers = full_cwa_from_game_state(current_gs)
        expected_winning_round = current_round_num + expected_cost_tup[0]
        expected_total_queries = total_queries_made + expected_cost_tup[1]
        # display.print_list_cwa(possible_combos_with_answers, "\nRemaining Combos:", use_round_indent=True)
        current_round_num += mcost_tup[0]
        total_queries_made += mcost_tup[1]
        query_this_round = 1 if (mcost_tup[0]) else current_gs.num_queries_this_round + 1
        display.display_query_num_info(current_round_num, query_this_round, total_queries_made, mcost_tup[0], best_move_tup[0])
        result = display.conduct_query(
            best_move_tup,
            expected_winning_round,
            expected_total_queries,
        )
        current_gs = gs_tup[result]
        update_query_history(query_history, best_move_tup, mcost_tup[0], result)
    # Found an answer
    possible_combos_with_answers = full_cwa_from_game_state(current_gs)
    print(f"\nFinal Score: Rounds: {current_round_num}. Queries: {total_queries_made}.")
    display.display_query_history(query_history, len(rc_nums_list))
    display.print_final_answer("\nANSWER: ", possible_combos_with_answers)
    # TODO: delete below 2 after convert all answers to ints instead of tuples.
    for r in query_history:
        print(r)

# DEBUG_MODE = False
# play([2, 5, 9, 15, 18, 22])   # ID: B63 YRW 4. Takes 0 queries to solve.
# play([4, 9, 11, 14])          # ID:         1.
# play([3, 7, 10, 14])          # ID:         2. FTF 435.
solve([3, 7, 10, 14])         # ID:         2. FOR PROFILING
# play([9, 22, 24, 31, 37, 40]) # ID: C63 0YV B. Interesting b/c multiple combos lead to same answer here. T 351
