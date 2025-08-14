import string, math
from itertools import zip_longest
from collections import deque
from PrettyPrint import PrettyPrintTree
# import colorama
from rich.table import Table
from rich.text import Text
from rich import print as rprint
import rules
from definitions import NIGHTMARE, console

# escape sequence is \033[<text color>;<background color>m
# see https://gist.github.com/fnky/458719343aabd01cfb17a3a4f7296797
# NOTE: for some reason that probably has to do with VS Code color themes, the checks and Xs don't display how I want them to in the terminal when using the Radical theme, but they do display correctly when using the Terminal app, or with certain other VS Code themes.
# RED = "\033[31m"            #   red text, default background
X_SEQ = "\033[97;41m"       # white text,     red background
CHECK_SEQ = "\033[97;42m"   # white text,   green background
DEFAULT = "\033[0;0m"
# DEFAULT = "\033[32;0m"
ROUND_INDENT_AMOUNT = 14
ROUND_INDENT = " " * ROUND_INDENT_AMOUNT
letters = string.ascii_uppercase
# see https://www.eggradients.com/shades-of-color or https://rgbcolorpicker.com/random/true
# also see https://rich.readthedocs.io/en/latest/appendix/colors.html#appendix-colors for more colors
RULE_COLORS = [
    "#79FB00",
    "#FF9D00",
    "#0800FF",
    "#F1ADF5",
    "#DF228B",
    "#EBCB57",
    "#8245BD",
    "#FF69B4",
    "#A71D44",
    "#6FC4EE",
    "#B20FFD",
    "#1A9050",
    "#FD9E7b",
    "#593328",
    "#521D7D",
    "#00FF7F",
    "#FF7780",
    "#F22410",
    "#EE8727",
    "#AF4109",
    "#F2E32D",
    "#BC0B6F",
    "#2BAE7B",
    "#01FF01",
    "#01796F",
    "#CE5908",
    "#A94064",
    "#FF007F",
    "#FF77FF",
    "#FF66CC",
    "#EDC9AF",
    "#F0DC82",
    "#0095FD",
    "#40E0D0"
    "#BE7437",
    "#9BB09E",
    "#FFBF00",
    "#00FFFF",
    "#D7AF00"
]
def r_names_perm_order(rl, permutation, permutation_order):
    permutation = permutation if(permutation_order) else range(len(rl))
    return([rl[i].name for i in permutation])
def rules_list_to_names_list(rl, pad=True, permutation=None):
    """
    Input: rl: the rule list of an answer combination.
    If a permutation is given, will list the rule names in permutation order w/"{name_of_rule_card}: " preceding it, otherwise, in standard order w/o name of rule card.
    """
    pad_spaces = rules.max_rule_name_length if(pad) else 0
    if(permutation is not None):
        pad_spaces += 3 if pad else 0
        names = [f'{letters[r_index]} {rl[r_index].name}'.ljust(pad_spaces) for r_index in permutation]
    else:
        names = [f'{r.name:<{pad_spaces}}' for r in rl]
    return(names)
def rules_list_to_names(rl, pad=True, permutation=None):
    names = rules_list_to_names_list(rl, pad, permutation)
    return(' '.join(names))
def make_r_name_list(rules_list, permutation, permutation_order):
    """
    If permutation_order, will output a list like this:
        ['C', 'square_lt_3', 'A', 'triangle_gt_square' . . .]
    otherwise, will just output the names in rule card order, without a string for the rule card name.
    """
    if(not(permutation_order)):
        permutation = None
    r_name_list = []
    for r_name in rules_list_to_names_list(rules_list, permutation=permutation, pad=False):
        if(permutation_order):
            r_name_list.append(r_name[0]) # append the name of the rule card to list.
        r_name_list.append(r_name[(2 if permutation_order else 0):])
    return(r_name_list)
def _make_rule_to_color_dict(combos):
    d = dict()
    color_index = 0
    for c in combos:
        for r in c:
            if(r.unique_id not in d):
                d[r.unique_id] = RULE_COLORS[color_index % len(RULE_COLORS)]
                color_index += 1
    if(color_index > len(RULE_COLORS)):
        print("WARN: Add more rule colors, or programmatically generate them")
    return(d)

