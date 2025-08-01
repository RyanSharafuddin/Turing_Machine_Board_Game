import string
import rules
from collections import deque
from PrettyPrint import PrettyPrintTree
import colorama

# escape sequence is \033[<text color>;<background color>m
# see https://gist.github.com/fnky/458719343aabd01cfb17a3a4f7296797
# NOTE: for some reason that probably has to do with VS Code color themes, the checks and Xs don't display how I want them to in the terminal when using the Radical theme, but they do display correctly when using the Terminal app, or with certain other VS Code themes.
# RED = "\033[31m"            #   red text, default background
X_SEQ = "\033[97;41m"       # white text,     red background
CHECK_SEQ = "\033[97;42m"   # white text,   green background
DEFAULT = "\033[0;0m"
# DEFAULT = "\033[32;0m"
ROUND_INDENT = " " * 14
def rules_list_to_names(rl, pad=True):
    pad_spaces = rules.max_rule_name_length if(pad) else 0
    names = [f'{r.name:<{pad_spaces}}' for r in rl]
    return(', '.join(names))
def print_all_possible_answers(message, possible_combos_with_answers):
    """
    The difference between this and print_list_combos is that this prints each unique answer only once, and, following each unique answer, is a list of all rules combinations that lead to that answer. In print_list_combos, an answer is printed multiple times if it shows up in multiple combos.
    """
    (combos, answers) = zip(*possible_combos_with_answers)
    set_possible_answers = set(answers)
    print(message)
    final_answer = (len(set_possible_answers) == 1)
    multiple_combo_spacing = 7 if final_answer else 9
    for(answer_index, possible_answer) in enumerate(sorted(set_possible_answers), start=1):
        relevant_combos = [c for (c,a) in possible_combos_with_answers if (a == possible_answer)]
        answer_number_str = '    ' if final_answer else f'{answer_index:>3}: '
        print(f"{answer_number_str}{possible_answer} {rules_list_to_names(relevant_combos[0])} {[r.card_index for r in relevant_combos[0]]}")
        for c in relevant_combos[1:]:
            print(f"{' ' * multiple_combo_spacing}{rules_list_to_names(c)} {[r.card_index for r in c]}")
def print_final_answer(message, cwas):
    # NOTE: it's possible that there are multiple possible combinations that lead to this answer, and the program has not figured out which rule combination is actually the case (since the goal is only to figure out the answer). Therefore, print *all* rule combinations that could be true, from the program's perspective.
    answer = cwas[0][1]
    (combos, _) = zip(*cwas)
    print(message, end="")
    print(answer)
    for c in combos:
        print(f"{' ' * len(message.lstrip())}{rules_list_to_names(c)} {[r.card_index for r in c]}")
def print_list_cwa(cwa, message = "", use_round_indent=False, active=True):
    if(not active):
        return
    indent = ROUND_INDENT if(use_round_indent) else ""
    if(message[0] == '\n'):
        indent = '\n' + indent
        message = message[1:]
    print(indent + message)
    for (i, cwa) in enumerate(sorted(cwa, key=lambda t:t[1])):
        print_combo_with_answer(i, cwa, use_round_indent)
def print_combo_with_answer(combo_with_answer_index, combo_with_answer, use_round_indent=False):
    indent = ROUND_INDENT if(use_round_indent) else ""
    (possible_combo, possible_answer) = combo_with_answer
    print(f'{indent}{combo_with_answer_index + 1:>3}: {possible_answer} {rules_list_to_names(possible_combo)}, rules_card_indices: {[r.card_index for r in possible_combo]}')
def print_problem(rcs_list, active=True):
    if(active):
        print("\nProblem")
        for (i, rc) in enumerate(rcs_list):
            print(f'{string.ascii_uppercase[i]}: {rules_list_to_names(rc)}')
def display_query_num_info(current_round_num, query_this_round, total_query, new_round: bool, proposal):
    if(new_round):
        print(f"\nRound   : {current_round_num:>3}")
        print(f"Proposal: {proposal}")
    q_newline = "\n" #if(query_this_round == 1) else ""
    print(f"{q_newline}{ROUND_INDENT}Query: {query_this_round}. Total query: {total_query}.")
def conduct_query(query_tup, expected_winning_round, expected_total_queries):
    """
    Asks user to conduct a query and input result, and returns result. Exits if user enters 'q'.
    """
    print(f"{ROUND_INDENT}Query verifier: {string.ascii_uppercase[query_tup[1]]}. Expected Final Score: Rounds: {expected_winning_round:.3f}. Queries: {expected_total_queries:.3f}.")
    print(f"{ROUND_INDENT}Result of query (T/F)\n{ROUND_INDENT}> ", end="")
    result_raw = input()
    if(result_raw == 'q'):
        exit()
    result = (result_raw in ['T', 't'])
    return(result)
