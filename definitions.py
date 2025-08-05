from collections import namedtuple


def get_digit(n, index, base=10):
    """
    Given a nonnegative integer n and an index, get the digit at that index of n. For example, if n is 3289, and index is 0, will return 9. index 1 will return 8. index 2 will return 2. Can optionally choose a base other than 10.
    """
    n = n // (base ** index)
    return (n % base)

possibilities = [sum([(get_digit(n, d, 5) + 1) * (10 ** d) for d in range(2, -1, -1)]) for n in range(125)]
all_125_possibilities_set = set(possibilities)

def int_to_tri_sq_ci_tuple(n):
    return(tuple([get_digit(n, i, 10) for i in range(2, -1, -1)]))

Rule = namedtuple('Rule', ['name', 'reject_set', 'func', 'card_index', 'unique_id'])

Query_Info = namedtuple(
    'Query_Info',
    [
        # 'possible_combos_with_answers_remaining_if_true',  # unneeded
        # 'possible_combos_with_answers_remaining_if_false', # unneeded
        # 'p_true',                                          # unneeded
        # 'a_info_gain_true',                                # unneeded
        # 'a_info_gain_false',                               # unneeded
        # 'expected_a_info_gain',                            # unneeded
        # 'expected_c_info_gain',                            # unneeded
        'set_indexes_cwa_remaining_true', # corresponds to game state sets of indexes remaining
        'set_indexes_cwa_remaining_false' # corresponds to game state sets of indexes remaining
    ]
)

Game_State = namedtuple(
    'Game_State',
    [
        'num_queries_this_round',
        'proposal_used_this_round',
        'fset_cwa_indexes_remaining', # {((2, 3, 4, 7), 121), ...}
        # In nightmare mode, each item in fset_cwa_indexes_remaining is:
        # ((card_indices of rules in combo), (verifier permutation tuple), answer int)
    ]
)

Problem = namedtuple(
    'Problem',
    [
        'rc_nums_list',
        'identity',     # This is the full ID, without spaces, from the website. string.
        'mode',         # 0, 1, or 2 for standard, extreme, or nightmare.
    ]
)

STANDARD = 0
EXTREME = 1
NIGHTMARE = 2

# rules_card_infos[i] is a dict for the ith verifier (which, in a non-nightmare game, corresponds to the ith rules card in rules_cards_list). That dict is:

# rules_card_infos[i] = {
#   outer_key = rule_index (index within card of a possible rule that the ith card could be):
#   if nightmare mode, outer_key = (corresponding_rc_index, rule_index). corresponding_rc_index is an index of a rule card that this verifier card could correspond to, and rule_index is the index of a rule on that card that this verifier could be verifying.
#   val = {
#       key = possible answer int that could be the case if the verifier is checking for the rule given by the outer key :
#       val = [all rule combos that correspond to that answer tuple and outer_key]
#             in nightmare mode, each item in above list is a tuple of (combo, permutation)
#             otherwise, each list item is just the combo
#   }
# }

# useful_queries_dict is {
#     key = proposal (answer int): value = {
#        inner_key = index of a rule card this query goes to: value = Query_Info (see named tuple)
#     }
# }

# q_history is a list of rounds 
# [
#    [proposal, (verifier queried, result), (verifier queried, result), ...]
#    [next round] ...
# ]