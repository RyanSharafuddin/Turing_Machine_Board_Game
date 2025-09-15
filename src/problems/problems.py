import pickle, os
from rich.table import Table
from rich.text import Text
# My imports
from ..core.config import *
from ..core.definitions import *
from ..core.display import MODE_NAMES, Solver_Displayer
from ..core.rules import rcs_deck
from ..core import solver

# NOTE: Problem IDs should not contain lowercase letters, so that the user can specify either lowercase or uppercase letters when they request a problem.
_STANDARD_PROB_TUPS = [
    (      "1",         [ 4,  9, 11, 14]),
    (      "2",         [ 3,  7, 10, 14]), # Nightmare version: 2,081 -> 307 -> 110 -> 94.
    ( "C4643N",         [19, 22, 36, 41]),
    ("A52F7E1",     [ 7,  8, 12, 14, 17]),
    ( "C5HCBJ",     [ 2, 15, 30, 31, 33]),
    ("B63YRW4", [ 2,  5,  9, 15, 18, 22]), # zero_query
    ("C630YVB", [ 9, 22, 24, 31, 37, 40]), # multiple combos -> same answer. nightmare version 2880 cwas.
    ("INVALID", [ 1,  2,  3,  4,  5,  6])  # invalid problem for testing purposes
]
_EXTREME_PROB_TUPS = [
    ( "F435FE",                  [13,  9, 11, 40, 18,  7, 43, 15]), # 2,904 -> 1,195 -> ~650 -> ~500
    ( "F5XTDF",          [28, 14, 19,  6, 27, 16,  9, 47, 20, 21]), #    86 -> 70
    ("F52LUJG",          [15, 16, 23,  8, 46, 13, 34, 17,  9, 37]),
    ("E63YF4H",  [18, 16, 17, 19, 10,  5, 14,  1, 11,  6,  2,  9]),
    ("F63EZQM",  [15, 44, 11, 23, 40, 17, 25, 10, 16, 20, 19,  3]),
]
_NIGHTMARE_PROB_TUPS = [
    ( "I4BYJK",          [9, 23, 33, 34]), # Test after fix nightmare isomorphic
]
_IDS_TO_COMMENTS_DICT = {
    "B63YRW4"   : "Zero query",
    "C630YVB"   : "Mult. combos",
    "F5XTDF"    : "Formerly ~180s",
    "F63EZQM"   : "Excellent tree",
    "F52LUJG"   : "Excellent tree",
    "F435FE"    : "Formerly ~3,500s",
    "INVALID"   : "Example test",
    "INVALID_N" : "Example test",
    "I48ZCX"    : "Somehow harder than 2_N",
    "C630YVB_N" : "Killed 9",
}
_ACCEPTABLE_MODES = ["S", "E", "N"]
def _add_problem_to_both_dicts(problem: Problem):
    """
    Adds problem to ID_TO_PROBLEM_DICT and also PREFIX_ID_TO_PROBLEM_LIST_DICT, which is a pre-requisite for getting the problem with get_local_problem_by_id.
    """
    _ID_TO_PROBLEM_DICT[problem.identity] = problem
    _add_problem_to_prefix_id_dict(problem)
def _read_user_problems_from_file(f_name):
    """ Reads user problems from a file line by line and returns a list of them """
    l = []
    if not os.path.exists(f_name):
        with open(f_name, 'w') as f:
            pass # create the file if it doesn't exist
        return l
    with open(f_name, 'r') as f:
        for line in f:
            if(line.strip()):
                p = eval(line)
            l.append(p)
    return(l)
def _add_problem_to_prefix_id_dict(problem: Problem):
    identity = problem.identity
    for i in range(len(identity)):
        prefix: str = identity[:i+1]
        if not(identity.endswith('_N') or identity.endswith('_S')):
            pref_add = prefix
        elif(len(prefix) + 2 <= len(identity)):
            pref_add = f'{prefix}_{identity[-1]}'
        else:
            break
        if(pref_add in _PREFIX_ID_TO_PROBLEM_LIST_DICT):
            _PREFIX_ID_TO_PROBLEM_LIST_DICT[pref_add].append(problem)
        else:
            _PREFIX_ID_TO_PROBLEM_LIST_DICT[pref_add] = [problem]
