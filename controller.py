import pickle, os, platform, gc, argparse, git
from rich import print as rprint
from rich.text import Text
# My imports
from src.core.definitions import *
from src.core.config import *
import src.problems.website as website
import src.problems.problems as problems
from src.core import display, solver
from src.core.solver_capitulate import Solver_Capitulate
from src.core.solver_nightmare import Solver_Nightmare

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
    display_bitsets = DISPLAY_CWA_BITSETS and display_problem and (s.all_cwa_bitsets is not None)
    print("\n" if display_bitsets else "", end="")
    sd.print_table_bitsets(
        bitsets=s.all_cwa_bitsets,
        base_16=CWA_BITSETS_BASE_16,
        active=display_bitsets
    )
    print()
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
        sd.print_all_possible_answers(
            full_cwa,
            "\nAll Possible Answers",
            permutation_order=P_ORDER,
            active=display_problem
        )
        print("\n" if (DISPLAY_CWA_BITSETS and display_problem and (s.all_cwa_bitsets is not None)) else "", end="")
        sd.print_table_bitsets(
            bitsets=s.all_cwa_bitsets,
            base_16=CWA_BITSETS_BASE_16,
            active=((DISPLAY_CWA_BITSETS and display_problem and (s.all_cwa_bitsets is not None)))
        )
        print()
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

def make_solver(problem: Problem):
    """ Makes a solver and solve()s the problem. """
    # if(args.capitulate): # args.capitulate should really be passed in as an argument to this function. At any ratd, capitulate solver isn't working currently anyway.
        # s = Solver_Capitulate(problem)
    if(problem.mode == NIGHTMARE):
        s = Solver_Nightmare(problem)
    else:
        s = solver.Solver(problem)
    sd = display.Solver_Displayer(s)
    sd.print_problem(s.rcs_list, s.problem, active=DISPLAY)
    if(not(s.full_cwas_list)):
        rprint(
            f"\n[bold red]Error[/bold red]: This is an invalid problem which has no solutions. Check that the problem is specified correctly, and check the relevant rule cards in rules.py."
        )
        console.print(
            "Reminder that any valid rule combination must obey two rules:\n  1. There is exactly one proposal that satisfies them all.\n  2. Each rule eliminates at least one possibility that is not eliminated by any other rule.",
            highlight=False
        )
        rprint("Rule card numbers list: ", s.problem.rc_nums_list, end='')
        print("Exiting.")
        exit()
    full_cwa = s.full_cwa_list_from_game_state(s.initial_game_state)
    title = "\nAll Possible Answers"
    sd.print_all_possible_answers(full_cwa, title, permutation_order=P_ORDER, active=DISPLAY)
    display_bitsets = DISPLAY and DISPLAY_CWA_BITSETS and (s.all_cwa_bitsets is not None)
    print("\n" if display_bitsets else "", end="")
    sd.print_table_bitsets(s.all_cwa_bitsets, base_16=CWA_BITSETS_BASE_16, active=display_bitsets)
    console.print(
        "[b #af87ff]NOTE[/b #af87ff]: If you think this problem will take a long time to solve, be sure to enable the 'Prevent your Mac from automatically sleeping when the display is off' system setting (or equivalent for your computer).",
        highlight=False
    )
    print("\nSolving . . .")
    s.solve()
    s.post_solve_printing()
    return(s)

def pickle_solver(problem: Problem, pickle_entire=False, force_overwrite=False):
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
    console.print(Text.assemble("\nPickling ", display.get_filename_text(f_name), ". . ."))
    if(not(pickle_entire)):
        s.filter_cache()
    git_hash = git.Repo(search_parent_directories=True).head.object.hexsha
    git_message = git.Repo(search_parent_directories=True).head.object.message
    s.git_hash = git_hash
    s.git_message = git_message
    pickle.dump(s, f, protocol=pickle.HIGHEST_PROTOCOL)
    f.close()
    console.print("Done.")
    problems.update_pickled_time_dict_if_necessary(s)
    return(s)

def get_or_make_solver(
        problem: Problem,
        pickle_entire=False,
        force_overwrite=True,
        no_pickles=False
    ) -> solver.Solver :
    """
    Given a `problem`, if the corresponding solver has been pickled, gets it, otherwise, makes it, pickles it.
    If pickle_entire is True, pickles the entire solver; otherwise, only pickles the parts of the evaluations cache needed to play the game perfectly.
    If force_overwrite is true, makes solver and writes it to file regardless of whether or not it existed before.
    If no_pickles is True, does not interact with pickles in any way. Makes solver from scratch, and does not pickle it nor change any existing pickles. Precludes force_overwrite and pickle_entire.
    Returns a tuple (solver, a bool indicating whether or not the solver was made from scratch)
    """
    # display.cprint_if_active(DISPLAY, f"\nReturning solver for problem: {problem.identity}")
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
                    f"Problem has been solved; retrieving solver from file. . ."
                )
                s = unpickle_solver(problem.identity)
                made_from_scratch = False
            else:
                display.cprint_if_active(
                    DISPLAY,
                    "Problem has been solved, but will overwrite the solver file."
                )
                s = pickle_solver(problem, pickle_entire=pickle_entire, force_overwrite=force_overwrite)
                made_from_scratch = True
        else:
            display.cprint_if_active(
                DISPLAY,
                f"Problem has not been solved. Solving. If this problem has 20+ answers, this may take some time . . ."
            )
            s = pickle_solver(problem, pickle_entire=pickle_entire)
            made_from_scratch = True
    if(DISABLE_GC):
        gc.enable()
    return((s, made_from_scratch))

