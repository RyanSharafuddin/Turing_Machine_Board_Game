from collections import namedtuple
from rich.console import Console


def get_digit(n, index, base=10):
    """
    Given a nonnegative integer n and an index, get the digit at that index of n. For example, if n is 3289, and index is 0, will return 9. index 1 will return 8. index 2 will return 2. Can optionally choose a base other than 10.
    """
    n = n // (base ** index)
    return (n % base)

def add_tups(*tups):
    """ Adds tuple arguments element-wise. WARN: do not use for anything performance-critical. """
    result = tuple([sum([t[i] for t in tups]) for i in range(len(tups[0]))])
    return(result)

possibilities = [sum([(get_digit(n, d, 5) + 1) * (10 ** d) for d in range(2, -1, -1)]) for n in range(125)]
all_125_possibilities_set = set(possibilities)

def int_to_tri_sq_ci_tuple(n):
    return(tuple([get_digit(n, i, 10) for i in range(2, -1, -1)]))

Rule = namedtuple('Rule', ['name', 'reject_set', 'func', 'card_index', 'unique_id'])

Query_Info = namedtuple(
    'Query_Info',
    [
        'cwa_set_true',
        'cwa_set_false'
    ]
)

Game_State = namedtuple(
    'Game_State',
    [
        'num_queries_this_round',
        'proposal_used_this_round',
        'cwa_set', # a set of ints corresponding to the indexes of the cwas in the the full_cwas_list
    ]
)

Problem = namedtuple(
    'Problem',
    [
        'identity',     # This is the full ID, without spaces, from the website. string.
        'rc_nums_list',
        'mode',         # 0, 1, or 2 for standard, extreme, or nightmare.
    ]
)

STANDARD = 0
EXTREME = 1
NIGHTMARE = 2
console = Console(force_terminal=True) # See https://rich.readthedocs.io/en/latest/console.html
# By default, Rich strips color escape codes if it detects that it is not printing directly to a terminal (for example, if it is printing to a file or if it's being piped into another program like less). With force_terminal, we can make it print color codes regardless of whether it is directly printing to a terminal.


# useful_queries_dict is {
#     key = proposal (answer int): value = {
#        inner_key = index of a verifier card this query goes to: value = Query_Info (see named tuple)
#     }
# }

# q_history is a list of rounds 
# [
#    [proposal, (verifier queried, result), (verifier queried, result), ...]
#    [next round] ...
# ]