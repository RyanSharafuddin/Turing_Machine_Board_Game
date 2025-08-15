import string, math
from itertools import zip_longest
from collections import deque
from PrettyPrint import PrettyPrintTree
# import colorama
from rich.table import Table
from rich.text import Text
from rich import box
from rich import print as rprint
import solver
from definitions import NIGHTMARE, console

# escape sequence is \033[<text color>;<background color>m
# see https://gist.github.com/fnky/458719343aabd01cfb17a3a4f7296797
# NOTE: for some reason that probably has to do with VS Code color themes, the checks and Xs don't display how I want them to in the terminal when using the Radical theme, but they do display correctly when using the Terminal app, or with certain other VS Code themes.
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
    "#9C5642",
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
def rules_list_to_names_list(rl, permutation=None):
    """
    Input: rl: the rule list of an answer combination.
    If a permutation is given, will list the rule names in permutation order w/ "{name_of_rule_card} " preceding it, otherwise, in standard order w/o name of rule card.
    """
    if(permutation is not None):
        names = [f'{letters[r_index]} {rl[r_index].name}' for r_index in permutation]
    else:
        names = [f'{r.name}' for r in rl]
    return(names)
def make_r_name_list(rules_list, permutation, permutation_order):
    """
    If permutation_order, will output a list like this:
        ['C', 'square_lt_3', 'A', 'triangle_gt_square' . . .]
    otherwise, will just output the names in rule card order, without a string for the rule card name.
    """
    if(not(permutation_order)):
        permutation = None
    r_name_list = []
    for r_name in rules_list_to_names_list(rules_list, permutation=permutation):
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

def display_query_num_info(current_round_num, query_this_round, total_query, new_round: bool, proposal):
    if(new_round):
        # print(f"\nRound   : {current_round_num:>3}")
        # print(f"Proposal: {proposal}")
        title = Text(f"Round {current_round_num} Proposal {proposal}")
        # console.print(title, justify="center")
        console.rule(title=title)
    q_newline = "\n" #if(query_this_round == 1) else ""
    print(f"{q_newline}{ROUND_INDENT}Query: {query_this_round}. Total query: {total_query}.")
def conduct_query(query_tup, expected_winning_round, expected_total_queries):
    """
    Asks user to conduct a query and input result, and returns result. Exits if user enters 'q'.
    """
    (proposal, verifier_to_query) = (query_tup[0], letters[query_tup[1]])
    print(f"{ROUND_INDENT}Expected Final Score: Rounds: {expected_winning_round:.3f}. Queries: {expected_total_queries:.3f}.")
    print(f"{ROUND_INDENT}Result of query (T/F)\n{ROUND_INDENT}", end="")
    console.print(Text(str(proposal)), Text(str(verifier_to_query)), highlight=False, end="")
    result_raw = input(': ')
    if(result_raw == 'q'):
        exit()
    result = (result_raw in ['T', 't', '1'])
    return(result)
def display_query_history(query_history, num_rcs, use_table=True):
    """
    If use_table is True, will print query history as a table; otherwise will just use text with spacing.
    """
    result_table = Table(padding=0, header_style="b", show_lines=True, title_style="", title="Query History")
    separator_string = ""
    separator = Text(separator_string, style="")
    result_displays = [
        Text("X", style="b white on red"),   # False
        Text("✓", style="b white on green"), # True
        Text(' ', style="")           # not queried
    ]
    emoji_displays = [        # maybe use in future
        Text("❌", style=""), # False
        Text("✅", style=""), # True
        Text('  ', style="")   # not queried
    ]
    if(query_history):
        if(not use_table):
            print("\n" + (" " * 8) + separator_string.join(letters[:num_rcs]))
        result_table.add_column() # round num
        result_table.add_column() # proposal
        for i in range(num_rcs):
            result_table.add_column(f"{letters[i]}")
        for (round_num, round_info) in enumerate(query_history, start=1):
            proposal = round_info[0]
            verifier_info = [2 for i in range(num_rcs)]
            for (v, result) in round_info[1:]:
                verifier_info[v] = result
            display_text = Text("")
            for result in verifier_info:
                display_text.append(result_displays[result])
                display_text.append(separator)
            row_args = [str(round_num), str(proposal)] + [result_displays[result] for result in verifier_info]
            result_table.add_row(*row_args)
            if(not use_table):
                console.print(f"{round_num}: {proposal}: ", display_text, highlight=False, sep="")
        if(use_table):
            console.print("\n", result_table, end="")

