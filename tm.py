import math, string, copy
from collections import namedtuple
from rules import *

possibilities = []
def get_digit(n, index, base=10):
    """
    Given a nonnegative integer n and an index, get the digit at that index of n. For example, if n is 3289, and index is 0, will return 9. index 1 will return 8. index 2 will return 2. Can optionally choose a base other than 10.
    """
    n = n // (base ** index)
    return (n % base)

for n in range(125):
    ones_place = get_digit(n, 0, 5)
    fives_place = get_digit(n, 1, 5)
    twenty_fives_place = get_digit(n, 2, 5)
    final_tup = (twenty_fives_place + 1, fives_place + 1, ones_place + 1)
    # print(final_tup) # uncomment to see what each possibility looks like.
    possibilities.append(final_tup)

all_125_possibilities_set = set(possibilities)
#NOTE: each possibility in the possibilities list is a tuple of the 3 digits. i.e. the answer
#      524 is represented as the tuple (5, 2, 4), with tuple[0] being the most significant digit.

Rule = namedtuple('Rule', ['name', 'reject_set', 'func', 'card_index'])
# card_index is the rule's index within the list that is the card. (i.e. 0th rule, 1st rule, 2nd rule, etc.)
def func_to_Rule(func, card_index):
    reject_set = {p for p in all_125_possibilities_set if not(func(*p))}
    return(Rule(func.__name__, reject_set, func, card_index))

for (rule_card_num, rule_card) in rcs_deck.items():
    rcs_deck[rule_card_num] = [func_to_Rule(f, i) for (i, f) in enumerate(rule_card)]
    # now rules_cards is a dict from rule_card_num to a list of Rules, where each rule consists of a name, reject_set, Python function, and index within its card

def is_combo_possible(combo):
    """
    Given a list of Rules, returns a tuple (a, b).
    a is either True or False, representing whether the combo is possible according to the 2 rules that:
    1) There must be exactly one possible answer.
    2) Each verifier eliminates at least one possibility that is not eliminated by any other verifier.
    if a is False, b is None. if a is True, b is the one tuple possibility that satisfies all rules.
    """
    reject_sets = [rule.reject_set for rule in combo]
    reject_sets_unions = set.union(*reject_sets)
    if(len(reject_sets_unions) != (len(all_125_possibilities_set) - 1)):
        return((False, None))
    answer = (all_125_possibilities_set - reject_sets_unions).pop()
    for (i, reject_set) in enumerate(reject_sets):
        all_other_reject_sets = reject_sets[0 : i] + reject_sets[i + 1 :]
        other_reject_sets_union = set.union(*all_other_reject_sets)
        if(not(reject_set - other_reject_sets_union)):
            return((False, None)) # means that this rule is redundant.
    return((True, answer))

