from collections import namedtuple


def get_digit(n, index, base=10):
    """
    Given a nonnegative integer n and an index, get the digit at that index of n. For example, if n is 3289, and index is 0, will return 9. index 1 will return 8. index 2 will return 2. Can optionally choose a base other than 10.
    """
    n = n // (base ** index)
    return (n % base)

possibilities = [tuple([get_digit(n, d, 5) + 1 for d in range(2, -1, -1)]) for n in range(125)]
all_125_possibilities_set = set(possibilities)
#NOTE: each possibility in the possibilities list is a tuple of the 3 digits. i.e. the answer
#      524 is represented as the tuple (5, 2, 4), with tuple[0] being the most significant digit.
Rule = namedtuple('Rule', ['name', 'reject_set', 'func', 'card_index'])

Query_Info = namedtuple(
    'Query_Info',
    [
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


# rules_card_infos[i] is a dict for the ith rules card in rules_cards_list. That dict is:
# rules_card_infos[i] = {
#   key = rule_index (index within card of a possible rule that the ith card could be) : val = {
#      key = possible answer tuple for that rules_card_index :
#       val = [all rule combos that correspond to that answer tuple and rules_card_index]
#   }
# }

# useful_queries_dict is {
#     key = proposal (answer tuple): value = {
#        inner_key = index of a rule card this query goes to: value = Query_Info (see named tuple)
#     }
# }