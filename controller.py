import pickle, os, platform, gc, argparse, git
from rich import print as rprint
# from rich.text import Text
from core.definitions import *
from core.config import *
from core.problems import get_problem_by_id as get_local_problem
import core.problems
from core import display, solver
from core.solver_capitulate import Solver_Capitulate
from core.solver_nightmare import Solver_Nightmare
import website
# https://stackoverflow.com/questions/14989858/get-the-current-git-hash-in-a-python-script

def update_query_history(q_history, move, new_round: bool, result: bool):
    if(new_round):
        q_history.append([move[0]])
    q_history[-1].append((move[1], result))
    if(move[0] != q_history[-1][0]):
        print("ERROR! The current move's proposal does not match up with the proposal used this round, and so this should have been a new round, but it isn't.")
        print("Query history:")
        for (round_num, round_info) in enumerate(q_history, start=1):
            print(f"{round_num}: {round_info}")
        print(f"Move: {move}")
        exit()

def play_from_solver(s: solver.Solver, display_problem = True):
    """
    This function assumes that the solver s has already been solved.
    If display_problem is off, will not display the problem
    """
    sd = display.Solver_Displayer(s)
    current_gs = s.initial_game_state
    full_cwa = s.full_cwa_list_from_game_state(current_gs)
    current_score = (0, 0) # current_round_num, total_queries_made
    query_history = [] # each round is: [proposal, (verifier, result), . . .]
    sd.print_problem(s.rcs_list, s.problem, active=display_problem)
    title = "\nAll Possible Answers"
    sd.print_all_possible_answers(full_cwa, title, permutation_order=P_ORDER, active=display_problem)
    while not(solver.one_answer_left(s.full_cwas_list, current_gs.cwa_set)):
        (best_move, mcost, gs_tup, expected_cost) = s.get_move_mcost_gs_ncost_from_cache(
            current_gs
        )
        full_cwa = s.full_cwa_list_from_game_state(current_gs)
        expected_total_score = add_tups(current_score, expected_cost)
        if(current_score > (0, 0)):
            # only print this table after having made some queries, since already printed it at start.
            sd.print_all_possible_answers(
                full_cwa, "Remaining Combos", permutation_order=P_ORDER, active=PRINT_COMBOS, verifier_to_sort_by=verifier_to_sort_by
            )
        current_score = add_tups(current_score, mcost)
        query_this_round = 1 if (mcost[0]) else current_gs.num_queries_this_round + 1
        display.display_new_round(current_score[0], query_this_round, best_move)
        result = display.conduct_query(
            best_move,
            expected_total_score,
            query_this_round,
            current_score[1]
        )
        verifier_to_sort_by = best_move[1]
        current_gs = gs_tup[result]
        update_query_history(query_history, best_move, mcost[0], result)
    # Found an answer
    v_to_sort_by = None if(current_score == (0, 0)) else best_move[1]
    sd.end_play_display(current_gs, v_to_sort_by, query_history, current_score)

def display_solution_from_solver(s: solver.Solver, display_problem = True):
    """
    This function assumes that the solver s has already been solved.
    """
    sd = display.Solver_Displayer(s)
    if(display_problem):
        sd.print_problem(s.rcs_list, s.problem, active=True)
    full_cwa = s.full_cwa_list_from_game_state(s.initial_game_state)
    if(solver.one_answer_left(s.full_cwas_list, s.initial_game_state.cwa_set)):
        sd.print_all_possible_answers(full_cwa, "\nANSWER", permutation_order=P_ORDER)
    else:
        if(display_problem):
            sd.print_all_possible_answers(full_cwa, "\nAll Possible Answers", permutation_order=P_ORDER)
        display.print_best_move_tree(s.initial_game_state, SHOW_COMBOS_IN_TREE, solver=s)

def unpickle_solver(identity):
    f_name = f_name_from_id(identity)
    return(unpickle_solver_from_f_name(f_name))

