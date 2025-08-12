import rules, display, solver
from problems import get_problem_by_id as get
from definitions import *
import pickle, os, sys, platform


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

def play_from_solver(s, display_problem = True):
    """
    This function assumes that the solver s has already been solved.
    If display_problem is off, will not display the problem
    """
    (rcs_list, initial_game_state) = (s.rcs_list, s.initial_game_state)
    current_gs = initial_game_state
    # NOTE: below line for display purposes only
    rules.max_rule_name_length = max([max([len(r.name) for r in rc]) for rc in rcs_list])
    full_cwa = s.full_cwa_from_game_state(current_gs)
    current_round_num = 0
    total_queries_made = 0
    query_history = [] # each round is: [proposal, (verifier, result), . . .]
    if(display_problem):
        display.print_problem(rcs_list, s.problem, active=True)
        display.print_all_possible_answers(full_cwa, s.problem.mode, "\nAll Possible Answers", permutation_order=True)
    while(len(solver.fset_answers_from_cwa_iterable(current_gs.fset_cwa_indexes_remaining)) > 1):
        (best_move_tup, mcost_tup, gs_tup, expected_cost_tup) = s.evaluations_cache[current_gs]
        full_cwa = s.full_cwa_from_game_state(current_gs)
        expected_winning_round = current_round_num + expected_cost_tup[0]
        expected_total_queries = total_queries_made + expected_cost_tup[1]
        if(total_queries_made > 0):
            # only print this table after having made some queries, since already printed it at start.
            display.print_all_possible_answers(
                full_cwa, s.problem.mode, "\nRemaining Combos", permutation_order=True, active=PRINT_COMBOS, use_round_indent=True, verifier_to_sort_by=verifier_to_sort_by
            )
        current_round_num += mcost_tup[0]
        total_queries_made += mcost_tup[1]
        query_this_round = 1 if (mcost_tup[0]) else current_gs.num_queries_this_round + 1
        display.display_query_num_info(current_round_num, query_this_round, total_queries_made, mcost_tup[0], best_move_tup[0])
        result = display.conduct_query(
            best_move_tup,
            expected_winning_round,
            expected_total_queries,
        )
        verifier_to_sort_by = best_move_tup[1]
        current_gs = gs_tup[result]
        update_query_history(query_history, best_move_tup, mcost_tup[0], result)
    # Found an answer
    full_cwa = s.full_cwa_from_game_state(current_gs)
    print(f"\nFinal Score: Rounds: {current_round_num}. Queries: {total_queries_made}.")
    display.display_query_history(query_history, len(rcs_list))
    display.print_all_possible_answers(full_cwa, s.problem.mode, "\nANSWER", permutation_order=True, verifier_to_sort_by=best_move_tup[1])

def display_solution_from_solver(s, display_problem = True):
    """
    This function assumes that the solver s has already been solved.
    """
    rules.max_rule_name_length = max([max([len(r.name) for r in rc]) for rc in s.rcs_list])
    if(display_problem):
        display.print_problem(s.rcs_list, s.problem, active=True)
    full_cwa = s.full_cwa_from_game_state(s.initial_game_state)
    if(len(solver.fset_answers_from_cwa_iterable(s.initial_game_state.fset_cwa_indexes_remaining)) == 1):
        display.print_all_possible_answers(full_cwa, s.problem.mode, "\nANSWER", permutation_order=True)
    else:
        if(display_problem):
            display.print_all_possible_answers(full_cwa, s.problem.mode, "\nAll Possible Answers", permutation_order=True)
        display.print_best_move_tree(s.initial_game_state, SHOW_COMBOS_IN_TREE, solver=s)
        # TODO: uncomment when done with adding the correct functions to display (see todo.txt optional)
        # display.print_multi_move_tree(initial_game_state, SHOW_COMBOS_IN_TREE, solver=s)

def unpickle_solver(identity):
    f_name = f_name_from_id(identity)
    print(f"\nUnpickling {f_name}.")
    f = open(f_name, 'rb')
    s = pickle.load(f)
    rules.max_rule_name_length = max([max([len(r.name) for r in rc]) for rc in s.rcs_list])
    f.close()
    print("Done.")
    return(s)

