import pickle, os, sys, platform, gc
from rich import print as rprint
from definitions import *
from config import *
from problems import get_problem_by_id as get
import display, solver


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
    full_cwa = s.full_cwa_from_game_state(current_gs)
    current_round_num = 0
    total_queries_made = 0
    query_history = [] # each round is: [proposal, (verifier, result), . . .]
    if(display_problem):
        sd.print_problem(s.rcs_list, s.problem, active=True)
        sd.print_all_possible_answers(full_cwa, "\nAll Possible Answers", permutation_order=P_ORDER)
    while not(solver.one_answer_left(current_gs.fset_cwa_indexes_remaining)):
        (best_move_tup, mcost_tup, gs_tup, expected_cost_tup) = s.evaluations_cache[current_gs]
        full_cwa = s.full_cwa_from_game_state(current_gs)
        expected_winning_round = current_round_num + expected_cost_tup[0]
        expected_total_queries = total_queries_made + expected_cost_tup[1]
        if(total_queries_made > 0):
            # only print this table after having made some queries, since already printed it at start.
            sd.print_all_possible_answers(
                full_cwa, "Remaining Combos", permutation_order=P_ORDER, active=PRINT_COMBOS, verifier_to_sort_by=verifier_to_sort_by
            )
        current_round_num += mcost_tup[0]
        total_queries_made += mcost_tup[1]
        query_this_round = 1 if (mcost_tup[0]) else current_gs.num_queries_this_round + 1
        display.display_new_round(current_round_num, query_this_round, best_move_tup)
        result = display.conduct_query(
            best_move_tup,
            expected_winning_round,
            expected_total_queries,
            query_this_round,
            total_queries_made
        )
        verifier_to_sort_by = best_move_tup[1]
        current_gs = gs_tup[result]
        update_query_history(query_history, best_move_tup, mcost_tup[0], result)
    # Found an answer
    full_cwa = s.full_cwa_from_game_state(current_gs)
    v_to_sort_by = None if(total_queries_made == 0) else best_move_tup[1]
    answers_table = sd.get_all_possible_answers_table(
        full_cwa, "ANSWER", permutation_order=P_ORDER, verifier_to_sort_by=v_to_sort_by
    )
    query_history_table = display.get_query_history_table(query_history, len(s.rcs_list))
    ans_num_style = "b cyan1"
    ans_line = f"Answer: [{ans_num_style}]{full_cwa[0][-1]}[/{ans_num_style}]"
    score_line = f"Final Score: Rounds: {current_round_num}. Total Queries: {total_queries_made}."
    display.end_play_display(answers_table, query_history_table, ans_line, score_line)

def display_solution_from_solver(s, display_problem = True):
    """
    This function assumes that the solver s has already been solved.
    """
    sd = display.Solver_Displayer(s)
    if(display_problem):
        sd.print_problem(s.rcs_list, s.problem, active=True)
    full_cwa = s.full_cwa_from_game_state(s.initial_game_state)
    if(len(solver.fset_answers_from_cwa_iterable(s.initial_game_state.fset_cwa_indexes_remaining)) == 1):
        sd.print_all_possible_answers(full_cwa, "\nANSWER", permutation_order=P_ORDER)
    else:
        if(display_problem):
            sd.print_all_possible_answers(full_cwa, "\nAll Possible Answers", permutation_order=P_ORDER)
        display.print_best_move_tree(s.initial_game_state, SHOW_COMBOS_IN_TREE, solver=s)

def unpickle_solver(identity):
    f_name = f_name_from_id(identity)
    print(f"\nUnpickling {f_name}.")
    f = open(f_name, 'rb')
    s = pickle.load(f)
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
    stack : list[Game_State] = [initial_game_state]
    while(stack):
        curr_gs = stack.pop()
        if((curr_gs in evaluations_cache) and (curr_gs not in new_evaluations_cache) and
            (not solver.one_answer_left(curr_gs.fset_cwa_indexes_remaining))):
            curr_gs_answer = evaluations_cache[curr_gs]
            (curr_gs_false_result, curr_gs_true_result) = curr_gs_answer[2]
            new_evaluations_cache[curr_gs] = curr_gs_answer
            stack.append(curr_gs_false_result)
            stack.append(curr_gs_true_result)
    return(new_evaluations_cache)