def _make_list_objs_to_color_dict(list_objs):
    color_index = 0
    d = dict()
    for obj in list_objs:
        if(obj not in d):
            d[obj] = RULE_COLORS[len(RULE_COLORS) - 1 - (color_index % len(RULE_COLORS))]
            color_index += 1
    return(d)

def _get_sort_key(n_mode, n_wo_p, verifier_to_sort_by=None):
    if((verifier_to_sort_by is not None) and not(n_wo_p)):
        def sort_by_rule_assigned_to_verifier(cwa):
            """
            Sort by answer, then the unique_id of the rule assigned to the verifier_to_sort_by, then by the unique_ids of the combo, and then by the permutation, if there is one.
            """
            (c, p, a) = (cwa[0], cwa[1], cwa[-1])
            p = range (len(c)) if(not(n_mode)) else p
            id_rule_assigned_to_verifier = c[p[verifier_to_sort_by]].unique_id
            return(
                (a, id_rule_assigned_to_verifier, tuple([r.unique_id for r in c])) +\
                      ((p,) if n_mode else tuple())
            )
        return(sort_by_rule_assigned_to_verifier)
    def default_sort(cwa):
        """
        Sort by answer, then by the unique_ids of the combo, and then by the permutation, if there is one.
        """
        (c, p, a) = (cwa[0], cwa[1], cwa[-1])
        return((a, tuple([r.unique_id for r in c])) + ((p,) if n_mode else tuple()))
    return(default_sort)

def _get_col_widths(table):
    """
    Note: table is not a Rich table; it's just a 2d array of objects that will later be converted into strings and right adjusted.
    """
    num_cols = len(table[0])
    max_length_by_column = [0] * num_cols
    new_table = [[str(elem) for elem in row] for row in table]
    for row in new_table:
        for (col, elem) in enumerate(row):
            max_length_by_column[col] = max(max_length_by_column[col], len(elem))
    return(max_length_by_column)

def _print_indented_table(table, indent_amount):
    """
    table is the Rich python object.
    """
    # for some reason, returning the table as a string with indents inserted and printing that doesn't seem to work.
    with console.capture() as capture:
        console.print(table)
    table_lines = capture.get().split("\n")
    for line in table_lines:
        print(f'{" " * indent_amount}{line}')

def _apply_style_to_r_names(
        r_names_list,
        verifier_to_sort_by,
        permutation_order,
        rule_to_style_dict,
        c,
        p,
        color_all=False,
        single_out_queried=True
    ):
    """
    Colors each unique rule with a different color. If color_all is on, colors every rule in the combo; otherwise only colors the rule in the column index specified by verifier_to_sort_by. Additionally
    """
    if(color_all):
        v_indexes_to_change = range(len(c))
    elif((verifier_to_sort_by is not None) and single_out_queried):
        v_indexes_to_change = [verifier_to_sort_by]
    else:
        return
    for v_index in v_indexes_to_change:
        r_names_indices_to_change = ([v_index * 2, v_index * 2 + 1] if(permutation_order) else [v_index])
        rule_to_style = c[p[v_index]] if(permutation_order) else c[v_index]
        base_style = rule_to_style_dict[rule_to_style.unique_id]
        v_single_out_style = f"r {base_style}" if(color_all and single_out_queried) else base_style
        single_out_this_v_index = ((v_index == verifier_to_sort_by) and single_out_queried)
        apply_style = v_single_out_style if(single_out_this_v_index) else base_style
        for i in r_names_indices_to_change:
            r_names_list[i] = Text(r_names_list[i], style=apply_style)

def print_list_cwa(cwas, mode, message = "", use_round_indent=False, custom_indent=None, active=True):
    if(not active):
        return
    indent = ROUND_INDENT if(use_round_indent) else ""
    if(message[0] == '\n'):
        indent = '\n' + indent
        message = message[1:]
    print(indent + message)
    sort_key = (lambda t: (t[2], t[1], [r.card_index for r in t[0]])) if (mode == NIGHTMARE) else \
        (lambda t: (t[-1], [r.card_index for r in t[0]]))
    for (i, cwa) in enumerate(sorted(cwas, key=sort_key)):
        print_combo_with_answer(i, cwa, mode, use_round_indent, custom_indent=custom_indent)
