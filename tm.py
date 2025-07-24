import math
import display
import rules
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

def make_rc_infos(num_rules_cards, possible_combos_with_answers):
    rc_infos = [dict() for _ in range(num_rules_cards)]
    for combo_with_answer in possible_combos_with_answers:
        (possible_combo, possible_answer) = combo_with_answer
        for (rule_card_index, rule) in enumerate(possible_combo):
            rules_card_info_dict = rc_infos[rule_card_index]
            answer_within_this_card_index = rule.card_index
            if(answer_within_this_card_index in rules_card_info_dict):
                this_rule_s_inner_dict = rules_card_info_dict[answer_within_this_card_index]
                if(possible_answer) in this_rule_s_inner_dict:
                    this_rule_s_inner_dict[possible_answer].append(possible_combo)
                else:
                    this_rule_s_inner_dict[possible_answer] = [possible_combo]
            else:
                rules_card_info_dict[answer_within_this_card_index] = {possible_answer: [possible_combo]}
    return(rc_infos)

def get_unsolved_rules_card_indices(rules_card_infos):
    unsolved_rules_card_indices_within_rules_cards_list = []
    for (rc_index, rc_info) in enumerate(rules_card_infos):
        if(len(rc_info) > 1): # if there are multiple rules this card could be
            unique_answers_this_rc = set()
            for inner_dict in rc_info.values():
                for possibility in inner_dict.keys():
                    unique_answers_this_rc.add(possibility)
            if(len(unique_answers_this_rc) == 1):
                print(f"For rules card {rc_index}, all possibilities for this card lead to the same answer, which means this problem should already be solved.")
                exit()
            elif(len(unique_answers_this_rc) > 1):
                unsolved_rules_card_indices_within_rules_cards_list.append(rc_index)
            else:
                print("Your program is broken, b/c this rules card has no possible answers.")
                exit()
    return(unsolved_rules_card_indices_within_rules_cards_list)