def f_name_from_id(identity):
    """
    identity is a string that is the ID of a problem from the website, without the '#' symbol.
    Stored in f"{PICKLE_DIRECTORY}/{identity}.bin"
    """
    if(identity[0] == '#'):
        identity = identity[1:]
    f_name = f"{PICKLE_DIRECTORY}/{identity}.bin"
    return(f_name)

def get_relevant_parts_cache(evaluations_cache, initial_game_state):
    """
    Given a cache and an initial_game_state, returns a new cache that only contains the initial game state and any states that are reachable from it in the best move tree. Note that leaf nodes, which only have one possible answer, are not included in either cache (this implies that if the initial game state takes zero queries to solve, both caches will be empty).
    """
    if(evaluations_cache is None):
        return(None)
    new_evaluations_cache = dict()
    stack = [initial_game_state]
    while(stack):
        curr_gs = stack.pop()
        if((curr_gs in evaluations_cache) and not (curr_gs in new_evaluations_cache)):
            curr_gs_answer = evaluations_cache[curr_gs]
            (curr_gs_false_result, curr_gs_true_result) = curr_gs_answer[2]
            new_evaluations_cache[curr_gs] = curr_gs_answer
            stack.append(curr_gs_false_result)
            stack.append(curr_gs_true_result)
    return(new_evaluations_cache)

def make_solver(problem):
    s = solver.Solver(problem)
    rules.max_rule_name_length = max([max([len(r.name) for r in rc]) for rc in s.rcs_list])
    display.print_problem(s.rcs_list, s.problem, active=True)
    full_cwa = s.full_cwa_from_game_state(s.initial_game_state)
    display.print_all_possible_answers(full_cwa, s.problem.mode, "\nAll Possible Answers", permutation_order=True)
    print("\nSolving . . .")
    s.solve()
    print(f"Finished.")
    print(f"It took {s.seconds_to_solve:,} seconds.")
    sys.stdout.flush()
    return(s)

def pickle_solver(problem, pickle_entire=False, force_overwrite=False):
    """
    Given a Problem named tuple, if the solver for it hasn't already been pickled, makes it and pickles it; otherwise it does nothing. 
    If pickle_entire is True, pickles the entire solver. If it's false, sets the solver's evaluation cache to only the parts accessed during a best game (all that is needed to display tree and play game), so that unpickling it is much faster.
    If force_overwrite is true, then it remakes the solver regardless of whether the corresponding file exists, and overwrites the file if it does exist.
    """
    f_name = f_name_from_id(problem.identity)
    if(os.path.exists(f_name) and not force_overwrite):
        print(f"Asked to pickle {f_name}, but it already exists. Returning None.")
        return
    f = open(f_name, 'wb') # open mode write binary. Needed for pickling to work.
    s = make_solver(problem)
    print(f"\nPickling {f_name} . . .")
    if(not(pickle_entire)):
        new_evaluations_cache = get_relevant_parts_cache(s.evaluations_cache, s.initial_game_state)
        s.evaluations_cache = new_evaluations_cache
    pickle.dump(s, f)
    f.close()
    print("Done")
    return(s)