def display_query_history(query_history, num_rcs):
    separator = ""
    if(query_history):
        print("\n" + (" " * 8) + separator.join(string.ascii_uppercase[:num_rcs]))
        for (round_num, round_info) in enumerate(query_history, start=1):
            verifier_info = [2 for i in range(num_rcs)]
            for (v, result) in round_info[1:]:
                verifier_info[v] = result
            print(f"{round_num}: {round_info[0]}: {separator.join([[f'{X_SEQ}X{DEFAULT}', f'{CHECK_SEQ}✓{DEFAULT}', ' '][result] for result in verifier_info])}")
            print(DEFAULT, end="")


# To be used for displaying things in debugging:

class Solver_Displayer:
    def __init__(self, solver):
        self.solver = solver

    def print_evaluations_cache_info(self, gs, name="game state"):
        """
        Returns a tuple (gs_false, gs_true) for game states that could result from executing the best query. For use in interactive debugging sessions.
        NOTE: in interactive debugging session, use like this:
        (gs_false, gs_true) = sd.print_evaluations_cache_info(gs, name)
        """
        evaluations_cache = self.solver.evaluations_cache
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
        expected_cost_false = evaluations_cache.get(gs_false, (None, None, None, (0,0)))[3]
        expected_cost_true = evaluations_cache.get(gs_true, (None, None, None, (0,0)))[3]

        (ec_rounds, ec_queries) = best_expected_cost_tup
        self.print_game_state(gs, name=name)
        print(f"Expected cost to win from current state: {ec_rounds:0.3f} rounds. {ec_queries:0.3f} queries.")
        print(f"Best move: {mov_to_str(best_mov)}")
        (r_cost, q_cost) = best_mov_cost_tup
        print(f"Cost of best move: {r_cost} round{'' if (r_cost == 1) else 's'}. {q_cost} query.")
        print(f"Probability query returns False: {p_false:0.3f}")
        print(f"Probability query returns True : { p_true:0.3f}")

        print(f"Expected cost to win after false query: {expected_cost_false[0]:0.3f} rounds. {expected_cost_false[1]:0.3f} queries.")
        print(f"Expected cost to win after true query : {expected_cost_true[0]:0.3f} rounds. {expected_cost_true[1]:0.3f} queries.")
        self.print_game_state(gs_false, "Game State if query returns false:")
        self.print_game_state(gs_true, "Game State if query returns true:")
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

    def print_game_state(self, gs, name="game_state", active=True):
        if(not active):
            return
        print(f'\n{name}')
        print(f'num_queries_this_round  : {gs.num_queries_this_round}.')
        print(f'proposal_used_this_round: {gs.proposal_used_this_round}')
        print(f"Sorted cwa set:")
        for (i, cwa) in enumerate([
            self.solver.rc_indexes_cwa_to_full_combos_dict[cwa] for cwa in sorted(gs.fset_cwa_indexes_remaining, key = lambda cwa: cwa[1])
        ]):
            print_combo_with_answer(i, cwa)

def inner_dict_to_string(inner_dict):
    s = '{ '
    for (possibility, combos_list) in inner_dict.items():
        s += f'{possibility}: {[[r.card_index for r in combo] for combo in combos_list]} '
    s += '}'
    return(s)

def print_rc_info(rc_infos, rc_index):
    rc_info = rc_infos[rc_index]
    print(f'\nrules card {rc_index}:' + ' {')
    for (rule_index_within_card, inner_dict) in rc_info.items():
            print(f'    possible rule index: {rule_index_within_card}: {inner_dict_to_string(inner_dict)}')
    print('}')

def print_useful_qs_dict_info(useful_queries_dict, rc_index, rc_infos, rcs_list):
    """
    Displays all information in the useful_queries_dict about a specific rules card. Note: will need the rc_infos used to make the useful_queries_dict, and the rc_list.
    """
    q_dict_this_card = dict()
    corresponding_rc = rcs_list[rc_index]
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
        print(f"{(' ' * 4)}{q}")
        print(f'{" " * 8} {"expected_a_info_gain":<25}: {q_info.expected_a_info_gain:.3f}')
        print(f'{" " * 8} {"p_true":<25}: {q_info.p_true:.3f}')
        print(f'{" " * 8} {"a_info_gain_true":<25}: {q_info.a_info_gain_true:0.3f}')
        print(f'{" " * 8} Combos remaining if query returns True:')
        for (i, (combo, answer)) in enumerate(sorted(q_info.possible_combos_with_answers_remaining_if_true, key=lambda t:(t[1], tuple([r.card_index for r in t[0]]))), start=1):
            print(f'{" " * 12} {i:>3}: {answer} {rules_list_to_names(combo)}, {tuple([r.card_index for r in combo])}')
        for i in sorted(q_info.set_indexes_cwa_remaining_true, key=lambda t:(t[1], t[0])):
            print(f'{" " * 14} {i}')
        print()
        print(f'{" " * 8} {"p_false":<25}: {1 - q_info.p_true:0.3f}') 
        print(f'{" " * 8} {"a_info_gain_false":<25}: {q_info.a_info_gain_false:0.3f}')
        print(f'{" " * 8} Combos remaining if query returns False:')
        for (i, (combo, answer)) in enumerate(sorted(q_info.possible_combos_with_answers_remaining_if_false, key=lambda t:(t[1], tuple([r.card_index for r in t[0]]))), start=1):
            print(f'{" " * 12} {i:>3}: {answer} {rules_list_to_names(combo)}, {tuple([r.card_index for r in combo])}')
        for i in sorted(q_info.set_indexes_cwa_remaining_false, key=lambda t:(t[1], t[0])):
            print(f'{" " * 14} {i}')