def print_combo_with_answer(index, cwa, mode, use_round_indent=False, custom_indent=0):
    indent = ROUND_INDENT if(use_round_indent) else (" " * custom_indent)
    (combo, permutation, answer) = [cwa[i] for i in (0, 1, -1)]
    permutation_string = f", permutation: {permutation}" if(mode == NIGHTMARE) else ''
    print(f'{indent}{index + 1:>3}: {answer} {rules_list_to_names(combo)}, rules_card_indices: {[r.card_index for r in combo]}{permutation_string}')
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
    print(f"{ROUND_INDENT}Query verifier: {letters[query_tup[1]]}. Expected Final Score: Rounds: {expected_winning_round:.3f}. Queries: {expected_total_queries:.3f}.")
    print(f"{ROUND_INDENT}Result of query (T/F)\n{ROUND_INDENT}> ", end="")
    result_raw = input()
    if(result_raw == 'q'):
        exit()
    result = (result_raw in ['T', 't'])
    return(result)
def display_query_history(query_history, num_rcs):
    separator = ""
    if(query_history):
        print("\n" + (" " * 8) + separator.join(letters[:num_rcs]))
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
        self.rule_to_color_dict = _make_rule_to_color_dict([cwa[0] for cwa in self.solver.full_cwa])
        self.card_index_to_color_dict = _make_list_objs_to_color_dict(
            [tuple([r.card_index for r in cwa[0]]) for cwa in solver.full_cwa]
        )
        self.n_mode = (self.solver.problem.mode == NIGHTMARE)
        # note that the below is different from the max rule name length in the problem, b/c not all rules in the problem are actually possible.
        self.max_possible_rule_length = max([max([len(r.name) for r in cwa[0]]) for cwa in solver.full_cwa], default=0)

    def print_problem(self, rcs_list, problem, active=True):
        modes = ["Standard", "Extreme", "Nightmare"]
        if(active):
            title = f"\nProblem: {problem.identity}. Mode: {modes[problem.mode]}"
            table = Table(title=title, header_style="deep_sky_blue3", border_style="blue", title_style='')
            table.add_column("Rule Index", justify="right")
            for c_index in range(len(rcs_list)):
                rc_text = f'Rule Card {letters[c_index]}'
                min_width = max(rules.max_rule_name_length, len(rc_text))
                table.add_column(Text(rc_text, justify="center"), min_width=min_width)
            zipped_rule_texts = zip_longest(*[[Text(r.name, style=self.rule_to_color_dict.get(r.unique_id, 'dim')) for r in rc] for rc in rcs_list], fillvalue='')
            for (i, zipped_rules) in enumerate(zipped_rule_texts):
                table.add_row(str(i), *zipped_rules)
            console.print(table)

    def get_card_indexes_text(self, card_index_col_widths, c):
        card_indexes_list = [r.card_index for r in c]
        card_indexes_strings_list = [
            str(ci).rjust(card_index_col_widths[col]) for (col, ci) in enumerate(card_indexes_list)
        ]
        card_indexes_text = Text()
        for (combo_index, c_index_str) in enumerate(card_indexes_strings_list):
            style=self.rule_to_color_dict[c[combo_index].unique_id]
            card_indexes_text.append(Text(text=f'{c_index_str} ', style=style))
        return(card_indexes_text)

    def get_r_names_texts_list(self, c, p, permutation_order, verifier_to_sort_by, color_all=True):
        n_wo_p = self.n_mode and not(permutation_order)
        r_names_list = make_r_name_list(c, p, permutation_order)
        _apply_style_to_r_names(
            r_names_list, verifier_to_sort_by, permutation_order, self.rule_to_color_dict, c, p, color_all=color_all, single_out_queried=not(n_wo_p)
        )
        return(r_names_list)

    def print_all_possible_answers(
            self,
            cwas,
            title                = "",
            permutation_order    = False,
            display_combo_number = True,
            active               = True,
            use_round_indent     = False,
            verifier_to_sort_by  = None
        ):
        """
        Pretty prints a table of all the combos_with_answers (cwas) given.
        title is the title of the table. Blank by default.
        permutation_order: if this is true and it's nightmare mode, prints the rule names in permutation order.
        active: if False, this function does nothing
        use_round_indent: whether to indent the tables
        """
        if(not active):
            return
        n_mode = (self.solver.problem.mode == NIGHTMARE)
        permutation_order = permutation_order and n_mode
        n_wo_p = n_mode and not(permutation_order)
        unzipped_cwa = list(zip(*cwas))
        (combos, permutations, answers) = (unzipped_cwa[0], unzipped_cwa[1], unzipped_cwa[-1])
        set_possible_answers = set(answers)
        final_answer = (len(set_possible_answers) == 1)

        table = Table(title=title, header_style="magenta", border_style="")
        # TODO: consider making creating the columns and their titles its own function.
        rule_col_title = f"{'Rule Card' if (n_wo_p) else 'Verifier'}"
        rule_col_width = max(len(f"{rule_col_title} X"), self.max_possible_rule_length)
        if(not final_answer):
            table.add_column("", justify="right") # answer index column
        table.add_column("Ans")
        if(display_combo_number):
            table.add_column("", justify="right") # combo index column
        for (v_index, r) in enumerate(combos[0]):
            if(permutation_order):
                table.add_column("") # RC, but it took up unnecessary space
            rule_column_name = f"{rule_col_title} {letters[v_index]}"
            rule_col_style = 'r' if((v_index == verifier_to_sort_by) and not(n_wo_p)) else ''
            col_text = Text(text=rule_column_name, style=rule_col_style, justify="center")
            table.add_column(col_text, min_width=rule_col_width) # Verifier/Rule Card columns
        table.add_column("Rule Indexes")
        if(n_mode):
            table.add_column("Permutation")

        # TODO: consider making the row arguments its own function.
        sorted_cwas = sorted(cwas, key=_get_sort_key(n_mode, n_wo_p, verifier_to_sort_by))
        a_index = 0
        card_index_col_widths = _get_col_widths([[r.card_index for r in c] for c in combos])
        for (c_index, cwa) in enumerate(sorted_cwas, start=1): # note that c_index starts at 1
            (c, a) = (cwa[0], cwa[-1])
            p = cwa[1] if (n_mode) else None
            new_ans = ((c_index == 1) or (a != sorted_cwas[c_index - 2][-1]))
            a_index += new_ans
            # NOTE: Uncomment/recomment the below if block to enable/disable lines between new answers
            # if(new_ans):
                # table.add_section()

            card_indexes_text = self.get_card_indexes_text(card_index_col_widths, c)
            r_names_texts_list = self.get_r_names_texts_list(
                c, p, permutation_order, verifier_to_sort_by, color_all=True
            )
            t_row_args = (tuple() if (final_answer) else ((str(a_index),) if(new_ans) else ('',))) +\
                ((str(a),) if(new_ans) else ('',))  +\
                ((str(c_index),) if(display_combo_number) else tuple()) +\
                tuple(r_names_texts_list) + \
                (card_indexes_text,) + \
                ( ( f'{" ".join([str(r_index) for r_index in p])}', )  if(n_mode) else tuple())
            table.add_row(*t_row_args)
        if(use_round_indent):
            _print_indented_table(table, ROUND_INDENT_AMOUNT)
        else:
            console.print(table)

    def print_evaluations_cache_info(self, gs, name="game state", permutation_order=True):
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
        self.print_game_state(gs, name=name, permutation_order=permutation_order)
        print(f"Expected cost to win from current state: {ec_rounds:0.3f} rounds. {ec_queries:0.3f} queries.")
        print(f"Best move: {mov_to_str(best_mov)}")
        (r_cost, q_cost) = best_mov_cost_tup
        print(f"Cost of best move: {r_cost} round{'' if (r_cost == 1) else 's'}. {q_cost} query.")
        print(f"Probability query returns False: {p_false:0.3f}")
        print(f"Probability query returns True : { p_true:0.3f}")

        print(f"Expected cost to win after false query: {expected_cost_false[0]:0.3f} rounds. {expected_cost_false[1]:0.3f} queries.")
        print(f"Expected cost to win after true query : {expected_cost_true[0]:0.3f} rounds. {expected_cost_true[1]:0.3f} queries.")
        self.print_game_state(
            gs_false, "Game State if query returns false:", verifier_to_sort_by=best_mov[1], permutation_order=permutation_order
        )
        self.print_game_state(
            gs_true, "Game State if query returns true:", verifier_to_sort_by=best_mov[1], permutation_order=permutation_order
        )
        ec_rounds_calculated = r_cost + p_false*expected_cost_false[0] + p_true*expected_cost_true[0]
        ec_queries_calculated = q_cost + p_false*expected_cost_false[1] + p_true*expected_cost_true[1]
        if(not(math.isclose(ec_rounds, ec_rounds_calculated))):
            print("O noes! But maybe floating point error?")
            print(f"Difference is: {abs(ec_rounds - ec_rounds_calculated)}")
            exit()
        if(not(math.isclose(ec_queries, ec_queries_calculated))):
            print("O noes! But maybe floating point error?")
            print(f"Difference is: {abs(ec_queries - ec_queries_calculated)}")
            exit()
        return(best_gs_tup)

    def print_game_state(
            self,
            gs,
            name="game_state",
            verifier_to_sort_by=None,
            permutation_order=True,
            active=True
        ):
        if(not active):
            return
        print(f'\n{name}')
        print(f'num_queries_this_round  : {gs.num_queries_this_round}.')
        print(f'proposal_used_this_round: {gs.proposal_used_this_round}')
        self.print_all_possible_answers(
            cwas=self.solver.full_cwa_from_game_state(gs),
            title="Combos With Answers Remaining",
            permutation_order=permutation_order,
            verifier_to_sort_by=verifier_to_sort_by
        )

    @staticmethod
    def get_rl_by_card_dict(rcs_list, rc_infos, v_index):
        """
        In nightmare mode, given the rcs_list, the rc_infos (which can be obtained from the solver class static method) and a verifier index, returns a dictionary where the keys are the rc_indexes of rules cards this verifier could correspond to, and the values are lists of rules within this rules card that the verifier could be checking.
        """
        corresponding_rc_info = rc_infos[v_index]
        rules_list_by_corresponding_card_dict = dict()
        for (rc_index, rule_index) in corresponding_rc_info.keys():
            rule = rcs_list[rc_index][rule_index]
            if(rc_index in rules_list_by_corresponding_card_dict):
                rules_list_by_corresponding_card_dict[rc_index].append(rule)
            else:
                rules_list_by_corresponding_card_dict[rc_index] = [rule]
        for rc_index in rules_list_by_corresponding_card_dict:
            rules_list_by_corresponding_card_dict[rc_index].sort(key=lambda r: r.card_index)
        return(rules_list_by_corresponding_card_dict)

    @staticmethod
    def print_rules_this_verifier(rl_by_card_dict, v_index, include_v_name=True):
        """
        Only used in nightmare mode. Given a dict from the get_rl_by_card_dict function and a verifier index, prints out a list of all the rules this verifier could correspond to. Mainly used in print_useful_qs_dict.
        """
        if(include_v_name):
            print(f"\nFor Verifier {letters[v_index]}:")
        for (rc_index, rule_list) in sorted(rl_by_card_dict.items()):
            print(f"    Rule Card {letters[rc_index]}: {rules_list_to_names(rule_list)}")

    def print_useful_qs_dict_info(self, useful_qs_dict, v_index, rc_infos, rcs_list, mode, see_all_combos=True):
        """
        Displays all information in the useful_queries_dict about a specific rules card. Note: will need the rc_infos used to make the useful_queries_dict, and the rc_list.
        """
        q_dict_this_card = dict()
        for (q, inner_dict) in sorted(useful_qs_dict.items()):
            if(v_index in inner_dict):
                q_info = inner_dict[v_index]
                q_dict_this_card[q] = q_info
        corresponding_rc_info = rc_infos[v_index]
        if(mode == NIGHTMARE):
            rules_list_by_corresponding_card_dict = self.get_rl_by_card_dict(rcs_list, rc_infos, v_index)
            self.print_rules_this_verifier(rules_list_by_corresponding_card_dict, v_index)
        else:
            possible_rules_this_verifier = \
                [rcs_list[v_index][rule_index] for rule_index in corresponding_rc_info.keys()]
            possible_rules_this_verifier.sort(key = lambda r: r.card_index)
            print(f'\nFor Verifier {letters[v_index]}. Possible rules: {rules_list_to_names(possible_rules_this_verifier)}')

        print(f"# useful queries this card: {len(q_dict_this_card)}")
        for (q, q_info) in sorted(q_dict_this_card.items()):
            print(f"\n{(' ' * 0)}{q} {letters[v_index]}") # print query

            # print(f'{" " * 8} {"expected_a_info_gain":<25}: {q_info.expected_a_info_gain:.3f}')
            # print(f'{" " * 8} {"p_true":<25}: {q_info.p_true:.3f}')
            # print(f'{" " * 8} {"a_info_gain_true":<25}: {q_info.a_info_gain_true:0.3f}')

            custom_indent = 4
            message_indent = 4
            (full_cwa_false, full_cwa_true) = \
                [[self.solver.rc_indexes_cwa_to_full_combos_dict[indexes] for indexes in q_info_set_indexes] for q_info_set_indexes in (q_info.set_indexes_cwa_remaining_false, q_info.set_indexes_cwa_remaining_true)]

            if(mode == NIGHTMARE):
                (rc_infos_false, rc_infos_true) = [self.solver.make_rc_infos(len(rcs_list), cwa, NIGHTMARE) for cwa in (full_cwa_false, full_cwa_true)]
                (rlbccd_false, rlbccd_true) = [self.get_rl_by_card_dict(rcs_list, rc_info, v_index) for rc_info in (rc_infos_false, rc_infos_true)]
                print(f"Possible rules if query returns True:")
                self.print_rules_this_verifier(rlbccd_true, v_index, include_v_name=False)

                print(f"\nPossible rules if query returns False:")
                self.print_rules_this_verifier(rlbccd_false, v_index, include_v_name=False)

            if(see_all_combos):
                print_list_cwa(full_cwa_true, mode, f'\n{" " * message_indent}Combos remaining if query returns True:', custom_indent=custom_indent)

                # print()
                # print(f'{" " * 8} {"p_false":<25}: {1 - q_info.p_true:0.3f}') 
                # print(f'{" " * 8} {"a_info_gain_false":<25}: {q_info.a_info_gain_false:0.3f}')

                print_list_cwa(full_cwa_false, mode, f'\n{" " * message_indent}Combos remaining if query returns False:', custom_indent=custom_indent)