def f_name_from_id(identity):
    """
    identity is a string that is the ID of a problem from the website, without the '#' symbol.
    Stored in f"{PICKLE_DIRECTORY}/{identity}.bin"
    """
    if(identity[0] == '#'):
        identity = identity[1:]
    f_name = f"{PICKLE_DIRECTORY}/{identity}.bin"
    return(f_name)

def get_relevant_parts_cache(s:solver.Solver):
    """
    Given a cache and an initial_game_state, returns a new cache that only contains the initial game state and any states that are reachable from it in the best move tree.
    """
    if(s.evaluations_cache is None):
        return(None)
    new_evaluations_cache = dict()
    stack : list[Game_State] = [s.initial_game_state]
    while(stack):
        curr_gs = stack.pop()
        if((curr_gs in s.evaluations_cache) and (curr_gs not in new_evaluations_cache) and
            (not solver.one_answer_left(s.full_cwas_list, curr_gs.cwa_set))):
            curr_gs_modified_answer = s.get_move_mcost_gs_ncost_from_cache(curr_gs)
            curr_gs_raw_answer = s.evaluations_cache[curr_gs]
            (curr_gs_false_result, curr_gs_true_result) = curr_gs_modified_answer[2]
            new_evaluations_cache[curr_gs] = curr_gs_raw_answer
            stack.append(curr_gs_false_result)
            stack.append(curr_gs_true_result)
    return(new_evaluations_cache)

def make_solver(problem: Problem):
    """ Makes a solver and solve()s the problem. """
    if(args.capitulate):
        s = Solver_Capitulate(problem)
    elif(problem.mode == NIGHTMARE):
        s = Solver_Nightmare(problem)
    else:
        s = solver.Solver(problem)
    sd = display.Solver_Displayer(s)
    sd.print_problem(s.rcs_list, s.problem, active=DISPLAY)
    if(not(s.full_cwas_list)):
        rprint(f"\n[bold red]Error[/bold red]: This is an invalid problem which has no solutions. Check that the problem is specified correctly, and check the relevant rule cards in rules.py.")
        console.print("Reminder that any rule combination must obey two rules:\n  1. There is exactly one proposal that satisfies them all.\n  2. Each rule eliminates at least one possibility that is not eliminated by any other rule.", highlight=False)
        rprint("\nRule card numbers list: ", s.problem.rc_nums_list, end='')
        print("Exiting.")
        exit()
    full_cwa = s.full_cwa_list_from_game_state(s.initial_game_state)
    title = "\nAll Possible Answers"
    sd.print_all_possible_answers(full_cwa, title, permutation_order=P_ORDER, active=DISPLAY)
    print("\nSolving . . .")
    s.solve()
    s.post_solve_printing()
    return(s)

def pickle_solver(problem, pickle_entire=False, force_overwrite=False):
    """
    Given a Problem named tuple, if the solver for it hasn't already been pickled, makes it and pickles it; otherwise it does nothing. 
    If pickle_entire is True, pickles the entire solver. If it's false, sets the solver's evaluation cache to only the parts accessed during a best game (all that is needed to display tree and play game), so that unpickling it is much faster.
    If force_overwrite is true, then it remakes the solver regardless of whether the corresponding file exists, and overwrites the file if it does exist.
    """
    f_name = f_name_from_id(problem.identity)
    if(not os.path.exists(PICKLE_DIRECTORY)):
        os.makedirs(PICKLE_DIRECTORY)
    if(os.path.exists(f_name) and not force_overwrite):
        print(f"Asked to pickle {f_name}, but it already exists. Returning None.")
        return
    s = make_solver(problem)
    f = open(f_name, 'wb') # open mode write binary. Needed for pickling to work.
    console.print(f"\nPickling {f_name} . . .", justify="center")
    if(not(pickle_entire)):
        new_evaluations_cache = get_relevant_parts_cache(s)
        s.evaluations_cache = new_evaluations_cache
    git_hash = git.Repo(search_parent_directories=True).head.object.hexsha
    git_message = git.Repo(search_parent_directories=True).head.object.message
    s.git_hash = git_hash
    s.git_message = git_message
    pickle.dump(s, f, protocol=pickle.HIGHEST_PROTOCOL)
    f.close()
    console.print("Done", justify="center")
    core.problems.update_pickled_time_dict_if_necessary(s)
    return(s)