def make_solver(problem: Problem):
    s = solver.Solver(problem)
    sd = display.Solver_Displayer(s)
    if(DISPLAY):
        sd.print_problem(s.rcs_list, s.problem, active=True)
    if(not(s.full_cwa)):
        rprint(f"\n[bold red]Error[/bold red]: This is an invalid problem which has no solutions. Check that you specified the problem correctly in problems.py, and the rules correctly in rules.py.")
        console.print("Reminder that any rule combination must obey two rules:\n  1. There is exactly one proposal that satisfies them all.\n  2. Each rule eliminates at least one possibility that is not eliminated by any other rule.", highlight=False)
        rprint("\nRule card numbers list: ", s.problem.rc_nums_list, end='')
        print("Exiting.")
        exit()
    full_cwa = s.full_cwa_from_game_state(s.initial_game_state)
    if(DISPLAY):
        sd.print_all_possible_answers(full_cwa, "\nAll Possible Answers", permutation_order=P_ORDER)
    print("\nSolving . . .")
    s.solve()
    print(f"Finished.")
    console.print(f"It took {s.seconds_to_solve:,} seconds.")
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
    s = make_solver(problem)
    f = open(f_name, 'wb') # open mode write binary. Needed for pickling to work.
    print(f"\nPickling {f_name} . . .")
    if(not(pickle_entire)):
        new_evaluations_cache = get_relevant_parts_cache(s.evaluations_cache, s.initial_game_state)
        s.evaluations_cache = new_evaluations_cache
    pickle.dump(s, f, protocol=pickle.HIGHEST_PROTOCOL)
    f.close()
    print("Done")
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
    problem = get(problem_id)
    f = out if (DISPLAY) else null
    print(f"\nReturning solver for problem: {problem.identity}.", file=f)
    if(DISABLE_GC):
        gc.disable()
        gc.collect()
    if(no_pickles):
        print("No pickles. Making solver from scratch.", file=f)
        s = make_solver(problem)
        made_from_scratch = True
    else:
        f_name = f_name_from_id(problem.identity)
        if(os.path.exists(f_name)):
            if(not force_overwrite):
                print(f"Problem ID: {problem.identity} has been solved; retrieving solver from file. . .", file=f)
                s = unpickle_solver(problem.identity)
                made_from_scratch = False
            else:
                print("This problem has been solved, but will overwrite the solver file.", file=f)
                s = pickle_solver(problem, pickle_entire=pickle_entire, force_overwrite=force_overwrite)
                made_from_scratch = True
        else:
            print(f"Problem ID: {problem.identity} has not been solved. Solving. If this problem has 20+ unique answers, this may take some time . . .", file=f)
            s = pickle_solver(problem, pickle_entire=pickle_entire)
            made_from_scratch = True
    if(DISABLE_GC):
        gc.enable()
    return((s, made_from_scratch))

def display_problem_solution(problem_id: str, pickle_entire=False, force_overwrite=False, no_pickles=False):
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

                                   # speed significantly, but may run out of memory faster.

# Profiling/Interactive Debugging
# s = get_or_make_solver(f5x, no_pickles=True)[0] # ~3 minutes.
# s = get_or_make_solver(f43, no_pickles=True)[0] # 3,413 seconds.

# Use the below 2 lines to get interactive debugging started
# sd = display.Solver_Displayer(s)
# (gs_false, gs_true) = sd.print_evaluations_cache_info(s.initital_game_state)


# Good problems for demonstration purposes:
zero_query = "B63YRW4"
p1 = "1"
p1_n = "1_N"
p2 = "2"        # which is actually harder than any of the "hard" standard modes I've come across
c63 = "C630YVB" # multiple combos, same answer
f5x = "F5XTDF"  # Nice tree. May want to turn off combo printing. Kinda hard: 168 seconds.
f63 = "F63EZQM" # Nice tree.      Full combos.
f52 = "F52LUJG" # Excellent tree. Full combos
f43 = "F435FE"  # Large tree. Hardest problem yet, at nearly an hour.
i = "Invalid"   # Testing purposes only.

print(f"Using {platform.python_implementation()}.")
p2_n = "2_N"
# latest = f43
# latest = i
# latest = f63
# latest = f52
# latest = p1
# latest = p1_n
# latest = f5x # 151 seconds after disabling garbage collection
# latest = c63
# latest = "B63YRW4_N" # zero_query
# latest = zero_query
# latest = "2_N"
# play(latest)
# display_problem_solution(latest)

# display_problem_solution(latest, no_pickles=True)
# play(latest, no_pickles=True)

# Use the below in REPL for testing/debugging purposes
# s = get_or_make_solver(latest, no_pickles=False, force_overwrite=False)[0]
# sd = display.Solver_Displayer(s)

# sd.print_useful_qs_dict_info(
#     s.qs_dict,
#     s.full_cwa,
#     verifier_index=None,          # set to None for all verifiers
#     proposal_to_examine=None,   # set to None for all proposals
#     see_all_combos=True
# )
# console.rule()
# (gs_false, gs_true) = sd.print_evaluations_cache_info(s.initial_game_state)

null = open('/dev/null', 'w')
out = sys.stdout
latest = p1_n # WARN ditto line 301
# latest = f63 # WARN ditto line 301
# latest = f5x # WARN ditto line 301
# play(latest, no_pickles=True)
display_problem_solution(latest, force_overwrite=True)
# s = get_or_make_solver(latest, force_overwrite=False, no_pickles=True) # WARN: ditto line 302
null.close()