def rc_infos_inner_dict_to_string(inner_dict, mode):
    s = '{ '
    for (possibility, inner_list) in inner_dict.items():
        if(mode == NIGHTMARE):
            inner_list_to_print = [([r.card_index for r in combo], permutation) for (combo, permutation) in inner_list]
        else:
            inner_list_to_print = [[r.card_index for r in combo] for combo in inner_list]
        inner_list_item_indent_str = "\n" + (' ' * 12)
        inner_list_str = inner_list_item_indent_str.join([str(item) for item in inner_list_to_print])
        s += f'\n        {possibility}:{inner_list_item_indent_str}{inner_list_str} '
    s += '\n    }'
    return(s)

def print_rc_info(rc_infos, rc_index, mode):
    rc_info = rc_infos[rc_index]
    print(f'\nVerifier {letters[rc_index]}:' + ' {')
    for (outer_dict_key, inner_dict) in rc_info.items():
            if(mode == NIGHTMARE):
                (rc_num, rule_index) = outer_dict_key
                outer_key_str = f"\n    Rule Card {letters[rc_num]}, Rule Index {rule_index} :"
            else:
                outer_key_str = f"\n    Rule Index {outer_dict_key} :"
            print(f'    {outer_key_str} {rc_infos_inner_dict_to_string(inner_dict, mode)}')
    print('}')