def get_or_make_solver(
        problem_id: str,
        pickle_entire=False,
        force_overwrite=True,
        no_pickles=False
    ):
    """
    Given a problem id (see problems.py), if the solver is in file, gets it. If it isn't in file, makes it, pickles it.
    If pickle_entire is True, pickles the entire solver; otherwise, only pickles the parts of the evaluations cache needed to play the game perfectly.
    If force_overwrite is true, makes solver and writes it to file regardless of whether or not it existed before.
    If no_pickles is True, does not interact with pickles in any way. Makes solver from scratch, and does not pickle it nor change any existing pickles. Precludes force_overwrite and pickle_entire.
    Returns a tuple (solver, a bool indicating whether or not the solver was made from scratch)
    """
    problem = get_local_problem(problem_id)
    if(problem is None):
        print()
        core.problems.print_all_local_problems()
        exit()
    display.cprint_if_active(DISPLAY, f"\nReturning solver for problem: {problem.identity}")
    if(DISABLE_GC):
        gc.disable()
        gc.collect()
    if(no_pickles):
        display.cprint_if_active(DISPLAY, "No pickles. Making solver from scratch.")
        s = make_solver(problem)
        made_from_scratch = True
    else:
        f_name = f_name_from_id(problem.identity)
        if(os.path.exists(f_name)):
            if(not force_overwrite):
                display.cprint_if_active(
                    DISPLAY,
                    f"Problem ID: {problem.identity} has been solved; retrieving solver from file. . ."
                )
                s = unpickle_solver(problem.identity)
                made_from_scratch = False
            else:
                display.cprint_if_active(
                    DISPLAY,
                    "This problem has been solved, but will overwrite the solver file."
                )
                s = pickle_solver(problem, pickle_entire=pickle_entire, force_overwrite=force_overwrite)
                made_from_scratch = True
        else:
            display.cprint_if_active(
                DISPLAY,
                f"Problem ID: {problem.identity} has not been solved. Solving. If this problem has 20+ unique answers, this may take some time . . ."
            )
            s = pickle_solver(problem, pickle_entire=pickle_entire)
            made_from_scratch = True
    if(DISABLE_GC):
        gc.enable()
    return((s, made_from_scratch))

def display_problem_solution(
    problem_id: str,
    pickle_entire=False,
    force_overwrite=False,
    no_pickles=False
):
    """
    Given a problem id (see problems.py), gets or makes a solver for it (see get_or_make_solver), then prints the best move tree with the options that are currently set (SHOW_COMBOS_IN_TREE).
    """
    (s, made_from_scatch) = get_or_make_solver(problem_id, pickle_entire, force_overwrite, no_pickles)
    display_solution_from_solver(s, display_problem=not(made_from_scatch))
def play(problem_id: str, pickle_entire=False, force_overwrite=False, no_pickles=False):
    """
    Given a problem id (see problems.py), gets or makes a solver for it (see get_or_make_solver), then plays that problem, prompting the user for answers to its queries. Affected by PRINT_COMBOS option.
    """
    (s, made_from_scatch) = get_or_make_solver(problem_id, pickle_entire, force_overwrite, no_pickles)
    play_from_solver(s, display_problem=not(made_from_scatch))

