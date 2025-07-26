import string
import rules

RED = "\033[31m"
CHECK_SEQ = "\033[97;42m"
DEFAULT = "\033[0m"
def answer_to_string(answer: tuple):
    return("".join(str(d) for d in answer) if (answer is not None) else "None")
def rules_list_to_names(rl, pad=True):
    pad_spaces = rules.max_rule_name_length if(pad) else 0
    names = [f'{r.name:<{pad_spaces}}' for r in rl]
    return(', '.join(names))
def print_all_possible_answers(message, possible_combos_with_answers):
    """
    The difference between this and print_list_combos is that this prints each unique answer only once, and, following each unique answer, is a list of all rules combinations that lead to that answer. In print_list_combos, an answer is printed multiple times if it shows up in multiple combos. Also, this function doesn't print rules_card_indices, though that is subject to change.
    """
    (combos, answers) = zip(*possible_combos_with_answers)
    set_possible_answers = set(answers)
    print(message)
    final_answer = (len(set_possible_answers) == 1)
    multiple_combo_spacing = 7 if final_answer else 9
    for(answer_index, possible_answer) in enumerate(sorted(set_possible_answers), start=1):
        relevant_combos = [c for (c,a) in possible_combos_with_answers if (a == possible_answer)]
        answer_number_str = '    ' if final_answer else f'{answer_index:>3}: '
        print(f"{answer_number_str}{answer_to_string(possible_answer)} {rules_list_to_names(relevant_combos[0])} {[r.card_index for r in relevant_combos[0]]}")
        for c in relevant_combos[1:]:
            print(f"{' ' * multiple_combo_spacing}{rules_list_to_names(c)} {[r.card_index for r in c]}")
def print_final_answer(message, cwas):
    # NOTE: it's possible that there are multiple possible combinations that lead to this answer, and the program has not figured out which rule combination is actually the case (since the goal is only to figure out the answer). Therefore, print *all* rule combinations that could be true, from the program's perspective.
    answer = cwas[0][1]
    (combos, _) = zip(*cwas)
    print(message, end="")
    print(answer_to_string(answer))
    for c in combos:
        print(f"{' ' * len(message.lstrip())}{rules_list_to_names(c)} {[r.card_index for r in c]}")
def print_list_cwa(cwa, message = ""):
    print(message)
    for (i, cwa) in enumerate(sorted(cwa, key=lambda t:t[1])):
        print_combo_with_answer(i, cwa)
def print_combo_with_answer(combo_with_answer_index, combo_with_answer):
    (possible_combo, possible_answer) = combo_with_answer
    print(f'{combo_with_answer_index + 1:>3}: {answer_to_string(possible_answer)} {rules_list_to_names(possible_combo)}, rules_card_indices: {[r.card_index for r in possible_combo]}')
def print_problem(rcs_list, active=True):
    """
    NOTE: will have to change this for nightmare mode, since rules cards won't have corresponding letters, only numbers.
    """
    if(active):
        print("\nProblem")
        for (i, rc) in enumerate(rcs_list):
            print(f'{string.ascii_uppercase[i]}: {rules_list_to_names(rc)}')
def conduct_query(query_tup, expected_winning_round, expected_total_queries):
    """
    Asks user to conduct a query and input result, and returns result. Exits if user enters 'q'.
    """
    print(f"Query {answer_to_string(query_tup[0])} {string.ascii_uppercase[query_tup[1]]}. Expected Final Score: Rounds: {expected_winning_round:.3f}. Queries: {expected_total_queries:.3f}.")
    print("Result of query (T/F)\n> ", end="")
    result_raw = input()
    if(result_raw == 'q'):
        exit()
    result = (result_raw in ['T', 't'])
    return(result)
def display_query_history(query_history, num_rcs):
    if(query_history):
        print("\n" + (" " * 8) + f" ".join(string.ascii_uppercase[:num_rcs]))
        # print((" " * 8) + f" ".join('🅰️🅱️A'[:num_rcs]))
        for (round_num, round_info) in enumerate(query_history, start=1):
            verifier_info = [2 for i in range(num_rcs)]
            for (v, result) in round_info[1:]:
                verifier_info[v] = result
            print(f"{round_num}: {answer_to_string(round_info[0])}: {' '.join([[f'{RED}X{DEFAULT}', f'{CHECK_SEQ}✓{DEFAULT}', ' '][result] for result in verifier_info])}")
            print(DEFAULT)