def mov_to_str(move: tuple):
    return(f"{move[0]} {letters[move[1]]}.")

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
    max_combos_by_depth = []    # array[i] is the maximum number of combos of an internal node at depth i, considering the root to be at depth 0. Set when making each tree.
    def __init__(
            self,
            gs,
            solver,
            prob=1.0,
            cost_to_get_here=(0, 0),
            depth=0,
            tree_type='gs',
            move=None,                  # NOTE: not currently used. Intended to be used for 'move' type trees, which show multiple move options other than best move, if that gets implemented.
    ):
        # prob is the probability of getting to this gs from the query above it in the best move tree
        self.gs = gs
        self.solver = solver
        self.prob = prob
        self.cost_to_get_here = cost_to_get_here
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
        if((tree.solver.evaluations_cache is not None) and (tree.gs in tree.solver.evaluations_cache)):
            result = tree.solver.evaluations_cache.get(tree.gs)
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
                # TODO: use the tree.solver to get some other useful moves that lead to different tree shapes than the best move, get their costs and resulting gs_tups and probabilities, and return some children moves that you want to see. Pretty sure you can do this with get_and_apply_moves.
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
    if((tree.solver.evaluations_cache is not None) and (tree.gs in tree.solver.evaluations_cache)):
        result = tree.solver.evaluations_cache.get(tree.gs)
        if(result is not None):
            (best_move, best_move_cost, gs_tup, total_expected_cost) = result
            current_num_combos = len(tree.gs.fset_cwa_indexes_remaining)
            num_combos_if_q_true = len(gs_tup[1].fset_cwa_indexes_remaining)
            p_true = num_combos_if_q_true / current_num_combos
            p_false = 1 - p_true
            prob_tup = (p_false, p_true)
            children = [
                Tree(
                    gs=gs_tup[i],
                    solver=tree.solver,
                    prob=prob_tup[i],
                    cost_to_get_here=add_tups(tree.cost_to_get_here, best_move_cost),
                    depth=tree.depth+1
                ) for i in range(2)
            ]
            return(children)
    return([])
