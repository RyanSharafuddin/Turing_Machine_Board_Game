from definitions import *
from solver import STANDARD, EXTREME, NIGHTMARE

# STANDARD
STANDARD_PROB_TUPS = [
    (      "1",         [ 4,  9, 11, 14]),
    (      "2",         [ 3,  7, 10, 14]),
    ( "C4643N",         [19, 22, 36, 41]),
    ("A52F7E1",     [ 7,  8, 12, 14, 17]),
    ( "C5HCBJ",     [ 2, 15, 30, 31, 33]),
    ("B63YRW4", [ 2,  5,  9, 15, 18, 22]), # zero_query
    ("C630YVB", [ 9, 22, 24, 31, 37, 40]), # multiple combos -> same answer
]

# EXTREME
EXTREME_PROB_TUPS = [
    ( "F435FE",                  [13,  9, 11, 40, 18,  7, 43, 15]), # 3,545 seconds.
    ( "F5XTDF",          [28, 14, 19,  6, 27, 16,  9, 47, 20, 21]), #   168 seconds.
    ("F52LUJG",          [15, 16, 23,  8, 46, 13, 34, 17,  9, 37]),
    ("E63YF4H",  [18, 16, 17, 19, 10,  5, 14,  1, 11,  6,  2,  9]),
    ("F63EZQM",  [15, 44, 11, 23, 40, 17, 25, 10, 16, 20, 19,  3]),
]

NIGHTMARE_PROB_TUPS = [
    ( "I4BYJK",          [9, 23, 33, 34]), # Test after fix nightmare isomorphic
]
NIGHTMARE_PROB_TUPS += [(f"{p_id}_N", rc_nums) for (p_id, rc_nums) in STANDARD_PROB_TUPS]
# NOTE: Any standard mode problem is now also a nightmare mode problem if just add "_N" to its problem id.


standard_problems = [Problem(*(problem_tup + (STANDARD,))) for problem_tup in STANDARD_PROB_TUPS]
extreme_problems =  [Problem(*(problem_tup + (EXTREME,))) for problem_tup in EXTREME_PROB_TUPS]
nightmare_problems =  [Problem(*(problem_tup + (NIGHTMARE,))) for problem_tup in NIGHTMARE_PROB_TUPS]
all_problems = standard_problems + extreme_problems + nightmare_problems
problem_identities = set()
for p in all_problems:
    if(p.identity in problem_identities):
        print(f"Error! There are multiple problems with identity {p.identity}. Exiting.")
        exit()
    problem_identities.add(p.identity)
id_to_problem_dict = {problem.identity: problem for problem in all_problems}
def get_problem_by_id(problem_id: str):
    """ All problems should be defined in problems.py. See this file for how it all works."""
    return(id_to_problem_dict[problem_id])