class Solver_Displayer:
    def __init__(self, solver: solver.Solver):
        self.solver = solver
        self.rule_to_color_dict = _make_rule_to_color_dict([cwa[0] for cwa in self.solver.full_cwa])
        self.card_index_to_color_dict = _make_list_objs_to_color_dict(
            [tuple([r.card_index for r in cwa[0]]) for cwa in solver.full_cwa]
        )
        self.n_mode = (self.solver.problem.mode == NIGHTMARE)
        self.max_rule_name_length = max([max([len(r.name) for r in rc]) for rc in self.solver.rcs_list])
        # note that max_possible_rule_length is different from max_rule_name_length,
        # b/c not all rules in the problem are necessarily possible.
        self.max_possible_rule_length = max(
            [max([len(r.name) for r in cwa[0]]) for cwa in solver.full_cwa], default=0
        )


    def print_problem(self, rcs_list, problem, active=True):
        modes = ["Standard", "Extreme", "Nightmare"]
        if(active):
            title = f"\nProblem: {problem.identity}. Mode: {modes[problem.mode]}"
            self.print_rcs_list(rcs_list, title)

    def print_rcs_list(self, rcs_list, title, active=True):
        if(active):
            table = Table(title=title, header_style="deep_sky_blue3", border_style="blue", title_style='')
            table.add_column("Rule Index", justify="right")
            for c_index in range(len(rcs_list)):
                rc_text = f'Rule Card {letters[c_index]}'
                min_width = max(self.max_rule_name_length, len(rc_text))
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

    def make_answer_table_cols(self, table, p_order, final_answer, display_combo_number, verifier_to_sort_by):
        n_wo_p = self.n_mode and not(p_order)
        rule_col_title = f"{'Rule Card' if (n_wo_p) else 'Verifier'}"
        rule_col_width = max(len(f"{rule_col_title} X"), self.max_possible_rule_length)
        if(not final_answer):
            table.add_column("", justify="right") # answer index column
        table.add_column("Ans")                   # answer       column
        if(display_combo_number):
            table.add_column("", justify="right") # combo index column
        for v_index in range(len(self.solver.rcs_list)):
            if(p_order):
                table.add_column("")              # RC          column (nightmare mode only)
            rule_column_name = f"{rule_col_title} {letters[v_index]}"
            rule_col_style = 'r' if((v_index == verifier_to_sort_by) and not(n_wo_p)) else ''
            col_text = Text(text=rule_column_name, style=rule_col_style, justify="center")
            table.add_column(col_text, min_width=rule_col_width) # Verifier/Rule Card columns
        table.add_column("Rule Indexes")          # Rule Indexes column
        if(self.n_mode):
            table.add_column("Permutation")       # Permutation column (nightmare mode only)

    def print_all_possible_answers(
            self,
            cwas,
            title                = "",
            permutation_order    = False,
            display_combo_number = True,
            active               = True,
            use_round_indent     = False,
            verifier_to_sort_by  = None,
            custom_indent        = 0
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

        table = Table(title=title, header_style="magenta", border_style="", title_style="")
        self.make_answer_table_cols(
            table, permutation_order, final_answer, display_combo_number, verifier_to_sort_by
        )
        # NOTE: Set LINES_BETWEEN_ANSWERS to True/False to enable/disable lines between new answers
        LINES_BETWEEN_ANSWERS = False

        # TODO: consider making the row arguments its own function.
        sorted_cwas = sorted(cwas, key=_get_sort_key(n_mode, n_wo_p, verifier_to_sort_by))
        a_index = 0
        card_index_col_widths = _get_col_widths([[r.card_index for r in c] for c in combos])
        for (c_index, cwa) in enumerate(sorted_cwas, start=1): # note that c_index starts at 1
            (c, a) = (cwa[0], cwa[-1])
            p = cwa[1] if (n_mode) else None
            new_ans = ((c_index == 1) or (a != sorted_cwas[c_index - 2][-1]))
            a_index += new_ans
            if(new_ans and LINES_BETWEEN_ANSWERS):
                table.add_section()

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
        if(use_round_indent or (custom_indent != 0)):
            indent_amount = ROUND_INDENT_AMOUNT if(use_round_indent) else custom_indent
            _print_indented_table(table, indent_amount)
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

    def print_possible_rules_by_verifier_from_cwas(self, full_cwas, v_index, title):
        """
        Given a list of full_cwas and a verifier index, prints a table of all rules that are possible for that verifier (derived from the cwas).
        """
        rule_ids_by_verifier = solver.get_set_r_unique_ids_vs_from_full_cwas(full_cwas, self.n_mode)
        # Now print a table (or tables, if n_mode) of all possible rules for each verifier.
        possible_rules_this_verifier = [
            self.solver.flat_rule_list[r_id] for r_id in sorted(rule_ids_by_verifier[v_index])
        ]
        rcs_list_possible = []
        if(self.n_mode):
            finish_possible_rules = False
            possible_rules_this_v_pointer = 0
            for rc in self.solver.rcs_list:
                rc_in_rcs_list_possible = []
                rcs_list_possible.append(rc_in_rcs_list_possible)
                if(finish_possible_rules):
                    continue
                for r in rc:
                    if(r.unique_id == possible_rules_this_verifier[possible_rules_this_v_pointer].unique_id):
                        rc_in_rcs_list_possible.append(
                            possible_rules_this_verifier[possible_rules_this_v_pointer]
                        )
                        possible_rules_this_v_pointer += 1
                        if(possible_rules_this_v_pointer == len(possible_rules_this_verifier)):
                            finish_possible_rules = True
                            break
        else:
            for i in range(len(self.solver.rcs_list)):
                rcs_list_possible.append(possible_rules_this_verifier if(i == v_index) else [])
        self.print_rcs_list(
            rcs_list_possible, title
        )

    def print_useful_qs_dict_info_helper(
        self, useful_qs_dict, full_cwas, v_index, proposal_to_examine=None, see_all_combos=True
    ):
        """
        Displays all information in the useful_queries_dict about a specific verifier card/proposal.
        If proposal_to_examine is none, will print info about all useful proposals.
        Note: will need the full_cwas used to make this useful_queries_dict.
        """
        q_dict_this_card = dict()
        for (proposal, inner_dict) in sorted(useful_qs_dict.items()):
            if(v_index in inner_dict):
                q_info = inner_dict[v_index]
                q_dict_this_card[proposal] = q_info

        possible_rules_title = f"\nVerifier {letters[v_index]} Rules Possible When This Qs Dict Was Made"
        self.print_possible_rules_by_verifier_from_cwas(full_cwas, v_index, title=possible_rules_title)
        print(f"# useful queries for Verifier {letters[v_index]}: {len(q_dict_this_card)}")
        for (prop_index, (proposal, q_info)) in enumerate(sorted(q_dict_this_card.items()), start=1):
            if not ((proposal_to_examine == proposal) or (proposal_to_examine is None)):
                continue
            custom_indent = 4
            (full_cwa_false, full_cwa_true) = \
                [[self.solver.rc_indexes_cwa_to_full_combos_dict[indexes] for indexes in q_info_set_indexes] for q_info_set_indexes in (q_info.set_indexes_cwa_remaining_false, q_info.set_indexes_cwa_remaining_true)]

            possible_rules_true_title = f"\n{prop_index}: Verifier {letters[v_index]} Rules Possible if {proposal} True"
            self.print_possible_rules_by_verifier_from_cwas(
                full_cwa_true, v_index, title=possible_rules_true_title
            )

            possible_rules_false_title = f"\n{prop_index}: Verifier {letters[v_index]} Rules Possible if {proposal} False"
            self.print_possible_rules_by_verifier_from_cwas(
                full_cwa_false, v_index, title=possible_rules_false_title
            )

            if(see_all_combos):
                self.print_all_possible_answers(
                    cwas=full_cwa_true,
                    title=f"\n{prop_index}: Combos Remaining If {proposal} {letters[v_index]} True",
                    permutation_order=True,
                    verifier_to_sort_by=v_index,
                    custom_indent=custom_indent
                )
                self.print_all_possible_answers(
                    cwas=full_cwa_false,
                    title=f"\n{prop_index}: Combos Remaining If {proposal} {letters[v_index]} False",
                    permutation_order=True,
                    verifier_to_sort_by=v_index,
                    custom_indent=custom_indent
                )

    def print_useful_qs_dict_info(
        self, useful_qs_dict, full_cwas, verifier_index=None, proposal_to_examine=None, see_all_combos=True
    ):
        """
        Displays all information in the useful_queries_dict about a specific verifier card/proposal.
        If either verifier_index or proposal_to_examine is none, will print info about all verifiers or all useful proposals, respectively. Note that if proposal_to_examine is not a useful proposal for the given verifier_index (or any verifier_index, if it's None), will print no information about it.
        Note: will need the full_cwas used to make this useful_queries_dict.
        """
        for possible_v_index in range(len(self.solver.rcs_list)):
            if((verifier_index is None) or (possible_v_index == verifier_index)):
                self.print_useful_qs_dict_info_helper(
                    useful_qs_dict, full_cwas, possible_v_index, proposal_to_examine, see_all_combos
                )

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