def get_or_make_solver(problem, pickle_entire=False, force_overwrite=True, no_pickles=False):
    """
    Given a Problem named tuple, if the solver is in file, gets it. If it isn't in file, makes it, pickles it.
    If pickle_entire is True, pickles the entire solver; otherwise, only pickles the parts of the evaluations cache needed to play the game perfectly.
    If force_overwrite is true, makes solver and writes it to file regardless of whether or not it existed before.
    If no_pickles is True, does not interact with pickles in any way. Makes solver from scratch, and does not pickle it nor change any existing pickles.
    Returns a tuple (solver, a bool indicating whether or not the solver was made from scratch)
    """
    print(f"\nReturning solver for problem: {problem.identity}.")
    if(no_pickles):
        print("No pickles. Making solver from scratch.")
        s = make_solver(problem)
        made_from_scratch = True
    else:
        f_name = f_name_from_id(problem.identity)
        if(os.path.exists(f_name)):
            if(not force_overwrite):
                print(f"Problem ID: {problem.identity} has been solved; retrieving solver from file. . .")
                s = unpickle_solver(problem.identity)
                made_from_scratch = False
            else:
                print("This problem has been solved, but will forcibly overwrite the solver file.")
                s = pickle_solver(problem, pickle_entire=pickle_entire, force_overwrite=force_overwrite)
                made_from_scratch = True
        else:
            print(f"Problem ID: {problem.identity} has not been solved. Solving. If this problem has 20+ unique answers, this may take some time . . .")
            s = pickle_solver(problem, pickle_entire=pickle_entire)
            made_from_scratch = True
    return((s, made_from_scratch))

def display_problem_solution(problem, pickle_entire=False, force_overwrite=False, no_pickles=False):
    """
    Given a Problem named tuple, gets or makes a solver for it (see get_or_make_solver), then prints the best move tree with the options that are currently set (SHOW_COMBOS_IN_TREE).
    """
    (s, made_from_scatch) = get_or_make_solver(problem, pickle_entire, force_overwrite, no_pickles)
    display_solution_from_solver(s, display_problem=not(made_from_scatch))

def play(problem, pickle_entire=False, force_overwrite=False, no_pickles=False):
    """
    Given a Problem named tuple, gets or makes a solver for it (see get_or_make_solver), then plays that problem, prompting the user for answers to its queries. Affected by PRINT_COMBOS option.
    """
    (s, made_from_scatch) = get_or_make_solver(problem, pickle_entire, force_overwrite, no_pickles)
    play_from_solver(s, display_problem=not(made_from_scatch))


# NOTE: How to use:
# Make problems (see above. Get from www.turingmachine.info)
# Problem are in form Problem(rc_nums_list, ID, mode (standard, extreme, or nightmare))
# Then, can use one of 3 main functions:
#   1) play(problem, pickle_entire, force_overwrite, no_pickles)
#   2) display_problem_solution(problem, pickle_entire, force_overwrite, no_pickles)
#   3) get_or_make_solver(problem, pickle_entire, force_overwrite, no_pickles) mainly for debugging/inspection.
# NOTE: If a tree is too big to fit on screen of terminal, can use the following command:
# python controller.py | less -SR -# 3

# less, with the -S option, allows you to scroll horizontally. -R tells it to honor the terminal color escape sequences. The -# n option means that each right/left arrow key press scrolls n lines. Can view full trees with that.

# options
PICKLE_DIRECTORY = "Pickles"       # Directory where all pickled solvers go.
# PRINT_COMBOS = False               # whether or not to print remaining combos after every query in play()
PRINT_COMBOS = True                # whether or not to print remaining combos after every query in play()
# SHOW_COMBOS_IN_TREE = False        # Print combos in trees in display_problem_solution()
SHOW_COMBOS_IN_TREE = True         # Print combos in trees in display_problem_solution()


# Profiling
# (s, _) = get_or_make_solver(f5x, no_pickles=True) # ~3 minutes.
# (s, _) = get_or_make_solver(f43, no_pickles=True) # 3,413 seconds.


# Good problems for demonstration purposes:
zero_query = get("B63YRW4")
p1 = get("1")
p1_n = get("1_N")
p2 = get("2")        # which is actually harder than any of the "hard" standard modes I've come across
c63 = get("C630YVB") # multiple combos, same answer
f5x = get("F5XTDF")  # Nice tree. May want to turn off combo printing. Kinda hard: 168 seconds.
f63 = get("F63EZQM") # Nice tree.      Full combos.
f52 = get("F52LUJG") # Excellent tree. Full combos
f43 = get("F435FE")  # Large tree. Hardest problem yet, at nearly an hour.

print(f"Using {platform.python_implementation()}.")
# latest = f43
latest = p1_n
display_problem_solution(latest, no_pickles=True)
play(latest, no_pickles=True)