def display_problem_solution(
    problem: Problem,
    pickle_entire=False,
    force_overwrite=False,
    no_pickles=False
):
    """
    Given a `problem`, gets or makes a solver for it (see get_or_make_solver), then prints the best move tree with the options that are currently set (SHOW_COMBOS_IN_TREE).
    """
    (s, made_from_scatch) = get_or_make_solver(problem, pickle_entire, force_overwrite, no_pickles)
    display_solution_from_solver(s, display_problem=not(made_from_scatch))
def play(problem: Problem, pickle_entire=False, force_overwrite=False, no_pickles=False):
    """
    Given a `problem`, gets or makes a solver for it (see get_or_make_solver), then plays that problem, prompting the user for answers to its queries. Affected by PRINT_COMBOS option.
    """
    (s, made_from_scatch) = get_or_make_solver(problem, pickle_entire, force_overwrite, no_pickles)
    play_from_solver(s, display_problem=not(made_from_scatch))

def get_web_problem(p_id, raw_mode, level, num_verifiers):
    """
    A convenience function for getting a web problem. If p_id is not None, gets a problem from the web with that ID. If it is None, gets an arbitrary problem with given mode, level of difficulty, and num_verifiers. Those are randomly chosen if they are None. Returns the problem, or None if there was a problem getting the problem.
    """
    if(p_id is not None):
        p = website.get_web_problem_from_id(p_id, print_action=True)
    else:
        mode = problems.get_mode_from_user(raw_mode)
        p = website.get_web_problem_from_mode_difficulty_num_vs(mode, level, num_verifiers, print_action=True)
    return(p)
def get_requested_problem(
        p_id=None,
        web=False,
        mode=None,
        level=None,
        verifiers=None,
        new_problem=None
    ) -> Problem:
    """
    Given arguments directly from the argument parser, returns the Problem that corresponds to those arguments, or displays an error message and exits if there isn't a corresponding Problem.
    """
    if(web):
        p = get_web_problem(p_id, mode, level, verifiers)
        if(p is None):
            console.print(f"Error. Could not successfully retrieve the problem from the website. Exiting.")
            exit()
            # TODO: consider not adding all web problems to known problems
        problems.add_problem_to_known_problems(p, ignore_warning=True)
        return(p)
    if(new_problem): # if no -n, this is None. If -n but no args, this is an empty list.
        p = problems.get_problem_from_user_string(' '.join(new_problem))
        if(p is None):
            console.print(
                "Here's an example of a valid problem input: 'python controller.py -n -d Fire 4 9 11 12 N'. The modes are (S)tandard, (E)xtreme, and (N)ightmare. Note that if no mode is included, standard mode will be assumed. Exiting."
            )
            exit()
        return(p)
    if(p_id is None):
        # no problem specified. Just display all problems and exit
        problems.print_all_local_problems()
        exit()
    p = problems.get_local_problem_by_id(p_id)
    if(p is None):
        print()
        problems.print_all_local_problems()
        exit()
    return(p)
def make_parser():
    """ Controls the program arguments and help display. """
    parser = argparse.ArgumentParser(
        description="Run this program without any arguments to see a list of available local problems. Then, for a given problem, can choose to display the best move tree or play it, or get a new problem from the web (by ID or by parameters), or make a new problem directly from user input. See arguments for more details."
    )
    parser.add_argument(
        "prob_id",
        type=str,
        nargs="?",
        default=None,
        help="Specify the problem id. Prefixes are fine. If neither -d nor -p are chosen, then it will simply make the solver with no_pickles turned on. Do: python controller.py <-d> <-p> <<-np> or <-fo> or <<-c> or <--from_file>> prob_id. Example: 'python controller.py -d f43'. Run without any arguments to see a list of available local problems.",
    )
    parser.add_argument(
        "--display", "-d",
        action="store_true",
        help="Display the best move tree. NOTE: if the tree is too big to fit on screen, you can pipe the result of this program into less -SR -#3. Example: 'python controller.py -d f5x | less -SR -# 3' The program less, with the -S option, allows you to scroll horizontally. -R tells it to honor the terminal color escape sequences. The -# n option means that each right/left arrow press scrolls n lines."
    )
    parser.add_argument("--play", "-p", action="store_true", help="Play the problem.")
    parser.add_argument("--no_pickles", "-np", action="store_true", help="No pickles.")
    parser.add_argument("--force_overwrite", "-fo", action="store_true", help="Force overwrite pickles.")
    parser.add_argument(
        "--from_file",
        action="store_true",
        help="Get solver from file, interpreting prob_id as a filename."
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
        help="Get a problem straight from turingmachine.info. If the positional argument prob_id is given, will get the problem with that ID; otherwise will get a problem from the optional -m (mode, S, E, or N, or 0, 1, or 2), -l (level of difficulty, 0, 1, or 2), and -v (number verifiers: 4, 5, or 6). If any of the mode, difficulty, or number of verifiers are not chosen, the computer will choose them 'randomly'. Examples: 'python controller.py -d -w FWW23A' or 'python controller.py -d -w -m N -l 2 -v 4' or 'python controller.py -w -d'."
    )
    parser.add_argument(
        "--mode", "-m",
        help="Only has an effect when used with -w to get a problem from the web. Specify the mode (S, E, or N. Or 0, 1, or 2) of the problem obtained from turingmachine.info. If unspecified, will be chosen randomly."
    )
    parser.add_argument(
        "--level", "-l",
        type=int,
        help="Only has an effect when used with -w to get a problem from the web. Specify the level of difficulty (0, 1, or 2) of the problem obtained from turingmachine.info. If unspecified, will be chosen randomly."
    )
    parser.add_argument(
        "--verifiers", "-v",
        type=int,
        help="Only has an effect when used with -w to get a problem from the web. Specify the number of verifiers (4, 5, or 6) of the problem obtained from turingmachine.info. If unspecified, will be chosen randomly."
    )
    return parser