def node_to_str(tree):
    nl = '\n'
    rcs_lengths = [len(rc) for rc in tree.solver.rcs_list]
    chars_to_print = [2 if (i > 10) else 1 for i in rcs_lengths] # chars_to_print[i] is the number of chars needed to print a rule index on the ith rule card, since some rule cards have over 10 rules on them, so rule index 10 (zero-based) will need two characters to print.
    if((tree.solver.evaluations_cache is not None) and (tree.gs in tree.solver.evaluations_cache)):
        result = tree.solver.evaluations_cache.get(tree.gs)
        if(result is not None): # internal node
            combos_l = sorted(tree.gs.fset_cwa_indexes_remaining, key = lambda t: t[1])
            (best_move, best_move_cost, gs_tup, total_expected_cost) = result
            combos_strs = [f"{n:>2}. {c[1]}: {' '.join(str(f'{i:>{chars_to_print[rc_ind]}}') for (rc_ind, i) in enumerate(c[0]))}" for (n, c) in enumerate(combos_l, start=1)]
            prob_str = f"{tree.prob:0.3f}" # Note: in format 0.123
            prob_str = f"{prob_str[2:4]}.{prob_str[4]}%"
            move_str = f"{best_move[0]} {letters[best_move[1]]}"
            # NOTE: comment out below if block to not mark new rounds in the best move tree
            if(best_move_cost[0] == 1): # if the best move costs a round
                move_str += ' (R)'
            cost_of_node_str = ' '.join([f'{add_tups(tree.cost_to_get_here, total_expected_cost)[i]:.3f}' for i in range(2)])
            verifier_names_str = (" " * 9) + ' '.join( # NOTE: change the 9 if change combo lines beginning
                [f'{letters[i]:>{chars_to_print[i]}}' for i in range(len(combos_l[0][0]))]
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
            lines = [f"{l:^{max_line_length}}" for l in lines] # the ^ centers the lines
            node_str = f"{nl.join(lines)}"
            return(node_str)
    else: # leaf node
        l = list(tree.gs.fset_cwa_indexes_remaining)
        answer = l[0][-1]
        return(answer)

def print_best_move_tree(gs, show_combos, solver):
    print()
    Tree.show_combos_in_tree = show_combos
    tree = Tree(gs=gs, solver=solver)
    Tree.max_combos_by_depth = get_max_string_height_by_depth(tree)
    pt = PrettyPrintTree(get_children, node_to_str)
    pt(tree)

def print_multi_move_tree(gs, show_combos, solver):
    raise Exception("Unimplemented")
    print()
    Tree.show_combos_in_tree = show_combos
    tree = Tree(gs)
    pt = PrettyPrintTree(get_children_multi_move, node_to_str_multi_move)
    pt(tree)