def get_web_problem(p_id, raw_mode, level, num_verifiers):
    """
    A convenience function for getting a web problem. If p_id is not None, gets a problem from the web with that ID. If it is None, gets an arbitrary problem with given mode, level of difficulty, and num_verifiers. Those are randomly chosen if they are None. Returns the problem, or None if there was a problem getting the problem.
    """
    if(p_id is not None):
        p = website.get_web_problem_from_id(p_id, print_action=True)
    else:
        mode = core.problems.get_mode_from_user(raw_mode)
        p = website.get_web_problem_from_mode_difficulty_num_vs(mode, level, num_verifiers, print_action=True)
    return(p)

# For Testing purposes
def unpickle_solver_from_f_name(f_name):
    print(f"\nUnpickling {f_name}.")
    f = open(f_name, 'rb')
    s: solver.Solver = pickle.load(f)
    f.close()
    print("Done.")
    sd = display.Solver_Displayer(s)
    console.print(f"This solver originally took {s.seconds_to_solve:,} seconds to solve.")
    if(hasattr(s, "git_hash")):
        console.print(f"This solver was created in git commit {s.git_hash}.")
        if(hasattr(s, "git_message")):
            console.print(f"Commit message: {s.git_message}", end="")
        else:
            print("Commit message was not recorded.")
    else:
        print("This solver did not record the git commit it was created in.")
    sd.print_eval_cache_size()
    return(s)
def display_problem_solution_from_file(f_name):
    s = unpickle_solver_from_f_name(f_name)
    display_solution_from_solver(s)
def play_from_file(f_name):
    s = unpickle_solver_from_f_name(f_name)
    play_from_solver(s)

# Make problems (see above. Get from www.turingmachine.info)
#   1) play(problem_id, pickle_entire, force_overwrite, no_pickles)
#   2) display_problem_solution(problem_id, pickle_entire, force_overwrite, no_pickles)
#   3) get_or_make_solver(problem_id, pickle_entire, force_overwrite, no_pickles) mainly for debugging/inspection.
# NOTE: If a tree is too big to fit on screen of terminal, can use the following command:
# python controller.py <problem_name_prefix>| less -SR -# 3

# less, with the -S option, allows you to scroll horizontally. -R tells it to honor the terminal color escape sequences. The -# n option means that each right/left arrow key press scrolls n lines. Can view full trees with that.


# Profiling/Interactive Debugging
# s = get_or_make_solver(f5x, no_pickles=True)[0] # ~3 minutes.
# s = get_or_make_solver(f43, no_pickles=True)[0] # 3,413 seconds.

# Use the below 2 lines to get interactive debugging started
# sd = display.Solver_Displayer(s)
# (gs_false, gs_true) = sd.print_evaluations_cache_info(s.initital_game_state)


