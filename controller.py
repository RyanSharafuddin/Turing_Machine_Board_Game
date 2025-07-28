import rules, display, solver

# TODO: May want a function to get the qs_dict for a problem so you can inspect and print it. Or make a Solver class with a field containing the qs_dict for easy inspection.

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

def play(rc_nums_list, mode=solver.STANDARD):
    s = solver.Solver(rc_nums_list, mode=mode)
    (rcs_list, initial_game_state) = (s.rcs_list, s.initial_game_state)
    current_gs = initial_game_state
    # NOTE: below line for display purposes only
    rules.max_rule_name_length = max([max([len(r.name) for r in rc]) for rc in rcs_list])
    display.print_problem(rcs_list, active=True)
    full_cwa = solver.full_cwa_from_game_state(current_gs)
    display.print_all_possible_answers("\nAll possible answers:", full_cwa)
    current_round_num = 0
    total_queries_made = 0
    query_history = [] # each round is: [proposal, (verifier, result), . . .]
    s.solve()
    evaluations_cache = s.evaluations_cache
    while(len(solver.fset_answers_from_cwa_iterable(current_gs.fset_cwa_indexes_remaining)) > 1):
        (best_move_tup, mcost_tup, gs_tup, expected_cost_tup) = evaluations_cache[current_gs]
        full_cwa = solver.full_cwa_from_game_state(current_gs)
        expected_winning_round = current_round_num + expected_cost_tup[0]
        expected_total_queries = total_queries_made + expected_cost_tup[1]
        display.print_list_cwa(full_cwa, "\nRemaining Combos:", use_round_indent=True, active=PRINT_COMBOS)
        current_round_num += mcost_tup[0]
        total_queries_made += mcost_tup[1]
        query_this_round = 1 if (mcost_tup[0]) else current_gs.num_queries_this_round + 1
        display.display_query_num_info(current_round_num, query_this_round, total_queries_made, mcost_tup[0], best_move_tup[0])
        result = display.conduct_query(
            best_move_tup,
            expected_winning_round,
            expected_total_queries,
        )
        current_gs = gs_tup[result]
        update_query_history(query_history, best_move_tup, mcost_tup[0], result)
    # Found an answer
    full_cwa = solver.full_cwa_from_game_state(current_gs)
    print(f"\nFinal Score: Rounds: {current_round_num}. Queries: {total_queries_made}.")
    display.display_query_history(query_history, len(rcs_list))
    display.print_final_answer("\nANSWER: ", full_cwa)

def display_problem_solution(rc_nums_list, mode=solver.STANDARD):
    """
    Prints best move tree (subject to change). Or just the answer if there are no useful moves to be made.
    """
    s = solver.Solver(rc_nums_list, mode=mode)
    (rcs_list, initial_game_state) = (s.rcs_list, s.initial_game_state)
    rules.max_rule_name_length = max([max([len(r.name) for r in rc]) for rc in rcs_list])
    display.print_problem(rcs_list, active=True)
    full_cwa = solver.full_cwa_from_game_state(initial_game_state)
    if(len(solver.fset_answers_from_cwa_iterable(initial_game_state.fset_cwa_indexes_remaining)) == 1):
        display.print_final_answer("\nANSWER: ", full_cwa)
    else:
        display.print_all_possible_answers("\nAll possible answers:", full_cwa)
        s.solve()
        display.print_best_move_tree(initial_game_state, SHOW_COMBOS_IN_TREE, solver=s)
        # TODO: uncomment when done with adding the correct functions to display (see todo.txt optional)
        # display.print_multi_move_tree(initial_game_state, SHOW_COMBOS_IN_TREE, solver=s)

# PRINT_COMBOS = False                # whether or not to print combos after every query when playing
PRINT_COMBOS = True                # whether or not to print combos after every query when playing
# SHOW_COMBOS_IN_TREE = False         # Print combos in trees when displaying problem solution
SHOW_COMBOS_IN_TREE = True         # Print combos in trees when displaying problem solution

# problems
zero_query = [2, 5, 9, 15, 18, 22] # ID: B63 YRW 4. Takes 0 queries to solve.
p1  = [4, 9, 11, 14]                # ID:         1.
p2  = [3, 7, 10, 14]                # ID:         2. Useful for profiling
c63 = [ 9, 22, 24, 31, 37, 40]      # ID: C63 0YV B. Interesting b/c multiple combos lead to same answer here.
c46 = [19, 22, 36, 41]             # ID: C46 43N
a52 = [ 7,  8, 12, 14, 17]           # ID: A52 F7E 1
c5h = [ 2, 15, 30, 31, 33]          # ID: C5H CBJ
f5x = [28, 14, 19,  6, 27, 16,  9, 47, 20, 21] # ID: F5X TDF. Extreme. Actually hard. Takes ~220 seconds.
e63 = [18, 16, 17, 19, 10,  5, 14,  1, 11,  6,  2,  9] # ID: E63 YF4 H. Extreme. Very easy, tho.
f63 = [15, 44, 11, 23, 40, 17, 25, 10, 16, 20, 19,  3] # ID #F63 EZQ M. Extreme. "hard" difficulty. 
latest_extreme = f63

# Playing
# play(zero_query)
# play(p1)
# play(p2)
# play(c63)
# play(c46)
# play(a52)
# play(f5x, mode=solver.EXTREME)
# play(latest_extreme, mode=solver.EXTREME)

# Profiling
# s = solver.solve(p2)         # ID:         2. FOR PROFILING
# s = solver.solve(f5x, mode=solver.EXTREME)   # currently ~218 seconds.

# Displaying best move tree
# display_problem_solution(zero_query)
# display_problem_solution(p1)
# display_problem_solution(p2)
# display_problem_solution(c63)
# display_problem_solution(c46)
# display_problem_solution(a52)
# display_problem_solution(latest_extreme, mode=solver.EXTREME)
# display_problem_solution(f5x, mode=solver.EXTREME) # may want to turn off SHOW_COMBOS_IN_TREE, unless have horizontal scrolling terminal (Ghostty?)
# display_problem_solution(latest_extreme, mode=solver.EXTREME)

# For interactive debugging purposes
# inspect solver.evaluations_cache and solver.initial_game_state using the debugging functions in display
# solver.solve(p2)


# Good problems for demonstration purposes:
# zero_query
# p2        which is actually harder than any of the "hard" standard modes I've come across
# c63       multiple combos, same answer

# f63, extreme.
# e63, extreme. Turn off tree combo printing, though. Takes ~3.5 minutes

# play(f5x, mode=solver.EXTREME)
