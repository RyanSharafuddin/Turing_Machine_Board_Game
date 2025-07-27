import rules, display, solver

# TODO: May want a function to get the qs_dict for a problem so you can inspect and print it. Or make a Solver class with a field containing the qs_dict for easy inspection.

def update_query_history(q_history, move, new_round: bool, result: bool):
    if(new_round):
        q_history.append([move[0]])
    q_history[-1].append((move[1], result))
    if(move[0] != q_history[-1][0]):
        print("ERROR! The current move's proposal does not match up with the proposal used this round, and so this should have been a new round, but it isn't.")
        exit()

def play(rc_nums_list):
    (rcs_list, evaluations_cache, initial_game_state) = solver.solve(rc_nums_list)
    current_gs = initial_game_state
    # NOTE: below line for display purposes only
    rules.max_rule_name_length = max([max([len(r.name) for r in rc]) for rc in rcs_list])
    display.print_problem(rcs_list, active=True)
    full_cwa = solver.full_cwa_from_game_state(current_gs)
    display.print_all_possible_answers("\nAll possible answers:", full_cwa)
    current_round_num = 0
    total_queries_made = 0
    query_history = [] # each round is: [proposal, (verifier, result), . . .]
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
    display.display_query_history(query_history, len(rc_nums_list))
    display.print_final_answer("\nANSWER: ", full_cwa)

def display_problem_solution(rc_nums_list):
    """
    Prints best move tree (subject to change).
    """
    (rcs_list, evaluations_cache, initial_game_state) = solver.solve(rc_nums_list)
    rules.max_rule_name_length = max([max([len(r.name) for r in rc]) for rc in rcs_list])
    display.print_problem(rcs_list, active=True)
    full_cwa = solver.full_cwa_from_game_state(initial_game_state)
    if(len(solver.fset_answers_from_cwa_iterable(initial_game_state.fset_cwa_indexes_remaining)) == 1):
        display.print_final_answer("\nANSWER: ", full_cwa)
    else:
        display.print_all_possible_answers("\nAll possible answers:", full_cwa)
        display.print_best_move_tree(evaluations_cache, initial_game_state, SHOW_COMBOS_IN_TREE)

PRINT_COMBOS = True                # whether or not to print combos after every query when playing
SHOW_COMBOS_IN_TREE = True         # Print combos in trees when displaying problem solution
# problems
zero_query = [2, 5, 9, 15, 18, 22] # ID: B63 YRW 4. Takes 0 queries to solve.
p1 = [4, 9, 11, 14]                # ID:         1.
p2 = [3, 7, 10, 14]                # ID:         2. Useful for profiling
c63 = [9, 22, 24, 31, 37, 40]      # ID: C63 0YV B. Interesting b/c multiple combos lead to same answer here.

# DEBUG_MODE = False

# play(zero_query)
# play(p1)
# play(p2)
# play(c63)

# solver.solve(p2)         # ID:         2. FOR PROFILING

display_problem_solution(zero_query)
display_problem_solution(p1)
display_problem_solution(p2)
display_problem_solution(c63)


# For interactive debugging purposes
# (rcs_list, evaluations_cache, initial_game_state) = solver.solve(p2)