def _user_input_to_triplet(s:str):
    """ helper function for get_problem_from_user_string """
    l = s.split()
    if(len(l) < 3):
        console.print(f"Error: '{s}' cannot be interpreted as a problem description.")
        return(None)
    if(l[-1].upper() not in _ACCEPTABLE_MODES):
        l.append('S') # assume mode 
    return(l[0], ' '.join(l[1:len(l)-1]), l[-1])
def _process_problem_input_from_user(p_id, rc_nums_str, mode_str):
    """ helper function for get_problem_from_user_string """
    problem_id = p_id.upper()
    if(problem_id in _ID_TO_PROBLEM_DICT):
        console.print(f"Error: There already exists a problem with ID '{problem_id}'")
        print("Note that problem IDs are not case-sensitive.")
        print(f"Returning the pre-existing problem with ID: '{problem_id}' instead.")
        return(_ID_TO_PROBLEM_DICT[problem_id])
    if(problem_id.endswith("_S") or problem_id.endswith("_N")):
        print("Error: Don't end problem IDs with '_S' or '_N'.")
        return(None)
    rcs_nums_strs_list = rc_nums_str.split()
    rc_nums = []
    for rc_num_str in rcs_nums_strs_list:
        try:
            rc = int(rc_num_str)
            rc_nums.append(rc)
            if(not rc in rcs_deck):
                console.print(f"Error: rule card {rc} is not defined in the rule card deck.")
                return(None)
        except ValueError:
            print(f"Error: '{rc_num_str}' cannot be interpreted as a rule card number.")
            return(None)
    if len(set(rc_nums)) != len(rc_nums):
        print(f"Error: Each rule card can only appear once in a problem.")
        return(None)
    mode = get_mode_from_user(mode_str)
    if(mode is None):
        print(f"Error: {mode_str} could not be interpreted as a mode.")
        return(None)
    if((mode == 1) and ((len(rc_nums) % 2) != 0)):
        print("Error: In Extreme mode, there should be an even number of rule cards.")
        return(None)
    p = Problem(identity=problem_id, rc_nums_list=rc_nums, mode=int(mode))
    s = solver.Solver(p)
    if not s.full_cwas_list:
        sd = Solver_Displayer(s)
        sd.print_problem(s.rcs_list, p)
        console.print(f"Error. This is an invalid problem with no solutions.")
        return(None)
    _add_problem_to_both_dicts(p)
    _write_user_problem_to_file(USER_PROBS_FILE_NAME, p)
    if((p.mode == STANDARD) or (p.mode == NIGHTMARE)):
        other_version_mode = NIGHTMARE if (p.mode == STANDARD) else STANDARD
        other_version_suffix = "_S" if other_version_mode == STANDARD else "_N"
        other_version_problem = Problem(
            f"{p.identity}{other_version_suffix}", p.rc_nums_list, other_version_mode
        )
        _add_problem_to_both_dicts(other_version_problem)
        _write_user_problem_to_file(USER_PROBS_FILE_NAME, other_version_problem)
    return(p)
def _write_user_problem_to_file(f_name, p: Problem):
    with open(f_name, "a+") as f:
        f.write(repr(p))
        f.write("\n")

def get_local_problem_by_id(problem_id: str):
    """
    Get a local problem (one currently in ID_TO_PROBLEM_DICT and PREFIX_ID_TO_PROBLEM_LIST_DICT) and return it. Note that the way the prefix id dict works, you can get a problem with just its prefix. For example, you can get problem F435FE by asking for problem f43. It even handles the _S and _N suffixes, so you can get F435FE_N by asking for f43_N, or f4345_N, or etc. If there are multiple problems that share a prefix, this function will display a list of them and ask for user input to disambiguate.
    """
    problem_id = problem_id.upper()
    problem_list = _PREFIX_ID_TO_PROBLEM_LIST_DICT.get(problem_id, [])
    if(not problem_list):
        console.print(
            f"[b red]Error[/b red]: The problem ID requested '{problem_id}' is not defined locally. Use -w to get a problem from the web.",
            justify="center"
        )
        return(None)
    if(len(problem_list) > 1):
        print(f"There are multiple problems f{problem_id} could refer to. Here they are:\n")
        for(index, problem) in enumerate(problem_list, start=1):
            console.print(index, ": ", problem, sep="", end="")
        a = int(input("\nWhich one would you like?\n> "))
        return(problem_list[a - 1])
    return(problem_list[0])
def get_problem_from_user_string(s):
    """
    Make a problem out of a single user input string, add it to the problem dicts and the text file of user problems, and return it. Return None if the problem is invalid in some way.
    """
    intermediate = _user_input_to_triplet(s)
    if(intermediate is None):
        return(None)
    return(_process_problem_input_from_user(*intermediate))
