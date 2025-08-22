from definitions import *

# NOTE: Problem IDs should not contain lowercase letters, so that the user can specify either lowercase or uppercase letters when they request a problem.

# STANDARD
STANDARD_PROB_TUPS = [
    (      "1",         [ 4,  9, 11, 14]),
    (      "2",         [ 3,  7, 10, 14]), # Nightmare version: 2,081 -> 307 -> 110 -> 94.
    ( "C4643N",         [19, 22, 36, 41]),
    ("A52F7E1",     [ 7,  8, 12, 14, 17]),
    ( "C5HCBJ",     [ 2, 15, 30, 31, 33]),
    ("B63YRW4", [ 2,  5,  9, 15, 18, 22]), # zero_query
    ("C630YVB", [ 9, 22, 24, 31, 37, 40]), # multiple combos -> same answer
    ("INVALID", [ 1,  2,  3,  4,  5,  6])  # invalid problem for testing purposes
]

# EXTREME
EXTREME_PROB_TUPS = [
    ( "F435FE",                  [13,  9, 11, 40, 18,  7, 43, 15]), # 2,904 -> 1,195 -> ~650
    ( "F5XTDF",          [28, 14, 19,  6, 27, 16,  9, 47, 20, 21]), #    86 -> 70
    ("F52LUJG",          [15, 16, 23,  8, 46, 13, 34, 17,  9, 37]),
    ("E63YF4H",  [18, 16, 17, 19, 10,  5, 14,  1, 11,  6,  2,  9]),
    ("F63EZQM",  [15, 44, 11, 23, 40, 17, 25, 10, 16, 20, 19,  3]),
]

NIGHTMARE_PROB_TUPS = [
    ( "I4BYJK",          [9, 23, 33, 34]), # Test after fix nightmare isomorphic
]
derived_nightmare_prob_tups = [(f"{p_id}_N", rc_nums) for (p_id, rc_nums) in STANDARD_PROB_TUPS]
derived_standard_prob_tups = [(f"{p_id}_S", rc_nums) for (p_id, rc_nums) in NIGHTMARE_PROB_TUPS]
NIGHTMARE_PROB_TUPS += derived_nightmare_prob_tups
STANDARD_PROB_TUPS += derived_standard_prob_tups
# NOTE: Any standard mode problem is now also a nightmare mode problem if just add "_N" to its problem id.
#       Also, any nightmare mode problem is a standard mode problem by adding "_S".


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
prefix_id_to_problem_list_dict = dict()
for (identity, problem) in id_to_problem_dict.items():
    for i in range(len(identity)):
        prefix: str = identity[:i+1]
        if not(identity.endswith('_N') or identity.endswith('_S')):
            pref_add = prefix
        elif(len(prefix) + 2 <= len(identity)):
            pref_add = f'{prefix}_{identity[-1]}'
        else:
            break
        if(pref_add in prefix_id_to_problem_list_dict):
            prefix_id_to_problem_list_dict[pref_add].append(problem)
        else:
            prefix_id_to_problem_list_dict[pref_add] = [problem]


# console.print(prefix_id_to_problem_list_dict)
def get_problem_by_id(problem_id: str):
    """ All problems should be defined in problems.py. See this file for how it all works. """
    problem_id = problem_id.upper()
    problem_list = prefix_id_to_problem_list_dict.get(problem_id, [])
    if(not problem_list):
        print(f"Error: The problem id requested '{problem_id}' is not defined in problems.py. Exiting.")
        exit()
    if(len(problem_list) > 1):
        print(f"There are multiple problems f{problem_id} could refer to. Here they are:\n")
        for(index, problem) in enumerate(problem_list, start=1):
            console.print(index, ": ", problem, sep="", end="")
        a = int(input("\nWhich one would you like?\n> "))
        return(problem_list[a - 1])
    return(problem_list[0])