def do_two_funcs(do_func_1: bool, func_1: callable, do_func_2: bool, func_2: callable, *args, **kwargs):
    """
    Does `func_1` and `func_2` on `*args` and `**kwargs` (they both get the same args) depending on the values of `do_func_1` and `do_func_2`
    """
    if(do_func_1):
        func_1(*args, **kwargs)
    if(do_func_2):
        func_2(*args, **kwargs)

# For Testing purposes
def unpickle_solver_from_f_name(f_name):
    console.print(Text.assemble("\nUnpickling ", display.get_filename_text(f_name), ". . ."))
    f = open(f_name, 'rb')
    s: solver.Solver = pickle.load(f)
    f.close()
    print("Done.")
    sd = display.Solver_Displayer(s)
    # if(hasattr(s, "git_hash")):
    #     console.print(f"This solver was created in git commit {s.git_hash}.")
    #     if(hasattr(s, "git_message")):
    #         console.print(f"Commit message: {s.git_message}", end="")
    #     else:
    #         print("Commit message was not recorded.")
    # else:
    #     print("This solver did not record the git commit it was created in.")
    console.print(Text.assemble(f"Seconds to solve: ", (f"{s.seconds_to_solve:,}", COLOR_OF_TIME)))
    sd.print_eval_cache_size()
    return(s)

def display_problem_solution_from_file(f_name):
    s = unpickle_solver_from_f_name(f_name)
    display_solution_from_solver(s)
def play_from_file(f_name):
    s = unpickle_solver_from_f_name(f_name)
    play_from_solver(s)

# Main ways to use:
#   1) play(problem, pickle_entire, force_overwrite, no_pickles)
#   2) display_problem_solution(problem, pickle_entire, force_overwrite, no_pickles)
#   3) get_or_make_solver(problem, pickle_entire, force_overwrite, no_pickles) mainly for debugging/inspection.
# NOTE: If a tree is too big to fit on screen of terminal, can use the following command:
# python controller.py <problem_name_prefix>| less -SR -# 3

# less, with the -S option, allows you to scroll horizontally. -R tells it to honor the terminal color escape sequences. The -# n option means that each right/left arrow key press scrolls n lines. Can view full trees with that.

if(__name__ == "__main__"):
    try:
        console.print("", style="green", end="")
        # console.print(f"Using {platform.python_implementation()}.", justify="center")
        parser = make_parser()
        args = parser.parse_args()

        if(args.from_file):
            do_two_funcs(
                args.display,
                display_problem_solution_from_file,
                args.play,
                play_from_file,
                f_name=args.prob_id
            )
            if not(args.play or args.display):
                s = unpickle_solver_from_f_name(args.prob_id)
            exit()
        problem = get_requested_problem(
            args.prob_id,
            args.web,
            args.mode,
            args.level,
            args.verifiers,
            args.new_problem
        )
        args.no_pickles = True if (args.capitulate) else args.no_pickles # capitulate turns on no pickles
        do_two_funcs(
            args.display,
            display_problem_solution,
            args.play,
            play,
            problem,
            no_pickles=args.no_pickles,
            force_overwrite=args.force_overwrite
        )
        if(not(args.play or args.display)):
            s = get_or_make_solver(
                problem, no_pickles=not(args.force_overwrite), force_overwrite=args.force_overwrite
            )[0]
    except KeyboardInterrupt:
        console.print("\nBaii")
        exit()

    # breakpoint here for debugging purposes.
    # To use in REPL: do:
    #   from controller import *
    #   problem = get_requested_problem(p_id=<ID HERE>)
    #   s = get_or_make_solver(problem, no_pickles=True, force_overwrite=False)[0]
    # Then use the solver displayer below to examine.
    # Use the below for testing/debugging purposes
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