def add_problem_to_known_problems(p: Problem, ignore_warning=False):
    """
    Add problem to the ids dict and the prefixes dict that problems uses to retrieve problems, and also add it to the file of user problems. Return the problem.

    If the problem ID already exists, do not add the problem to the dicts or the file.
    In this case, if ignore warning is on, will just return the problem (without adding it to the dicts or file).

    If ignore warning is off and the ID already exists, print an error message and return None.
    """
    if(p.identity in _ID_TO_PROBLEM_DICT):
        if(not ignore_warning):
            print(f"Could not add {p.identity} to known problems because a problem with that ID already exists.")
            return(None)
        else:
            return(p)
    else:
        _add_problem_to_both_dicts(p)
        _write_user_problem_to_file(USER_PROBS_FILE_NAME, p)
        return(p)
def print_all_local_problems():
    """
    Print the table that lists all locally available problems.
    """
    table = Table(
        title="Available Local Problems",
        title_style="bright_white",
        header_style=PROBLEM_TABLE_HEADER_COLOR,
        border_style=PROBLEM_TABLE_BORDER,
        row_styles=["", "on #1c1c1c"],
    )
    table.add_column(Text("ID", justify="center"), justify="right", style=PROBLEM_ID_COLOR)
    table.add_column(Text("Rule Cards List", justify="center"), justify="left", style=RULE_CARD_NUMS_COLOR)
    table.add_column(Text("Mode", justify="center"))
    table.add_column(Text("Comments", justify="center"))
    table.add_column(Text("Time Taken", justify="center"), justify="right")
    probs_list = list(_ID_TO_PROBLEM_DICT.values())
    probs_list.sort(key=lambda p: (p.mode, p.identity))
    for (problem_index, p) in enumerate(probs_list):
        time_pickle_seconds = _PICKLED_TIME_DICT.get(p.identity, None)
        if(time_pickle_seconds is not None):
            time_pickle_str = f"{time_pickle_seconds:,}"
        else:
            time_pickle_str = ''
        if((p.mode == 1) and STACK_EXTREME_RULE_CARDS):
            top_row = ''
            bottom_row = ''
            for rc_index in range(len(p.rc_nums_list) // 2):
                top_row += f'{p.rc_nums_list[2 * rc_index]:>2}' + ' '
                bottom_row += f'{p.rc_nums_list[2 * rc_index + 1]:>2}' + ' '
            rc_nums_str = top_row.rstrip() + '\n' + bottom_row.rstrip()
        else:
            rc_nums_str = ' '.join([f'{n:>2}' for n in p.rc_nums_list])
        table.add_row(
            p.identity,
            rc_nums_str,
            Text(MODE_NAMES[p.mode], style=STANDARD_EXTREME_NIGHTMARE_MODE_COLORS[p.mode]),
            _IDS_TO_COMMENTS_DICT.get(p.identity, ""),
            Text(time_pickle_str, style=""),
        )
        if(p.mode < 2) and (probs_list[problem_index +1].mode != p.mode):
            table.add_section()
    console.print(table, justify="center")
def get_mode_from_user(user_mode_str):
    """
    Given a mode string that is one of '0', '1', '2', or 'S', 'E', or 'N', (or the lowercase letters of those) return an integer 0, 1, or 2.
    Return None if the mode is not one of those things.
    If the mode is not one of those things and it's also not None, print an error message.

    Needed by controller to send mode to website.py.
    """
    if(user_mode_str is None):
        return(None)
    mode_int_strs = ['0', '1', '2']
    if(user_mode_str in mode_int_strs):
        return(mode_int_strs.index(user_mode_str))
    if(user_mode_str.upper() in _ACCEPTABLE_MODES):
        return(_ACCEPTABLE_MODES.index(user_mode_str.upper()))
    print(f"'{user_mode_str}' cannot be interpreted as a mode.")
    return(None)
def pre_process_p_id(p_id: str):
    """
    Given a problem ID string, process it by removing a leading # if present, capitalizing all letters, and removing whitespace. Return None if given None.

    Useful in problems.py and also in dealing with web input/output in website.py.
    """
    if(p_id is None):
        return None
    if(p_id[0] == '#'):
        p_id = p_id[1:]
    p_id = p_id.upper()
    p_id = ''.join(p_id.split())
    return(p_id)
def update_pickled_time_dict_if_necessary(s: solver.Solver):
    """
    If the solver s just solved a new problem or set a new record, note this down in the pickled time dict. Also, if any problems were deleted from the user file since the last time this happened, delete them from the pickled time dict.
    """
    previous_best = _PICKLED_TIME_DICT.get(s.problem.identity, float("inf"))
    p_ids_to_delete = [p_id for p_id in _PICKLED_TIME_DICT if not(p_id in _ID_TO_PROBLEM_DICT)]
    for p_id in p_ids_to_delete:
        del(_PICKLED_TIME_DICT[p_id])
    if(s.seconds_to_solve < previous_best):
        if(previous_best != float("inf")):
            console.print(
                f"This solver beat the previous record by {previous_best - s.seconds_to_solve:,} seconds."
            )
    if(bool(p_ids_to_delete) or (s.seconds_to_solve < previous_best)):
        print(f"Pickling time dict . . .")
        _PICKLED_TIME_DICT[s.problem.identity] = s.seconds_to_solve
        f = open(TIME_PICKLE_FILE_NAME, "wb")
        pickle.dump(_PICKLED_TIME_DICT, f, protocol=pickle.HIGHEST_PROTOCOL)
        f.close()
        print("Done pickling the time dict.")
def get_best_time(problem: Problem):
    """
    Return the number of seconds of the best recorded solver performance on this problem, or float("inf") if there is no recorded performance.
    """
    return _PICKLED_TIME_DICT.get(problem.identity, float("inf"))

_derived_nightmare_prob_tups = [(f"{p_id}_N", rc_nums) for (p_id, rc_nums) in _STANDARD_PROB_TUPS]
_derived_standard_prob_tups = [(f"{p_id}_S", rc_nums) for (p_id, rc_nums) in _NIGHTMARE_PROB_TUPS]
_NIGHTMARE_PROB_TUPS += _derived_nightmare_prob_tups
_STANDARD_PROB_TUPS += _derived_standard_prob_tups
# TODO: only the problems defined in this file now have _S and _N versions. Should change it so that all problems, including those in the user problem file, have _S and _N versions. Can do this by updating the function add_problem_to_known_problems to check if it's a nightmare/standard mode problem it's adding, and then automatically also add the standard/nightmare (respectively) version of it.
# NOTE: Any standard mode problem is now also a nightmare mode problem if just add "_N" to its problem id.
#       Also, any nightmare mode problem is a standard mode problem by adding "_S".

_standard_problems = [Problem(*(problem_tup + (STANDARD,))) for problem_tup in _STANDARD_PROB_TUPS]
_extreme_problems =  [Problem(*(problem_tup + (EXTREME,))) for problem_tup in _EXTREME_PROB_TUPS]
_nightmare_problems =  [Problem(*(problem_tup + (NIGHTMARE,))) for problem_tup in _NIGHTMARE_PROB_TUPS]
_all_problems = (
    _standard_problems +
    _extreme_problems +
    _nightmare_problems +
    _read_user_problems_from_file(USER_PROBS_FILE_NAME)
)
_problem_identities = set()
for _p in _all_problems:
    if(_p.identity in _problem_identities):
        console.print(
            f"[b red]Error[/b red]! There are multiple problems with identity '{_p.identity}'. Exiting."
        )
        exit()
    _problem_identities.add(_p.identity)
_ID_TO_PROBLEM_DICT : dict[str:Problem] = {problem.identity: problem for problem in _all_problems}
_PREFIX_ID_TO_PROBLEM_LIST_DICT = dict()
for _problem in _ID_TO_PROBLEM_DICT.values():
    _add_problem_to_prefix_id_dict(_problem)

if not os.path.isfile(TIME_PICKLE_FILE_NAME):
    time_pickle_dir = os.path.dirname(TIME_PICKLE_FILE_NAME)
    if not os.path.exists(time_pickle_dir):
        os.makedirs(time_pickle_dir)
    _PICKLED_TIME_DICT = dict()
    with open(TIME_PICKLE_FILE_NAME, 'wb') as _f:
        pickle.dump(_PICKLED_TIME_DICT, _f, protocol=pickle.HIGHEST_PROTOCOL)
with open(TIME_PICKLE_FILE_NAME, 'rb') as _f:
    _PICKLED_TIME_DICT: dict = pickle.load(_f)
# TODO: use a trie instead of the wildly inefficient prefix dict
# TODO: Put the problems and their pickles and comments and evaluations in an actual database, rather than some text files.