# To be used for displaying things in debugging:
def inner_dict_to_string(inner_dict):
    s = '{ '
    for (possibility, combos_list) in inner_dict.items():
        s += f'{answer_to_string(possibility)}: {[[r.card_index for r in combo] for combo in combos_list]} '
    s += '}'
    return(s)

def print_rc_info(rc_infos, rc_index):
    rc_info = rc_infos[rc_index]
    print(f'\nrules card {rc_index}:' + ' {')
    for (rule_index_within_card, inner_dict) in rc_info.items():
            print(f'    possible rule index: {rule_index_within_card}: {inner_dict_to_string(inner_dict)}')
    print('}')

def print_useful_qs_dict_info(useful_queries_dict, rc_index, rc_infos, rc_list):
    """
    Displays all information in the useful_queries_dict about a specific rules card. Note: will need the rc_infos used to make the useful_queries_dict, and the rc_list.
    """
    q_dict_this_card = dict()
    corresponding_rc = rc_list[rc_index]
    corresponding_rc_info = rc_infos[rc_index]
    possible_rules_this_card = [
        corresponding_rc[possible_rule_index] for possible_rule_index in corresponding_rc_info.keys()
    ]
    print()
    for q in sorted(useful_queries_dict.keys()):
        inner_dict = useful_queries_dict[q]
        if(rc_index in useful_queries_dict[q]):
            q_info = inner_dict[rc_index]
            q_dict_this_card[q] = q_info
    print(f'For card {string.ascii_uppercase[rc_index]}. Possible rules: {rules_list_to_names(possible_rules_this_card)}')
    print(f"# useful queries this card: {len(q_dict_this_card)}")
    for q in sorted(q_dict_this_card.keys()):
        q_info = q_dict_this_card[q]
        print((' ' * 4) + answer_to_string(q))
        print(f'{" " * 8} {"expected_a_info_gain":<25}: {q_info.expected_a_info_gain:.3f}')
        print(f'{" " * 8} {"p_true":<25}: {q_info.p_true:.3f}')
        print(f'{" " * 8} {"a_info_gain_true":<25}: {q_info.a_info_gain_true:0.3f}')
        print(f'{" " * 8} Combos remaining if query returns True:')
        for (i, (combo, answer)) in enumerate(sorted(q_info.possible_combos_with_answers_remaining_if_true, key=lambda t:(t[1], tuple([r.card_index for r in t[0]]))), start=1):
            print(f'{" " * 12} {i:>3}: {answer_to_string(answer)} {rules_list_to_names(combo)}, {tuple([r.card_index for r in combo])}')
        for i in sorted(q_info.set_indexes_cwa_remaining_true, key=lambda t:(t[1], t[0])):
            print(f'{" " * 14} {i}')
        print()
        print(f'{" " * 8} {"p_false":<25}: {1 - q_info.p_true:0.3f}') 
        print(f'{" " * 8} {"a_info_gain_false":<25}: {q_info.a_info_gain_false:0.3f}')
        print(f'{" " * 8} Combos remaining if query returns False:')
        for (i, (combo, answer)) in enumerate(sorted(q_info.possible_combos_with_answers_remaining_if_false, key=lambda t:(t[1], tuple([r.card_index for r in t[0]]))), start=1):
            print(f'{" " * 12} {i:>3}: {answer_to_string(answer)} {rules_list_to_names(combo)}, {tuple([r.card_index for r in combo])}')
        for i in sorted(q_info.set_indexes_cwa_remaining_false, key=lambda t:(t[1], t[0])):
            print(f'{" " * 14} {i}')