def mov_to_str(move: tuple):
    return(f"{move[0]} to verifier {string.ascii_uppercase[move[1]]}.")

def get_max_string_height_by_depth(tree):
    """
    Given a tree, returns a list l, where l[i] is the maximum number of combinations of an internal node at that height.
    """
    answer = []
    q = deque()
    q.append(tree)
    while(q):
        curr_node = q.popleft()
        if(curr_node.gs in tree.solver.evaluations_cache): # it's an internal node
            num_combinations = len(curr_node.gs.fset_cwa_indexes_remaining)
            if(curr_node.depth == len(answer)):
                answer.append(num_combinations)
            else:
                answer[curr_node.depth] = max(answer[curr_node.depth], num_combinations)
            children = get_children(curr_node)
            for child in children:
                q.append(child)
    return(answer)

class Tree:
    show_combos_in_tree = False # a class variable so don't have to include it in every tree initializer
    solver = None               # Now the Tree class has access to the solver used to create all its info.
    max_combos_by_depth = []    # array[i] is the maximum number of combos of an internal node at depth i, considering the root to be at depth 0. Set when making each tree.
    def __init__(
            self,
            gs,
            prob=1.0,
            cost_to_get_here=(0, 0),
            # num_newlines=0, # number of newlines to insert when printing combos
            depth=0,
            tree_type='gs',
            move=None,
    ):
        # prob is the probability of getting to this gs from the query above it in the best move tree
        self.gs = gs
        self.prob = prob
        self.cost_to_get_here = cost_to_get_here
        # self.num_newlines = num_newlines
        self.depth = depth

        # TODO: fields to be added to be used for 'move' type trees:
        self.type = tree_type
        self.move = move
        # prob_tup # probabilities of the move being (false, true)
        # gs_tup   # resulting game states from the move being false, true
        # m_cost   # the cost the move in self.move

def add_tups(*tups):
    result = tuple([sum([t[i] for t in tups]) for i in range(len(tups))])
    return(result)

def get_children_multi_move(tree):
    if(tree.type == 'move'):
        # TODO: implement
        # should have set tree.gs_tup and tree.prob_tup for this move, so just return those.
        raise Exception("Unimplemented")
    else:
        # tree is type game state
        if((Tree.solver.evaluations_cache is not None) and (tree.gs in Tree.solver.evaluations_cache)):
            result = Tree.solver.evaluations_cache.get(tree.gs)
            if(result is not None):
                (best_move, best_move_cost, gs_tup, total_expected_cost) = result
                current_num_combos = len(tree.gs.fset_cwa_indexes_remaining)
                num_combos_if_q_true = len(gs_tup[1].fset_cwa_indexes_remaining)
                p_true = num_combos_if_q_true / current_num_combos
                p_false = 1 - p_true
                prob_tup = (p_false, p_true)

                raise Exception("Unimplemented")
                m = Tree(gs=tree.gs, cost_to_get_here=tree.cost_to_get_here, tree_type='move', move=best_move)
                # return a list of several moves that lead to different evaluations, if there are any
                # TODO: use the Tree.solver to get some other useful moves that lead to different tree shapes than the best move, get their costs and resulting gs_tups and probabilities, and return some children moves that you want to see. Pretty sure you can do this with get_and_apply_moves.
                return[m]
        # finished game; no children. This is an answer node
        return([])

def node_to_str_multi_move(tree):
    if(tree.type == 'gs'):
        # I think I can just call my regular node_to_str(tree) function below.
        # Ah, but I'll have to pass in a new parameter that tells it not to print the best move beneath all the gs info in the node, since the best move will now be its own node. Well, pass in or set. Maybe make it a class field in tree, and have print_multi_move_tree and print_best_move_tree set it when you first call them. Should also stop the regular node_to_str function from printing the probability of reaching a game state in the game state nodes when using it from here.
        pass
    else: # move type node
        pass
    raise Exception("Unimplemented")