def get_all_rules_combinations(rules_cards_list):
    """ Returns all possible combinations of rules, whether possible or not. """
    num_rules_cards = len(rules_cards_list)
    rules_cards_lengths = [len(rules_card) for rules_card in rules_cards_list]
    total_num_combinations = math.prod(rules_cards_lengths)
    rules_combos = []
    for combo_num in range(total_num_combinations):
        new_combo = [
            rules_cards_list[rules_card_index][
                (combo_num // math.prod(rules_cards_lengths[rules_card_index + 1:])) % rules_cards_lengths[rules_card_index]
            ]
            for rules_card_index in range(num_rules_cards)
        ]
        rules_combos.append(new_combo)
    # print all combos, possible or not.
    # for (combo_num, combo) in enumerate(rules_combos, start=1):
    #     print(f'{combo_num}: {[rule.name for rule in combo]}')
    return(rules_combos)

def get_possible_rules_combos_with_answers(rules_cards_list):
    all_rules_combos = get_all_rules_combinations(rules_cards_list)
    possible_combos_with_answers = [] # tuples of ([rules_list], answer_tuple)
    for combo in all_rules_combos:
        (possible, answer) = is_combo_possible(combo)
        if(possible):
            possible_combos_with_answers.append((combo, answer))
    return(possible_combos_with_answers)

def make_rc_infos(num_rules_cards, possible_combos_with_answers):
    rc_infos = [dict() for _ in range(num_rules_cards)]
    print("\nRemaining Combos:")
    for (combo_with_answer_index, combo_with_answer) in enumerate(sorted(possible_combos_with_answers, key=lambda t:t[1])):
        (possible_combo, possible_answer) = combo_with_answer
        print_combo_with_answer(combo_with_answer_index, combo_with_answer)
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
    # print internal info
    # print()
    for (rc_index, rc_info) in enumerate(rules_card_infos):
        # print(f'rules card {rc_index}:' + ' {')
        # for (rule_index_within_card, inner_dict) in rc_info.items():
            # print(f'    possible rule index: {rule_index_within_card}: {inner_dict_to_string(inner_dict)}')
        # print('}')
        if(len(rc_info) > 1): # if there are multiple rules this card could be
            unique_answers_this_rc = set()
            for inner_dict in rc_info.values():
                for possibility in inner_dict.keys():
                    unique_answers_this_rc.add(possibility)
            # NOTE: This below block may not be necessary at all, as even if it's not included, it's fine, b/c when you calculate the information gain of a possible query, it will show that querying this card results in an information gain of 0.
            # NOTE: Actually, I don't think this should happen at all. Shouldn't every possible answer appear at least once on every possible rules card, otherwise the answer isn't possible at all? Good thing the program exits if this happens.
            if(len(unique_answers_this_rc) == 1):
                print(f"Huh! Rules card {rc_index} is 'unsolved' in the sense that it is unknown which of the rules on it is being checked for, but it doesn't matter(?) because no matter which rule is the one that's being checked, they all lead to the same answer. Exiting.")
                exit()
            elif(len(unique_answers_this_rc) > 1):
                unsolved_rules_card_indices_within_rules_cards_list.append(rc_index)
            else:
                print("Your program is broken, b/c this rules card has no possible answers.")
                exit()
    # print()
    # print(f'Unsolved rules cards indices: {unsolved_rules_card_indices_within_rules_cards_list}')
    return(unsolved_rules_card_indices_within_rules_cards_list)

def populate_useful_qs_dict(
        useful_queries_dict,
        unsolved_rules_card_indices_within_rules_cards_list,
        rules_cards_list,
        rc_infos,
        all_125_possibilities_set,
        possible_combos_with_answers,
        possible_combos,
        set_possible_answers,
    ):
    current_num_possible_combos = len(possible_combos)
    current_num_possible_answers = len(set_possible_answers)
    for unsolved_card_index in unsolved_rules_card_indices_within_rules_cards_list:
        corresponding_rc = rules_cards_list[unsolved_card_index]
        corresponding_rc_info = rc_infos[unsolved_card_index]
        possible_rules_this_card = [
            corresponding_rc[possible_rule_index] for possible_rule_index in corresponding_rc_info.keys()
        ]
        # print(f"On unsolved rules card: {unsolved_card_index}")
        # print(f"Possible rules: {[r.name for r in possible_rules_this_card]}")
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
                # NOTE: redoing a lot of work here, as many possible useful queries will result in exactly the same possible_accepting_rules_card_indices and possible_rejecting_rules_card_indices as previous queries, so you're recomputing the work of the answers remaining if result is true or false. TODO: Consider making it a function and caching results for use later.
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
                #     print(f"Failed when considering query: {answer_tup_to_string(possible_query)} on card {string.ascii_uppercase[unsolved_card_index]}")
                #     print_all_possible_answers("Combos remaining if true:", set_answers_remaining_if_true, possible_combos_with_answers_remaining_if_true)
                #     print_all_possible_answers("Combos remaining if false:", set_answers_remaining_if_false, possible_combos_with_answers_remaining_if_false)
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
        # print out all query info relevant to this card
        # q_dict_this_card = dict()
        # print()
        # for q in sorted(useful_queries_dict.keys()):
        #     inner_dict = useful_queries_dict[q]
        #     if(unsolved_card_index in useful_queries_dict[q]):
        #         q_info = inner_dict[unsolved_card_index]
        #         q_dict_this_card[q] = q_info
        # print(f'For card {string.ascii_uppercase[unsolved_card_index]}. Possible rules: {rules_list_to_names(possible_rules_this_card)}')
        # print(f"# useful queries this card: {len(q_dict_this_card)}")
        # for q in sorted(q_dict_this_card.keys()):
        #     q_info = q_dict_this_card[q]
        #     print((' ' * 4) + answer_tup_to_string(q))
        #     print(f'{" " * 8} {"expected_a_info_gain":<25}: {q_info.expected_a_info_gain:.3f}')
        #     print(f'{" " * 8} {"p_true":<25}: {q_info.p_true:.3f}')
        #     print(f'{" " * 8} {"a_info_gain_true":<25}: {q_info.a_info_gain_true:0.3f}')
        #     print(f'{" " * 8} Combos remaining if query returns True:')
        #     for (i, (combo, answer)) in enumerate(sorted(q_info.possible_combos_with_answers_remaining_if_true, key=lambda t:(t[1], tuple([r.card_index for r in t[0]]))), start=1):
        #         print(f'{" " * 12} {i:>3}: {answer_tup_to_string(answer)} {rules_list_to_names(combo)}, {tuple([r.card_index for r in combo])}')
        #     for i in sorted(q_info.set_indexes_cwa_remaining_true, key=lambda t:(t[1], t[0])):
        #         print(f'{" " * 14} {i}')
        #     print()
        #     print(f'{" " * 8} {"p_false":<25}: {1 - q_info.p_true:0.3f}') 
        #     print(f'{" " * 8} {"a_info_gain_false":<25}: {q_info.a_info_gain_false:0.3f}')
        #     print(f'{" " * 8} Combos remaining if query returns False:')
        #     for (i, (combo, answer)) in enumerate(sorted(q_info.possible_combos_with_answers_remaining_if_false, key=lambda t:(t[1], tuple([r.card_index for r in t[0]]))), start=1):
        #         print(f'{" " * 12} {i:>3}: {answer_tup_to_string(answer)} {rules_list_to_names(combo)}, {tuple([r.card_index for r in combo])}')
        #     for i in sorted(q_info.set_indexes_cwa_remaining_false, key=lambda t:(t[1], t[0])):
        #         print(f'{" " * 14} {i}')

Query_Info = namedtuple(
    'Query_Info',
    [   # NOTE: TODO: will probably have to make possible_combos_with... a set when get to 2 and 3 query phase, in order to do set intersection when seeing what the best set of 2 or 3 queries to make in a round is. May have to override eq and hash and/or do tests to make sure that set intersection/comparison with combos/answers works. Consider this after finish 1 query/round work.
        'possible_combos_with_answers_remaining_if_true',
        'possible_combos_with_answers_remaining_if_false',
        'p_true',
        'a_info_gain_true',
        'a_info_gain_false',
        'expected_a_info_gain',
        'expected_c_info_gain',
        'set_indexes_cwa_remaining_true', # set of tuples (rc_indices of the cwa, (answer_tup)).
        'set_indexes_cwa_remaining_false'
    ]
)

Game_State = namedtuple(
    'Game_State',
    [
        'num_queries_this_round',
        'proposal_used_this_round',
        'fset_cwa_indexes_remaining',
        'fset_answers_remaining'
    ]
)

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
        game_state_false = Game_State(
            num_queries_this_round = num_queries_this_round,
            proposal_used_this_round = move[0],
            fset_cwa_indexes_remaining = fset_indexes_cwa_remaining_false,
            fset_answers_remaining = fset_answers_from_fset_cwa(fset_indexes_cwa_remaining_false)
        )
        game_state_true = Game_State(
            num_queries_this_round = num_queries_this_round,
            proposal_used_this_round = move[0],
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
            # TODO: make a function to create the (move, cost, gs_tuple, p_tuple) tuple and yield it here.
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

def print_game_state(gs, name="game_state", active=True):
    print(f'\nPrinting {name}:\nnum_queries_this_round: {gs.num_queries_this_round}.\nproposal_this_round: {answer_tup_to_string(gs.proposal_used_this_round)}')
    print(f"cwa set in game state:")
    for (i, cwa) in enumerate(map(lambda cwa: rc_indexes_cwa_to_full_combos_dict[cwa], sorted(gs.fset_cwa_indexes_remaining, key = lambda cwa: cwa[1]))):
        print_combo_with_answer(i, cwa)
    print(f"answer set in game state:")
    for (i, ans) in enumerate(sorted(map(lambda ans_tup:answer_tup_to_string(ans_tup), gs.fset_answers_remaining))):
        print(f'{i+1}: {ans}')


# TODO: cache the output of this function for {game_state : (best_move, cost of that move)}
# see get_moves docstring for definitions of move and cost.
# NOTE: do I actually need current_round_num or total_queries_made parameters in args to below? Yes, for pruning purposes. Or is it? B/c even if cost is high, probability could be low? But you know the probabilities. Think about it later. Then previous_best is a tuple of (expected_round_num_solved, expected_total_queries?) Consider making these two args a tuple for easy comparison.
# WARN: copy game state, no mutate
def calculate_best_move(qs_dict, game_state, previous_best, current_round_num, total_queries_made, mov_history=[]):
    """
    Returns a tuple (best move in this state, mov_cost_tup, gs_tup, expected cost to win from game_state (this is a tuple of (expected rounds, expected total queries))).
    best_move_tup is a tup of (proposal, rc_index)
    # TODO: delete the mov_history, as it was only used for debugging.
    """
    best_move = None
    (expected_round_cost, expected_queries_cost) = (0, 0)
    if(len(game_state.fset_answers_remaining) == 1):
        return( (None, None, None, (0,0)) )
    # print here to avoid printing all the game states directly at end of game
    # print(f"\ncurrent round: {current_round_num}. total_queries: {total_queries_made}.")
    # print(f"Move history: {mov_history}")
    # print_game_state(game_state)
    best_expected_cost_tup = (float('inf'), float('inf'))
    for move_info in get_and_apply_moves(game_state, qs_dict):
        gs_tup = move_info[2]
        p_tup = move_info[3]
        mov_cost_tup = move_info[1]
        (p_false, p_true) = p_tup
        (_, _, _, gs_false_expected_cost_to_win) = calculate_best_move(
            qs_dict,
            gs_tup[0],
            previous_best, # NOTE: not actually used yet.
            current_round_num + mov_cost_tup[0], # NOTE: correct value, but not used yet.
            total_queries_made + 1, # NOTE: not used yet. To use, add in a move's cost to these values, compare to previous best, and if worse, abandon this branch. For previous best, update it with each new answer you get (after multiplying by probs and adding), and start it at +infinity.
            mov_history + [f'{answer_tup_to_string(move_info[0][0])} to verifier {string.ascii_uppercase[move_info[0][1]]}. False']
            # mov_history + [f'{answer_tup_to_string(move_info[0][0])} to verifier {string.ascii_uppercase[move_info[0][1]]}']
        )
        (_, _, _, gs_true_expected_cost_to_win) = calculate_best_move(
            qs_dict,
            gs_tup[1],
            previous_best, # NOTE: not actually used yet.
            current_round_num + mov_cost_tup[0], # NOTE: correct value, but not used yet.
            total_queries_made + 1, # all moves cost 1 query
            mov_history + [f'{answer_tup_to_string(move_info[0][0])} to verifier {string.ascii_uppercase[move_info[0][1]]}. True.']
        )
        (mov_round_cost, mov_query_cost) = mov_cost_tup
        expected_round_cost = mov_round_cost + (p_false * gs_false_expected_cost_to_win[0]) + (p_true * gs_true_expected_cost_to_win[0])
        expected_query_cost = mov_query_cost + (p_false * gs_false_expected_cost_to_win[1]) + (p_true * gs_true_expected_cost_to_win[1])
        expected_cost_tup = (expected_round_cost, expected_query_cost)
        if(expected_cost_tup < best_expected_cost_tup):
            best_expected_cost_tup = expected_cost_tup
            best_move_tup = move_info[0]
            best_mov_cost_tup = mov_cost_tup
            best_gs_tup = gs_tup
    return((best_move_tup, best_mov_cost_tup, best_gs_tup, expected_cost_tup))

# TODO: have the program handle standard mode before it handles nightmare mode.
# a problem is a list of rules cards.
def solve(rules_cards_nums_list):
    """
    rules_card_nums_list is a list of the names (numbers) of the rules cards in this problem. Solve will print out which queries to perform, and (TBD) either print out what to do in all possible cases, or ask for the answers of the queries and proceed from there.
    """
    num_rules_cards = len(rules_cards_nums_list)
    # TODO: change below for extreme mode. Will also need to change the card_index of each rules in a rules card in extreme mode, since each card is now a combo of 2 cards.
    rules_cards_list = [rcs_deck[num] for num in rules_cards_nums_list]
    possible_combos_with_answers = get_possible_rules_combos_with_answers(rules_cards_list)
    global rc_indexes_cwa_to_full_combos_dict # TODO: remove the global modifier on this after debug
    rc_indexes_cwa_to_full_combos_dict = {}
    for cwa in possible_combos_with_answers:
        rc_indexes_cwa_to_full_combos_dict[(tuple([r.card_index for r in cwa[0]]), cwa[1])] = cwa
    (possible_combos, possible_answers) = zip(*possible_combos_with_answers)
    set_possible_answers = set(possible_answers)
    print_problem(rcs_list=rules_cards_list, active=True)
    print_all_possible_answers("All possible answers:", set_possible_answers, possible_combos_with_answers)

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
    while(len(set_possible_answers) > 1):
        # see todo.txt for documentation on what exactly rc_infos is
        rc_infos = make_rc_infos(num_rules_cards, possible_combos_with_answers)
        unsolved_rules_card_indices_within_rules_cards_list = get_unsolved_rules_card_indices(rc_infos)

        # useful_queries_dict is {
        #     key = proposal (answer tuple): value = {
        #        inner_key = index of the rule card this query goes to: value = Query_Info (see named tuple)
        #     }
        # }
        useful_queries_dict = dict()
        populate_useful_qs_dict(
            useful_queries_dict,
            unsolved_rules_card_indices_within_rules_cards_list,
            rules_cards_list,
            rc_infos,
            all_125_possibilities_set,
            possible_combos_with_answers,
            possible_combos,
            set_possible_answers,
        )
        fset_cwa_indexes_remaining = frozenset(
            map(
                lambda cwa: (tuple([r.card_index for r in cwa[0]]), cwa[1]),
                possible_combos_with_answers
            )
        )
        initial_game_state = Game_State(0, None, fset_cwa_indexes_remaining, frozenset(set_possible_answers))
        (best_move_tup, mcost_tup, gs_tup, expected_cost_tup) = calculate_best_move(
            qs_dict=useful_queries_dict,
            game_state=initial_game_state,
            previous_best=float('inf'),
            current_round_num=1,
            total_queries_made=0
        )
        print(f"\nQuery {answer_tup_to_string(best_move_tup[0])} to verifier {string.ascii_uppercase[best_move_tup[1]]}. Expected game winning round: {expected_cost_tup[0] + 1}. Expected number of queries to win: {expected_cost_tup[1]}.")
        # (best_query, corresponding_rc_index, best_q_info) = (None, None, None)
        # (best_expected_a_info_gain, best_expected_c_info_gain) = (0, 0)
        # for (q, inner_dict) in useful_queries_dict.items():
        #     for (rc_index, q_info) in inner_dict.items():
        #         if((q_info.expected_a_info_gain, q_info.expected_c_info_gain) > (best_expected_a_info_gain, best_expected_c_info_gain)):
        #             (best_expected_a_info_gain, best_expected_c_info_gain) = (q_info.expected_a_info_gain, q_info.expected_c_info_gain)
        #             (best_query, corresponding_rc_index, best_q_info) = (q, rc_index, q_info)

        # print(f'\nQuery {answer_tup_to_string(best_query)} to verifier {string.ascii_uppercase[corresponding_rc_index]}. Expected answer info gain: {best_expected_a_info_gain:0.3f}. Expected combo info gain: {best_expected_c_info_gain:0.3f}.')
        # print("Result of query (T/F)\n> ", end="")
        # result_raw = input()
        # if(result_raw == 'q'):
        #     exit()
        # result = (result_raw in ['T', 't'])
        # possible_combos_with_answers = best_q_info.possible_combos_with_answers_remaining_if_true if(result) else best_q_info.possible_combos_with_answers_remaining_if_false
        # (possible_combos, possible_answers) = zip(*possible_combos_with_answers)
        # set_possible_answers = set(possible_answers)
        exit()
        # query loop end
    # Found an answer
    print_all_possible_answers("ANSWER:", set_possible_answers, possible_combos_with_answers)

# TODO: put in display file
def answer_tup_to_string(answer):
    return("".join(str(d) for d in answer) if (answer is not None) else "None")
def rules_list_to_names(rl, pad=True):
    pad_spaces = max_rule_name_length if(pad) else 0
    names = [f'{r.name:<{pad_spaces}}' for r in rl]
    return(', '.join(names))
def print_all_possible_answers(message, set_possible_answers, possible_combos_with_answers):
    print("\n" + message)
    final_answer = (len(set_possible_answers) == 1)
    multiple_combo_spacing = 7 if final_answer else 9
    for(answer_index, possible_answer) in enumerate(sorted(set_possible_answers), start=1):
        relevant_combos = [c for (c,a) in possible_combos_with_answers if (a == possible_answer)]
        answer_number_str = '   ' if final_answer else f'{answer_index:>3}: '
        print(f"{answer_number_str}{answer_tup_to_string(possible_answer)} {rules_list_to_names(relevant_combos[0])}")
        for c in relevant_combos[1:]:
            print(f"{' ' * multiple_combo_spacing}{rules_list_to_names(c)}")
def print_combo_with_answer(combo_with_answer_index, combo_with_answer):
    (possible_combo, possible_answer) = combo_with_answer
    print(f'{combo_with_answer_index + 1:>3}: {answer_tup_to_string(possible_answer)} {rules_list_to_names(possible_combo)}, rules_card_indices: {[r.card_index for r in possible_combo]}')
def inner_dict_to_string(inner_dict):
    s = '{ '
    for (possibility, combos_list) in inner_dict.items():
        s += f'{answer_tup_to_string(possibility)}: {[[r.card_index for r in combo] for combo in combos_list]} '
    s += '}'
    return(s)
def print_problem(rcs_list, active):
    """
    NOTE: will have to change this for nightmare mode, since rules cards won't have corresponding letters, only numbers.
    """
    if(active):
        print("\nProblem")
        for (i, rc) in enumerate(rcs_list):
            print(f'{string.ascii_uppercase[i]}: {rules_list_to_names(rc)}')
# solve([2, 5, 9, 15, 18, 22]) # corresponds to zero_query_problem.png. Can be solved without making any queries. Problem ID: "B63 YRW 4" on the website turingmachine.info.
# solve([4, 9, 11, 14]) # problem 1 in the book
# solve([3, 7, 10, 14]) # problem 2 in the book. FTF 435
solve([9, 22, 24, 31, 37, 40]) # "C63 0YV B" online. Interesting b/c multiple combos lead to same answer here. T 351