def print_game_state(gs, name="game_state", active=True):
    if(not active):
        return
    # global rc_indexes_cwa_to_full_combos_dict # NOTE: use this for debugging session
    from tm import rc_indexes_cwa_to_full_combos_dict
    print(f'\n{name}')
    print(f'num_queries_this_round  : {gs.num_queries_this_round}.')
    print(f'proposal_used_this_round: {answer_to_string(gs.proposal_used_this_round)}')
    print(f"Sorted cwa set:")
    for (i, cwa) in enumerate([
        rc_indexes_cwa_to_full_combos_dict[cwa] for cwa in sorted(gs.fset_cwa_indexes_remaining, key = lambda cwa: cwa[1])
    ]):
        print_combo_with_answer(i, cwa)
    print(f"Sorted answer set:")
    for (i, ans) in enumerate(sorted([answer_to_string(ans_tup) for ans_tup in gs.fset_answers_remaining])):
        print(f'{i+1:>3}: {ans}')

def mov_to_str(move: tuple):
    return(f"{answer_to_string(move[0])} to verifier {string.ascii_uppercase[move[1]]}.")

def print_evaluations_cache_info(gs, name="game state"):
    """
    Returns a tuple (gs_false, gs_true) for game states that could result from executing the best query. For use in interactive debugging sessions.
    """
    # global rc_indexes_cwa_to_full_combos_dict # NOTE: use this for debugging session
    from tm import evaluations_cache
    # global evaluations_cache
    (best_mov, best_mov_cost_tup, best_gs_tup, best_expected_cost_tup) = evaluations_cache[gs]
    (gs_false, gs_true) = best_gs_tup
    cwa_remaining_if_false = gs_false.fset_cwa_indexes_remaining
    num_cwa_false = len(cwa_remaining_if_false)

    cwa_remaining_if_true = gs_true.fset_cwa_indexes_remaining
    num_cwa_true = len(cwa_remaining_if_true)

    num_cwa_now = len(gs.fset_cwa_indexes_remaining)
    p_true = num_cwa_true / num_cwa_now
    p_false = num_cwa_false / num_cwa_now

    # Remember that the cache does not contain already-won states.
    (_, _, _, expected_cost_false) = evaluations_cache.get(gs_false, (None, None, None, (0,0)))
    (_, _, _, expected_cost_true) = evaluations_cache.get(gs_true, (None, None, None, (0,0)))

    (ec_rounds, ec_queries) = best_expected_cost_tup
    print_game_state(gs, name=name)
    print(f"Expected cost to win from current state: {ec_rounds:0.3f} rounds. {ec_queries:0.3f} queries.")
    print(f"Best move: {mov_to_str(best_mov)}")
    (r_cost, q_cost) = best_mov_cost_tup
    print(f"Cost of best move: {r_cost} round{'' if (r_cost == 1) else 's'}. {q_cost} query.")
    print(f"Probability query returns False: {p_false:0.3f}")
    print(f"Probability query returns True : { p_true:0.3f}")

    print(f"Expected cost to win after false query: {expected_cost_false[0]:0.3f} rounds. {expected_cost_false[1]:0.3f} queries.")
    print(f"Expected cost to win after true query : {expected_cost_true[0]:0.3f} rounds. {expected_cost_true[1]:0.3f} queries.")
    print_game_state(gs_false, "Game State if query returns false:")
    print_game_state(gs_true, "Game State if query returns true:")
    tolerance = .01
    ec_rounds_calculated = r_cost + p_false*expected_cost_false[0] + p_true*expected_cost_true[0]
    ec_queries_calculated = q_cost + p_false*expected_cost_false[1] + p_true*expected_cost_true[1]
    if(abs(ec_rounds - ec_rounds_calculated) > tolerance):
        print("O noes! But maybe floating point error?")
        print(f"Difference is: {abs(ec_rounds - ec_rounds_calculated)}")
        # print(f"Should have been: {(r_cost + p_false*expected_cost_false[0] + p_true*expected_cost_true[0])}.")
        # print(f"Is              : {ec_rounds}.")
        exit()
    if(abs(ec_queries - ec_queries_calculated) > tolerance):
        print("O noes! But maybe floating point error?")
        print(f"Difference is: {abs(ec_queries - ec_queries_calculated)}")
        # print(f"Should have been: {(q_cost + p_false*expected_cost_false[1] + p_true*expected_cost_true[1])}.")
        # print(f"Is              : {ec_queries}.")
        exit()
    return(best_gs_tup)