def populate_useful_qs_dict(
        unsolved_rules_card_indices_within_rules_cards_list,
        rules_cards_list,
        rc_infos,
        all_125_possibilities_set,
        possible_combos_with_answers,
        possible_combos,
        set_possible_answers,
    ):
    useful_queries_dict = dict()
    current_num_possible_combos = len(possible_combos)
    current_num_possible_answers = len(set_possible_answers)
    for unsolved_card_index in unsolved_rules_card_indices_within_rules_cards_list:
        corresponding_rc = rules_cards_list[unsolved_card_index]
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
                #     print(f"Failed when considering query: {display.answer_tup_to_string(possible_query)} on card {string.ascii_uppercase[unsolved_card_index]}")
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
                        map(
                            lambda cwa: (tuple([r.card_index for r in cwa[0]]), cwa[1]),
                            possible_combos_with_answers_remaining_if_true
                        )
                    ),
                    set(
                        map(
                            lambda cwa: (tuple([r.card_index for r in cwa[0]]), cwa[1]),
                            possible_combos_with_answers_remaining_if_false
                        )
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

def fset_answers_from_fset_cwa(fset_cwa):
    return(frozenset([cwa[1] for cwa in fset_cwa]))

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
        # if the num queries is 3, then any next query starts a new round, and game_state's proposal_used_this_round is not read. Important to set to None to help cache.
        proposal_used_this_round = None if(num_queries_this_round == 3) else move[0]
        game_state_false = Game_State(
            num_queries_this_round = num_queries_this_round,
            proposal_used_this_round = proposal_used_this_round,
            fset_cwa_indexes_remaining = fset_indexes_cwa_remaining_false,
            fset_answers_remaining = fset_answers_from_fset_cwa(fset_indexes_cwa_remaining_false)
        )
        game_state_true = Game_State(
            num_queries_this_round = num_queries_this_round,
            proposal_used_this_round = proposal_used_this_round,
            fset_cwa_indexes_remaining = fset_indexes_cwa_remaining_true,
            fset_answers_remaining = fset_answers_from_fset_cwa(fset_indexes_cwa_remaining_true)
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
    game_states are copied, not mutated.
    """
    # NOTE: don't forget to set proposal_used_this_round
    # NOTE: if taking too much time, may want to copy qs_dict and remove queries/rcs that are no longer useful, and pass them along as part of game_state. But then there'd be the problem that dicionaries aren't hashable . . . Could consider instead maintaining a frozenset of (proposal, rc_index) for those proposal rc_index pairs that are still useful, and when creating a new game_state for next function call, copying it over into a new frozenset, except without the pairs that are no longer useful. Maybe do profiling first though to see if this is what is consuming time.
    num_combos_currently = len(game_state.fset_cwa_indexes_remaining)
    if((game_state.num_queries_this_round == 3) or (game_state.num_queries_this_round == 0)):
        # does not continue from previous query. All queries this move are new round.
        cost = (1, 1) if (game_state.num_queries_this_round == 3) else (0, 1)
        for (proposal, inner_dict) in qs_dict.items():
            for (rc_index, q_info) in inner_dict.items():
                move = (proposal, rc_index)
                move_info = create_move_info(num_combos_currently, game_state, 1, q_info, move, cost)
                if(not(move_info is None)):
                    yield(move_info)
                else:
                    # proposal to rc_index is not a useful query. Consider eliminating it from game_state, if you start passing around fsets for this info as in above note. See comment in create_move_info.
                    pass
    else:
        # does continue from previous query; new proposals cost a round
        if(game_state.proposal_used_this_round is None):
            print("FAIL")
            exit()
        cost = (0, 1) # considering all queries with this round's proposal first, then new proposals.
        inner_dict_this_proposal = qs_dict.get(game_state.proposal_used_this_round)
        if(not(inner_dict_this_proposal is None)):
            num_queries_this_round = game_state.num_queries_this_round + 1
            for (rc_index, q_info) in inner_dict_this_proposal.items():
                move = (game_state.proposal_used_this_round, rc_index)
                move_info = create_move_info(num_combos_currently, game_state, num_queries_this_round, q_info, move, cost)
                if(not(move_info is None)):
                    yield(move_info)
                else:
                    pass # not a useful query. See other comments.
        # after trying all the moves that continue with the same query this round, try ending the round early.
        cost = (1, 1)
        num_queries_this_round = 1
        for (proposal, inner_dict) in qs_dict.items():
            if(proposal == game_state.proposal_used_this_round):
                continue # no sense starting a new round when you could have remained on same round.
            for (rc_index, q_info) in inner_dict.items():
                move = (proposal, rc_index)
                move_info = create_move_info(num_combos_currently, game_state, num_queries_this_round, q_info, move, cost)
                if(not(move_info is None)):
                    yield(move_info)
                else:
                    pass  # not a useful query

# see get_moves docstring for definitions of move and cost.
# NOTE: do I actually need current_round_num or total_queries_made parameters in args to below? Yes, for pruning purposes. Or is it? B/c even if cost is high, probability could be low? But you know the probabilities. Think about it later. Then previous_best is a tuple of (expected_round_num_solved, expected_total_queries?) Consider making these two args a tuple for easy comparison.
# WARN: copy game state, no mutate
def calculate_best_move(
        qs_dict,
        game_state,
        previous_best,
        current_round_num,
        total_queries_made,
        evaluations_cache # a dict of {game_state: (best_move_tup, best_mov_cost_tup, best_gs_tup, expected_cost_tup)} NOTE: might consider offloading this to Python's decorator for LRU cache rather than doing it manually and never evicting anything.
    ):
    """
    Returns a tuple (best move in this state, mov_cost_tup, gs_tup, expected cost to win from game_state (this is a tuple of (expected rounds, expected total queries))).
    best_move_tup is a tup of (proposal, rc_index)
    # TODO: delete the mov_history, as it was only used for debugging.
    """
    if(game_state in evaluations_cache):
        return(evaluations_cache[game_state])
    (expected_round_cost, expected_queries_cost) = (0, 0)
    if(len(game_state.fset_answers_remaining) == 1):
        # don't bother filling up the cache with already-solved states.
        return( (None, None, None, (0,0)) )
    # print(f"\ncurrent round: {current_round_num}. total_queries: {total_queries_made}.")
    # print(f"Move history: {mov_history}")
    # print_game_state(game_state)
    best_expected_cost_tup = (float('inf'), float('inf'))
    for move_info in get_and_apply_moves(game_state, qs_dict):
        (move, mov_cost_tup, gs_tup, p_tup) = move_info
        (p_false, p_true) = p_tup
        (_, _, _, gs_false_expected_cost_to_win) = calculate_best_move(
            qs_dict,
            gs_tup[0],
            previous_best, # NOTE: not actually used yet.
            current_round_num + mov_cost_tup[0], # NOTE: correct value, but not used yet.
            total_queries_made + 1, # NOTE: not used yet. To use, add in a move's cost to these values, compare to previous best, and if worse, abandon this branch. For previous best, update it with each new answer you get (after multiplying by probs and adding), and start it at +infinity.
            evaluations_cache=evaluations_cache
            # mov_history + [f'{display.answer_tup_to_string(move_info[0][0])} to verifier {string.ascii_uppercase[move_info[0][1]]}. False']
        )
        (_, _, _, gs_true_expected_cost_to_win) = calculate_best_move(
            qs_dict,
            gs_tup[1],
            previous_best, # NOTE: not actually used yet.
            current_round_num + mov_cost_tup[0], # NOTE: correct value, but not used yet.
            total_queries_made + 1, # all moves cost 1 query
            evaluations_cache=evaluations_cache
            # mov_history + [f'{display.answer_tup_to_string(move_info[0][0])} to verifier {string.ascii_uppercase[move_info[0][1]]}. True.']
        )
        (mov_round_cost, mov_query_cost) = mov_cost_tup
        expected_round_cost = mov_round_cost + (p_false * gs_false_expected_cost_to_win[0]) + (p_true * gs_true_expected_cost_to_win[0])
        expected_query_cost = mov_query_cost + (p_false * gs_false_expected_cost_to_win[1]) + (p_true * gs_true_expected_cost_to_win[1])
        expected_cost_tup = (expected_round_cost, expected_query_cost)
        if(expected_cost_tup < best_expected_cost_tup):
            best_expected_cost_tup = expected_cost_tup
            best_move_tup = move
            best_mov_cost_tup = mov_cost_tup
            best_gs_tup = gs_tup
    answer = (best_move_tup, best_mov_cost_tup, best_gs_tup, best_expected_cost_tup)
    evaluations_cache[game_state] = answer
    return(answer)

# TODO: have the program handle standard mode before it handles nightmare mode.
# a problem is a list of rules cards.
def solve(rules_cards_nums_list):
    """
    rules_card_nums_list is a list of the names (numbers) of the rules cards in this problem. Solve will print out which queries to perform, and (TBD) either print out what to do in all possible cases, or ask for the answers of the queries and proceed from there.
    """
    # globals for debugging purposes
    global rc_indexes_cwa_to_full_combos_dict # TODO: remove the global modifier on this after debug
    global initial_game_state
    global evaluations_cache

    num_rules_cards = len(rules_cards_nums_list)
    # TODO: change below for extreme mode. Will also need to change the card_index of each rules in a rules card in extreme mode, since each card is now a combo of 2 cards.
    rcs_list = [rules.rcs_deck[num] for num in rules_cards_nums_list]
    # NOTE: below line for display purposes only
    rules.max_rule_name_length = max([max([len(r.name) for r in rc]) for rc in rcs_list])
    possible_combos_with_answers = get_possible_rules_combos_with_answers(rcs_list)
    rc_indexes_cwa_to_full_combos_dict = {}
    for cwa in possible_combos_with_answers:
        rc_indexes_cwa_to_full_combos_dict[(tuple([r.card_index for r in cwa[0]]), cwa[1])] = cwa
    (possible_combos, possible_answers) = zip(*possible_combos_with_answers)
    set_possible_answers = set(possible_answers)
    display.print_problem(rcs_list, active=True)
    display.print_all_possible_answers("\nAll possible answers:", possible_combos_with_answers)

    # Note: may not need this block below.
    # number_possible_combos = len(possible_combos)
    # num_unique_possible_answers = len(set_possible_answers)
    # if(num_unique_possible_answers != number_possible_combos):
        # print("NOTE: There are different possible rules combos that give rise to the same answer. Perhaps you can exploit this to solve for the answer without also needing to solve for which rules combo gives rise to the answer? Consider it.")
        # exit()

    # All non-constant variables that need to be set correctly at beginning of each loop:
    # possible_combos_with_answers (remove ruled out possibilities)
    # possible_combos and possible_answers (make from possible_combos_with answers using zip)
    # set_possible_answers (make from possible_answers)

    current_round_num = 1
    total_queries_made = 0
    if(len(set_possible_answers) > 1):
        # see definitions.py for documentation on what exactly rc_infos is
        rc_infos = make_rc_infos(num_rules_cards, possible_combos_with_answers)
        unsolved_rules_card_indices_within_rules_cards_list = get_unsolved_rules_card_indices(rc_infos)

        useful_queries_dict = populate_useful_qs_dict(
            unsolved_rules_card_indices_within_rules_cards_list,
            rcs_list,
            rc_infos,
            all_125_possibilities_set,
            possible_combos_with_answers,
            possible_combos,
            set_possible_answers,
        )
        fset_cwa_indexes_remaining = frozenset(
            [(tuple([r.card_index for r in cwa[0]]), cwa[1]) for cwa in possible_combos_with_answers]
        )
        evaluations_cache = dict()
        initial_game_state = Game_State(0, None, fset_cwa_indexes_remaining, frozenset(set_possible_answers))
        current_game_state = initial_game_state

    while(len(set_possible_answers) > 1):
        (best_move_tup, mcost_tup, gs_tup, expected_cost_tup) = calculate_best_move(
            qs_dict=useful_queries_dict,
            game_state=current_game_state,
            previous_best=float('inf'),
            current_round_num=current_round_num,
            total_queries_made=total_queries_made,
            evaluations_cache=evaluations_cache
        )
        if(DEBUG_MODE):
            return
        # display.print_list_cwa(possible_combos_with_answers, "\nRemaining Combos:")
        # TODO: print out queries used this round/overall.
        print(f"\nCurrent round number: {current_round_num}. Total queries made: {total_queries_made}.")
        result = display.conduct_query(
            best_move_tup,
            current_round_num,
            total_queries_made,
            expected_cost_tup
        )
        current_game_state = gs_tup[result]
        current_round_num = current_round_num + mcost_tup[0]
        total_queries_made += mcost_tup[1]
        set_possible_answers = current_game_state.fset_answers_remaining
        possible_combos_with_answers = [
            rc_indexes_cwa_to_full_combos_dict[cwa] for cwa in
            current_game_state.fset_cwa_indexes_remaining
        ]
        # query loop end
    # Found an answer
    # TODO: print out queries used this round. Also print out the query table from the notepad in physical game.
    print(f"\nCurrent round number: {current_round_num}. Total queries made: {total_queries_made}.")
    display.print_final_answer("\nANSWER: ", possible_combos_with_answers)

DEBUG_MODE = True
# corresponds to zero_query_problem.png. Can be solved without making any queries. Problem ID: "B63 YRW 4".
# solve([2, 5, 9, 15, 18, 22])
# solve([4, 9, 11, 14]) # problem 1 in the book
solve([3, 7, 10, 14]) # problem 2 in the book. FTF 435. Try answering false false for debug purposes.
# solve([9, 22, 24, 31, 37, 40]) # "C63 0YV B". Interesting b/c multiple combos lead to same answer here. T 351
