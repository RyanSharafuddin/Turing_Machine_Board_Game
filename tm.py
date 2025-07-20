import math, copy
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

for (rule_card_num, rule_card) in rules_cards.items():
    rules_cards[rule_card_num] = [func_to_Rule(f, i) for (i, f) in enumerate(rule_card)]
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

# TODO: have the program handle standard mode before it handles nightmare mode. 
# a problem is a list of rules cards.
def solve(rules_cards_nums_list):
    """
    rules_card_list is a list of the names (numbers) of the rules cards in this problem. Solve will print out which queries to perform, and (TBD) either print out what to do in all possible cases, or ask for the answers of the queries and proceed from there.
    """
    num_rules_cards = len(rules_cards_nums_list)
    rules_cards_list = [rules_cards[num] for num in rules_cards_nums_list]    # TODO: change for extreme mode. Will also need to change the card_index of each rules in a rules card in extreme mode, since each card is now a combo of 2 cards.
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

    possible_combos_with_answers = [] # tuples of ([rules_list], answer_tuple)
    for combo in rules_combos:
        (possible, answer) = is_combo_possible(combo)
        if(possible):
            possible_combos_with_answers.append((combo, answer))


    original_possible_combos_with_answers = copy.deepcopy(possible_combos_with_answers)
    (possible_combos, possible_answers) = zip(*possible_combos_with_answers)
    set_possible_answers = set(possible_answers)
    print_all_possible_answers("All possible answers:", set_possible_answers, possible_combos_with_answers)

    len_possible_answers = len(possible_answers) # the tuples that are the answer number
    num_unique_possible_answers = len(set_possible_answers)

    # Note: may not need this block below.
    if(num_unique_possible_answers != len_possible_answers):
        print("NOTE: There are different possible rules combos that give rise to the same answer. Perhaps you can exploit this to solve for the answer without also needing to solve for which rules combo gives rise to the answer? Consider it.")
        exit()

    # NOTE TODO: It's not the number of possible combos that you have to narrow down to 1; it's the number of possible answer tuples that you have to narrow down to 1.
    while(len(set_possible_answers) > 1):
        rules_card_infos = [dict() for i in range(num_rules_cards)]
        # rules_card_infos[i] is a dict for the ith rules card in rules_cards_list, where each key is the rules_card_index of a possible rule that the ith card could be, and the value mapped to that key is a dictionary {a:b}, where a is a possible answer tuple and b is a list of combos that correspond to that answer tuple and that rule from the rule card.
        print("POSSIBLE COMBOS:")
        for (combo_with_answer_index, combo_with_answer) in enumerate(possible_combos_with_answers):
            (possible_combo, possible_answer) = combo_with_answer
            print(f'{combo_with_answer_index + 1:>3}: {answer_tup_to_string(possible_answer)}, {combo_to_combo_rules_names(possible_combo):<150}, rules_card_indices: {[r.card_index for r in possible_combo]}')

            for (rule_card_index, rule) in enumerate(possible_combo):
                rules_card_info_dict = rules_card_infos[rule_card_index]
                answer_within_this_card_index = rule.card_index
                if(answer_within_this_card_index in rules_card_info_dict):
                    this_rule_s_inner_dict = rules_card_info_dict[answer_within_this_card_index]
                    if(possible_answer) in this_rule_s_inner_dict:
                        this_rule_s_inner_dict[possible_answer].append(possible_combo)
                    else:
                        this_rule_s_inner_dict[possible_answer] = [possible_combo]
                else:
                    rules_card_info_dict[answer_within_this_card_index] = {possible_answer: [possible_combo]}

        unsolved_rules_card_indices_within_rules_cards_list = []
        # print internal info
        print()
        for (rc_index, rc_info) in enumerate(rules_card_infos):
            print(f'rules card {rc_index}:' + ' {')
            for (rule_index_within_card, inner_dict) in rc_info.items():
                print(f'    possible rule index: {rule_index_within_card}: {inner_dict_to_string(inner_dict)}')
            print('}')
            if(len(rc_info) > 1):
                #TODO: consider not listing a rules card as unsolved in the case that there are multiple possible rules it could be, but they all lead to the same answer. Maybe have a warning/exit block if this happens.
                unique_answers_this_rc = set()
                for inner_dict in rc_info.values():
                    for possibility in inner_dict.keys():
                        unique_answers_this_rc.add(possibility)
                # NOTE: This below block may not be necessary at all, as even if it's not included, it's fine, b/c when you calculate the information gain of a possible query, it will show that querying this card results in an information gain of 0.
                if(len(unique_answers_this_rc) == 1):
                    print(f"Huh! Rules card {rc_index} is 'unsolved' in the sense that it is unknown which of the rules on it is being checked for, but it doesn't matter(?) because no matter which rule is the one that's being checked, they all lead to the same answer. Exiting.")
                    exit()
                else:
                    unsolved_rules_card_indices_within_rules_cards_list.append(rc_index)
        print()
        print(f'Unsolved rules cards indices: {unsolved_rules_card_indices_within_rules_cards_list}')
        for unsolved_card_index in unsolved_rules_card_indices_within_rules_cards_list:
            useful_queries_dict = dict() # key = query, value = tuple of ([rules eliminated if true], [rules eliminated if false]). TODO: populate this and also find out how 'set-like' the dict.keys() view is: can it be used directly like a set? How do view objects work anyway?
            useful_queries_set = set() # TODO will need to keep track of each card's useful queries set
            corresponding_rule_card = rules_cards_list[unsolved_card_index]
            corresponding_rc_info = rules_card_infos[unsolved_card_index]
            possible_rules_this_card = []
            for possible_rule_index in corresponding_rc_info.keys():
                possible_rules_this_card.append(corresponding_rule_card[possible_rule_index])
            print(f"On unsolved rules card: {unsolved_card_index}")
            print(f"Possible rules: {[r.name for r in possible_rules_this_card]}")
            for possible_query in all_125_possibilities_set:
                possible_rules_accepting = []
                possible_rules_rejecting = []
                for possible_rule in possible_rules_this_card:
                    if(possible_query in possible_rule.reject_set):
                        possible_rules_rejecting.append(possible_rule)
                    else:
                        possible_rules_accepting.append(possible_rule)
                if(bool(possible_rules_accepting) and bool(possible_rules_rejecting)):
                    useful_queries_set.add(possible_query)
            print(f"# useful queries: {len(useful_queries_set)}")
            for q in sorted(useful_queries_set):
                print(answer_tup_to_string(q))
            # TODO: for each useful query, calculate which combos and possible answers will remain if the result is true and if the result is false (use the flat lists from the beginning rather than the nested info dicts?), and, using the number of combos and possible answers that existed before, calculate the probability of it being true or false (assuming each combo is equally likely), as well as the information gain resulting from it being true or false, and then calculate the expected information gain from that query. Keep track of the single query that results in a highest expected information gain, and then later also the one proposal (single number) with 2 queries that results in highest gain, then the 3 queries. But get the 1 query completely working first.
            print()

        exit() # TODO: delete when write in queries to eliminate possible answers each turn

    print_all_possible_answers("ANSWER:", set_possible_answers, possible_combos_with_answers)

# TODO: put in display file
def answer_tup_to_string(answer):
    return("".join(str(d) for d in answer))
def combo_to_combo_rules_names(combo):
    return(str([r.name for r in combo]))
def print_all_possible_answers(message, set_possible_answers, possible_combos_with_answers):
    print(message)
    final_answer = (len(set_possible_answers) == 1)
    for(answer_index, possible_answer) in enumerate(sorted(set_possible_answers), start=1):
        print(f"{f'{answer_index:>3}: ' if(not final_answer) else ''}{answer_tup_to_string(possible_answer)}")
        for (c, a) in possible_combos_with_answers:
            if(a == possible_answer):
                print(f"{' ' * 8}{combo_to_combo_rules_names(c)}")
    print()
def inner_dict_to_string(inner_dict):
    s = '{ '
    for (possibility, combos_list) in inner_dict.items():
        s += f'{answer_tup_to_string(possibility)}: {[[r.card_index for r in combo] for combo in combos_list]} '
    s += '}'
    return(s)

# solve([2, 5, 9, 15, 18, 22]) # corresponds to zero_query_problem.png. Can be solved without making any queries.
solve([4, 9, 11, 14]) # problem 1 in the book
# solve([3, 7, 10, 14]) # problem 2 in the book