def get_children(tree):
    if((Tree.solver.evaluations_cache is not None) and (tree.gs in Tree.solver.evaluations_cache)):
        result = Tree.solver.evaluations_cache.get(tree.gs)
        if(result is not None):
            (best_move, best_move_cost, gs_tup, total_expected_cost) = result
            current_num_combos = len(tree.gs.fset_cwa_indexes_remaining)
            num_combos_if_q_true = len(gs_tup[1].fset_cwa_indexes_remaining)
            # num_combos_if_q_false = current_num_combos - num_combos_if_q_true
            # larger_num_combos = max(num_combos_if_q_true, num_combos_if_q_false)
            # num_newlines_tup = (larger_num_combos - num_combos_if_q_false, larger_num_combos - num_combos_if_q_true)
            p_true = num_combos_if_q_true / current_num_combos
            p_false = 1 - p_true
            prob_tup = (p_false, p_true)
            children = [Tree(gs=gs_tup[i], prob=prob_tup[i], cost_to_get_here=add_tups(tree.cost_to_get_here, best_move_cost), depth=tree.depth+1) for i in range(2)]
            return(children)
    return([])
def node_to_str(tree):
    nl = '\n'
    rcs_lengths = [len(rc) for rc in tree.solver.rcs_list]
    chars_to_print = [2 if (i > 10) else 1 for i in rcs_lengths] # chars_to_print[i] is the number of chars needed to print a rule index on the ith rule card, since some rule cards have over 10 rules on them, so rule index 10 (zero-based) will need two characters to print.
    if((Tree.solver.evaluations_cache is not None) and (tree.gs in Tree.solver.evaluations_cache)):
        result = Tree.solver.evaluations_cache.get(tree.gs)
        if(result is not None): # internal node
            # NOTE: consider displaying cost of this move, either in edge or in node.
            combos_l = sorted(tree.gs.fset_cwa_indexes_remaining, key = lambda t: t[1])
            (best_move, best_move_cost, gs_tup, total_expected_cost) = result
            combos_strs = [f"{n:>2}. {c[1]}: {' '.join(str(f'{i:>{chars_to_print[rc_ind]}}') for (rc_ind, i) in enumerate(c[0]))}" for (n, c) in enumerate(combos_l, start=1)]
            prob_str = f"{tree.prob:0.3f}" # Note: in format 0.123
            prob_str = f"{prob_str[2:4]}.{prob_str[4]}%"
            move_str = f"{best_move[0]} {string.ascii_uppercase[best_move[1]]}"
            # NOTE: comment out below if block to not mark new rounds in the best move tree
            if(best_move_cost[0] == 1): # if the best move costs a round
                move_str += ' (R)'
            cost_of_node_str = ' '.join([f'{add_tups(tree.cost_to_get_here, total_expected_cost)[i]:.3f}' for i in range(2)])
            verifier_names_str = (" " * 9) + ' '.join( # NOTE: change the 9 if change combo lines beginning
                [f'{string.ascii_uppercase[i]:>{chars_to_print[i]}}' for i in range(len(combos_l[0][0]))]
            )
            if(Tree.show_combos_in_tree): # only show combos in tree if user asks for it.
                combos_lines = [verifier_names_str] + combos_strs + ['' for i in range(Tree.max_combos_by_depth[tree.depth] - len(combos_strs))]
            else:
                combos_lines = []

            if(tree.prob == 1):
                prob_line = [] # don't show probability for initial game state where probability is 1
            else:
                prob_line = [prob_str]

            lines = (
                prob_line +
                [cost_of_node_str] +
                combos_lines +
                [move_str]
            )
            max_line_length = max([len(l) for l in lines])
            lines = [f"{l:^{max_line_length}}" for l in lines]
            # lines = lines[1:] if tree.prob == 1 else lines # don't print prob = 1.000 for initial state
            node_str = f"{nl.join(lines)}"
            return(node_str)
    else: # leaf node
        # NOTE: consider displaying the combos remaining as well
        l = list(tree.gs.fset_cwa_indexes_remaining)
        answer = l[0][1]
        return(answer)

def print_best_move_tree(gs, show_combos, solver):
    print()
    Tree.show_combos_in_tree = show_combos
    Tree.solver = solver
    tree = Tree(gs)
    Tree.max_combos_by_depth = get_max_string_height_by_depth(tree)
    pt = PrettyPrintTree(get_children, node_to_str)
    pt(tree)

def print_multi_move_tree(gs, show_combos, solver):
    raise Exception("Unimplemented")
    print()
    Tree.show_combos_in_tree = show_combos
    Tree.solver = solver
    tree = Tree(gs)
    pt = PrettyPrintTree(get_children_multi_move, node_to_str_multi_move)
    pt(tree)