if(__name__ == "__main__"):
    console.print(" ", style="green")
    console.print(f"Using {platform.python_implementation()}.", justify="center")
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "prob_id",
        type=str,
        nargs="?",
        default=None,
        help="Specify the problem id. Prefixes are fine. If neither -d nor -p are chosen, then it will simply make the solver with no_pickles turned on. Example usage: python controller.py <-d> <-p> <<-np> or <-fo> or <<-c> or <--from_file>> prob_id. Run without any arguments to see a list of available problems.",
    )
    parser.add_argument("--display", "-d", action="store_true", help="Display the tree.")
    parser.add_argument("--play", "-p", action="store_true", help="Play the problem.")
    parser.add_argument("--no_pickles", "-np", action="store_true", help="No pickles.")
    parser.add_argument("--force_overwrite", "-fo", action="store_true", help="Force overwrite pickles.")
    parser.add_argument(
        "--from_file",
        action="store_true",
        help="Get solver from file, using the main argument as a filename."
    )
    parser.add_argument(
        "--capitulate","-c",
        action="store_true",
        help="Give up on being perfect. Choosing this turns on --no_pickles."
    )
    parser.add_argument(
        "--new_problem", "-n",
        nargs="*",
        help="Create a problem from user input, rather than specifying an already-existing problem. Syntax: p_id rc_num rc_num ... mode, which is one of S, E, or N. If no mode, S will be assumed. Here's an example of a valid problem input: 'python controller.py -n Fire 4 9 11 12 N -d'"
    )
    parser.add_argument(
        "--web", "-w",
        action="store_true",
        help="Get a problem straight from turingmachine.info. If the positional argument prob_id is given, will get the problem with that ID; otherwise will get a problem from the optional -m (mode, S, E, or N, or 0, 1, or 2), -l (level, 0, 1, or 2), and -v (number verifiers: 4, 5, or 6). If any of the mode, difficulty, or number of verifiers are not chosen, the computer will choose them 'randomly'. Examples: 'python controller.py -d -w FWW23A' or 'python controller.py -d -w -m N -l 2 -v 4'"
    )
    parser.add_argument(
        "--mode", "-m",
        help="Only has an effect when used with -w to get a problem from the web. Specify the mode of problems (S, E, or N. Or 0, 1, or 2) obtained from turingmachine.info. If unspecified, will be chosen randomly."
    )
    parser.add_argument(
        "--level", "-l",
        type=int,
        help="Only has an effect when used with -w to get a problem from the web. Specify the level of difficulty of problems (0, 1, or 2) obtained from turingmachine.info. If unspecified, will be chosen randomly."
    )
    parser.add_argument(
        "--verifiers", "-v",
        type=int,
        help="Only has an effect when used with -w to get a problem from the web. Specify the number of verifiers (4, 5, or 6) obtained from turingmachine.info. If unspecified, will be chosen randomly."
    )
    args = parser.parse_args()

    if(args.web):
        p = get_web_problem(args.prob_id, args.mode, args.level, args.verifiers)
        if(p is None):
            console.print(f"Error. Could not successfully retrieve the problem from the website. Exiting.")
            exit()
        core.problems.add_problem_to_known_problems(p, ignore_warning=True)
        args.prob_id = p.identity
    elif(args.new_problem): # if no -n, this is None. If -n but no args, this is an empty list.
        p = core.problems.get_problem_from_user_string(' '.join(args.new_problem))
        if(p is None):
            print(
                "Here's an example of a valid problem input: 'python controller.py -n -d Fire 4 9 11 12 N'. The modes are (S)tandard, (E)xtreme, and (N)ightmare. Note that if no mode is included, standard mode will be assumed. Exiting."
            )
            exit()
        args.prob_id = p.identity
    if(args.prob_id is None):
        # no problem specified. Perhaps display all problems?
        core.problems.print_all_local_problems()
        exit()
    # now have a valid problem (or file) specified.
    args.no_pickles = True if (args.capitulate) else args.no_pickles # capitulate turns on no pickles
    if(args.from_file):
        if(args.play):
            play_from_file(args.prob_id)
        if(args.display):
            display_problem_solution_from_file(args.prob_id)
        exit()
    if(args.display):
        display_problem_solution(
            args.prob_id,
            no_pickles=args.no_pickles,
            force_overwrite=args.force_overwrite
        )
    if(args.play):
        play(
            args.prob_id,
            no_pickles=args.no_pickles,
            force_overwrite=args.force_overwrite
        )
    if(not(args.play or args.display)):
        s = get_or_make_solver(
            args.prob_id, no_pickles=not(args.force_overwrite), force_overwrite=args.force_overwrite
        )[0]

    # breakpoint here for debugging purposes.
    # Use the below in REPL for testing/debugging purposes
    # sd = display.Solver_Displayer(s)
    # sd.print_useful_qs_dict_info(
    #     s.qs_dict,
    #     s.initial_game_state.cwa_set
    #     verifier_index=None,          # set to None for all verifiers
    #     proposals_to_examine=None,   # set to None for all proposals
    #     see_all_combos=True
    # )
    # console.rule()
    # (gs_false, gs_true) = sd.print_evaluations_cache_info(s.initial_game_state)