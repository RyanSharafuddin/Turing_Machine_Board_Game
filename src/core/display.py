import string, math, os
from itertools import zip_longest
from collections import deque
import numpy as np
from PrettyPrint import PrettyPrintTree
from rich.table import Table
from rich.text import Text
from rich.highlighter import ReprHighlighter
from rich import box
# My imports
from . import solver
from .definitions import *
from .config import *

MODE_NAMES = ["Standard", "Extreme", "Nightmare"]
BIT_ONE_TEXT = Text('1', style="bright_green")
BIT_ZERO_TEXT = Text('0', style="bright_red")

letters = string.ascii_uppercase
def _r_names_perm_order(rl, permutation, permutation_order):
    permutation = permutation if(permutation_order) else range(len(rl))
    return([rl[i].name for i in permutation])
def _rules_list_to_names_list(rl, permutation=None):
    """
    Input: rl: the rule list of an answer combination.

    If a permutation is given, will list the rule names in permutation order w/ "{name_of_rule_card} " preceding it, otherwise, in standard order w/o name of rule card.
    """
    if(permutation is not None):
        names = [f'{letters[r_index]} {rl[r_index].name}' for r_index in permutation]
    else:
        names = [f'{r.name}' for r in rl]
    return(names)
def _make_r_name_list(rules_list, permutation, permutation_order):
    """
    If permutation_order, will output a list like this:
        ['C', 'square_lt_3', 'A', 'triangle_gt_square' . . .]
    otherwise, will just output the names in rule card order, without a string for the rule card name.
    """
    if(not(permutation_order)):
        permutation = None
    r_name_list = []
    for r_name in _rules_list_to_names_list(rules_list, permutation=permutation):
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
                d[r.unique_id] = COLORS[color_index % len(COLORS)]
                color_index += 1
    if(color_index > len(COLORS)):
        print("WARN: Add more rule colors, or programmatically generate them")
    return(d)
def _make_objs_to_color_dict(list_objs):
    color_index = 0
    d = dict()
    for obj in list_objs:
        if(obj not in d):
            d[obj] = COLORS[len(COLORS) - 1 - (color_index % len(COLORS))]
            color_index += 1
    return(d)
def _get_sort_key(n_mode, n_wo_p, verifier_to_sort_by=None):
    if((verifier_to_sort_by is not None) and not(n_wo_p)):
        def sort_by_rule_assigned_to_verifier(cwa):
            """
            Sort by answer, then the unique_id of the rule assigned to the verifier_to_sort_by, then by the unique_ids of the combo, and then by the permutation, if there is one.
            """
            (c, p, a) = (cwa[0], cwa[1], cwa[-1])
            p = (list(range(len(c)))) if(not(n_mode)) else p
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
    num_cols = max(len(table[i]) for i in range(len(table)))
    max_length_by_column = [0] * num_cols
    new_table = [[str(elem) for elem in row] for row in table]
    for row in new_table:
        for (col, elem) in enumerate(row):
            max_length_by_column[col] = max(max_length_by_column[col], len(elem))
    return(max_length_by_column)
def _rich_obj_to_list_lines(rich_obj) -> list[str]:
    with console.capture() as capture:
        console.print(rich_obj)
    lines = capture.get().split("\n")
    return lines
def _print_indented_table(table, indent_amount):
    """
    table is the Rich python object.
    """
    # for some reason, returning the table as a string with indents inserted and printing that doesn't seem to work.
    table_lines = _rich_obj_to_list_lines(table)
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
def _combine(*items):
    """ Takes a variable number of renderables and combines them into a single left-aligned grid. """
    grid = Table.grid()
    for i in items:
        grid.add_row(i)
    return(grid)
def _highlight(*items):
    h = ReprHighlighter()
    l = [h(item) for item in items]
    return(l if(len(l) > 1) else l[0])
def _get_query_history_table(query_history, num_rcs, use_table=True):
    """
    WARN: will be None if there is no query history.
    If use_table is True, will print query history as a table; otherwise will just use text with spacing.
    """
    result_table = Table(
        padding=0,
        header_style="b",
        show_lines=True,
        title_style="",
        title="\nQuery History",
        caption_style=''
    )
    separator_string = ""
    separator = Text(separator_string, style="")
    width_one_chars = [
        Text("X", style="b white on red"),   # False
        Text("✓", style="b white on green"), # True
        Text(' ', style="")           # not queried
    ]
    emoji_displays = [        # maybe use in future
        Text("❌", style=""), # False
        Text("✅", style=""), # True
        Text('  ', style="")   # not queried
    ]
    table_to_use = emoji_displays
    if(query_history):
        if(not use_table):
            print("\n" + (" " * 8) + separator_string.join(letters[:num_rcs]))
        result_table.add_column() # round num
        result_table.add_column() # proposal
        for i in range(num_rcs):
            result_table.add_column(f"{'' if (table_to_use == width_one_chars) else ' '}{letters[i]}")
        for (round_num, round_info) in enumerate(query_history, start=1):
            proposal = round_info[0]
            verifier_info = [2 for i in range(num_rcs)]
            for (v, result) in round_info[1:]:
                verifier_info[v] = result
            display_text = Text("")
            for result in verifier_info:
                display_text.append(table_to_use[result])
                display_text.append(separator)
            row_args = [str(round_num), str(proposal)] + [table_to_use[result] for result in verifier_info]
            result_table.add_row(*row_args)
            if(not use_table):
                raise Exception("Ah wait, you should use_table")
                console.print(f"{round_num}: {proposal}: ", display_text, highlight=False, sep="")
        if(use_table):
            return(result_table)
def display_new_round(current_round_num, query_this_round, query_tup):
    """ This function checks if it is a new round, and displays it. If it's not a new round, does nothing. """
    proposal = query_tup[0]
    if(query_this_round == 1):
        title = Text(f"Round {current_round_num} Proposal {proposal}")
        console.rule(title=title)
def conduct_query(query_tup, expected_total_score, query_this_round, total_query):
    """
    Asks user to conduct a query and input result, and returns result. Exits if user enters 'q'.
    """
    # can include the q_round_this_line in the grid, if you want to align it with the other things.
    # currently fine as is.
    (expected_winning_round, expected_total_queries) = expected_total_score
    q_this_round_line = f"\nQuery: {query_this_round}. Total Query: {total_query}."
    console.print(q_this_round_line, justify="center", highlight=False)
    (proposal, verifier_to_query) = (query_tup[0], letters[query_tup[1]])
    round_display_str = f"Rounds: {expected_winning_round:.3f}"
    query_display_str = f"Queries: {expected_total_queries:.3f}"
    longest_line = f"Expected Final Score: {round_display_str}. {query_display_str}."

    g = Table.grid()
    # g.add_row(q_this_round_line)
    g.add_row(longest_line)
    g.add_row(f"Result of query (T/F)")
    console.print(g, justify="center")

    # below several lines is a hack to get input() where I want it
    color = "#00B7EB"
    proposal_text = Text(f'{proposal} ', style=f'u b {color}')         # add styles if desired
    verifier_text = Text(f'{verifier_to_query}') # add styles here
    term_width = os.get_terminal_size()[0]
    start_index = (term_width // 2) - (len(longest_line)//2)
    full_query_text = Text(" " * start_index).append(proposal_text.append(verifier_text))
    console.print(full_query_text, end="")

    result_raw = input(': ')
    if(result_raw == 'q'):
        exit()
    result = (result_raw in ['T', 't', '1'])
    return(result)
def cprint_if_active(active, *args, **kwargs):
    """
    If active is True, does console.print with all args/kwargs. If there is no justify in kwargs, sets it to center.
    """
    if(active):
        if("justify" not in kwargs):
            kwargs["justify"] = "center"
        console.print(*args, **kwargs)
def center_print(*args, **kwargs):
    console.print(*args, **kwargs, justify="center", highlight=True)
def mov_to_str(move: tuple):
    """ Return a move string like 123 A"""
    return(f"{move[0]} {letters[move[1]]}")
def get_move_text(move: tuple):
    """
    Return a move Text object like 152 A, where the proposal and verifier are colored with colors set in config.py.
    """
    return(
        Text.assemble(
            (f'{move[0]}', PROPOSAL_COLOR),
            " ",
            (letters[move[1]], VERIFIER_COLORS[move[1] % len(VERIFIER_COLORS)])
        )
    )
def get_filename_text(filename: str):
    """
    Return a Text object of the filename with formatting applied as per config.
    """
    return(Text(filename, style=FILENAME_COLOR))

class Solver_Displayer:
    def __init__(self, solver: solver.Solver):
        self._rule_to_color_dict = _make_rule_to_color_dict([cwa[0] for cwa in solver.full_cwas_list])
        self._answer_to_color_dict = _make_objs_to_color_dict([cwa[-1] for cwa in solver.full_cwas_list])
        if(PRINT_SD_COLOR_DICT):
            console.print(self._answer_to_color_dict)
        self._max_rule_name_length = max([max([len(r.name) for r in rc]) for rc in solver.rcs_list])
        self.max_possible_rule_length = max(
            [max([len(r.name) for r in cwa[0]]) for cwa in solver.full_cwas_list], default=0
        )
        # note that max_possible_rule_length is different from max_rule_name_length,
        # b/c not all rules in the problem are necessarily possible.
        self.solver = solver
        self.n_mode = (self.solver.n_mode)

    @staticmethod
    def _get_width_at_left_idx_col_small_p(left_index, max_elts_partition, partition: list):
        zeroth_partition_elt_index = max_elts_partition - len(partition)
        if(left_index < zeroth_partition_elt_index):
            return(0)
        correct_index = left_index - zeroth_partition_elt_index
        return(len(f'{partition[correct_index]}'))
    @staticmethod
    def _get_width_at_left_idx_col_second_p(left_index, partition: list):
        if(left_index < len(partition)):
            return(len(f'{partition[left_index]}'))
        return(0)
    def _get_card_indexes_text(self, card_index_col_widths, c):
        card_indexes_list = [r.card_index for r in c]
        card_indexes_strings_list = [
            str(ci).rjust(card_index_col_widths[col]) for (col, ci) in enumerate(card_indexes_list)
        ]
        card_indexes_text = Text()
        for (combo_index, c_index_str) in enumerate(card_indexes_strings_list):
            style=self._rule_to_color_dict[c[combo_index].unique_id]
            card_indexes_text.append(Text(text=f'{c_index_str} ', style=style))
        return(card_indexes_text)
    def _get_r_names_texts_list(self, c, p, permutation_order, verifier_to_sort_by, color_all=True):
        n_wo_p = self.n_mode and not(permutation_order)
        r_names_list = _make_r_name_list(c, p, permutation_order)
        _apply_style_to_r_names(
            r_names_list, verifier_to_sort_by, permutation_order, self._rule_to_color_dict, c, p, color_all=color_all, single_out_queried=not(n_wo_p)
        )
        return(r_names_list)
    def _make_answer_table_cols(
        self,
        table,
        p_order,
        final_answer,
        display_combo_number,
        verifier_to_sort_by,
        tree_version
    ):
        n_wo_p = self.n_mode and not(p_order)
        rule_col_title = '' if tree_version else f"{'Rule Card ' if (n_wo_p) else 'Verifier '}"
        rule_col_width = max(len(f"{rule_col_title} X"), self.max_possible_rule_length)
        if(not final_answer):
            table.add_column("", justify="right") # answer index column
        table.add_column("Ans")                   # answer       column
        if(display_combo_number):
            table.add_column("", justify="right") # combo index column
        for v_index in range(len(self.solver.rcs_list)):
            if(p_order):
                table.add_column("")              # RC          column (nightmare mode only)
            rule_column_name = f"{rule_col_title}{letters[v_index]}"
            rule_col_style = 'r' if((v_index == verifier_to_sort_by) and not(n_wo_p)) else ''
            col_text = Text(text=rule_column_name, style=rule_col_style, justify="center")
            table.add_column(col_text, min_width=rule_col_width) # Verifier/Rule Card columns
        if not tree_version:
            table.add_column("Rule Indexes")          # Rule Indexes column
            if(self.n_mode):
                table.add_column("Permutation")       # Permutation column (nightmare mode only)
    def _print_possible_rules_by_verifier_from_cwas(
        self,
        full_cwas,
        v_index,
        title,
        justify="center",
        indent=0,
        active=True,
        border_style="blue",
        **kwargs
    ):
        """
        Given a list of full_cwas and a verifier index, prints a table of all rules that are possible for that verifier (derived from the cwas).
        """
        if not(active):
            return
        rule_ids_by_verifier = solver.solver_utils.get_set_r_unique_ids_vs_from_full_cwas(full_cwas, self.n_mode)
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
            rcs_list_possible, title, justify=justify, indent=indent, border_style=border_style, **kwargs
        )
    def _print_useful_qs_dict_info_helper(
        self,
        useful_qs_dict,
        cwa_set_when_q_dict_made,
        v_index,
        proposals_to_examine=None,
        see_all_combos=True,
    ):
        """
        Displays all information in the useful_queries_dict about a specific verifier card/list of proposals.
        If proposals_to_examine is none, will print info about all useful proposals.
        Note: will need the full_cwas used to make this useful_queries_dict.
        """
        full_cwas = self.solver.full_cwa_list_from_cwa_set(cwa_set_when_q_dict_made)
        q_dict_this_card: dict[int: Query_Info] = dict()
        for (proposal, inner_dict) in sorted(useful_qs_dict.items()):
            if(v_index in inner_dict):
                q_info: Query_Info = inner_dict[v_index]
                q_dict_this_card[proposal] = q_info

        possible_rules_title = f"\nVerifier [b cyan]{letters[v_index]}[/b cyan] Rules Possible When This Qs Dict Was Made"
        # NOTE print table
        self._print_possible_rules_by_verifier_from_cwas(
            full_cwas,
            v_index,
            title=possible_rules_title,
            caption=f"# useful queries for Verifier {letters[v_index]}: {len(q_dict_this_card)}",
            caption_style=""
        )
            # console.print(f"# useful queries for Verifier {letters[v_index]}: {len(q_dict_this_card)}", highlight=False, justify="center")
        for (prop_index, (proposal, q_info)) in enumerate(sorted(q_dict_this_card.items()), start=1):
            if not ((proposals_to_examine is None) or (proposal in proposals_to_examine)):
                continue
            (full_cwa_false, full_cwa_true) = [
                self.solver.full_cwa_list_from_cwa_set(
                        self.solver.intersect_gscwa_qinfocwa(cwa_set_when_q_dict_made, q_info_cwa_set)
                    ) for q_info_cwa_set in (q_info.cwa_set_false, q_info.cwa_set_true)
            ]

            # only in long form version
            possible_rules_false_title = Text.assemble(
                f"\n{prop_index}",
                f": Verifier ",
                (f"{letters[v_index]}", "b cyan"),
                _highlight(f" Rules if {proposal} False")
            )

            possible_rules_true_title = Text.assemble(
                f"\n{prop_index}",
                f": Verifier ",
                (f"{letters[v_index]}", "b cyan"),
                _highlight(f" Rules if {proposal} True")
            )

            # NOTE table possible verifier rules for ❌ result
            self._print_possible_rules_by_verifier_from_cwas(
                full_cwa_false,
                v_index,
                title=possible_rules_false_title,
                border_style="indian_red1"
            )

            # NOTE table possible verifier rules for ✅ result
            self._print_possible_rules_by_verifier_from_cwas(
                full_cwa_true,
                v_index,
                title=possible_rules_true_title,
                border_style="chartreuse1"
            )


            if(see_all_combos):

                # NOTE table CWAs for ❌ result
                self.print_all_possible_answers(
                    cwas=full_cwa_false,
                    title=Text.assemble(
                        f"\n{prop_index}: ",
                        f"CWAs if ",
                        (f"{proposal} {letters[v_index]}", "b cyan"),
                        _highlight(f" False")
                    ),
                    permutation_order=True,
                    verifier_to_sort_by=v_index,
                    border_style="#A64949"
                )

                # NOTE table CWAs for ✅ result
                self.print_all_possible_answers(
                    cwas=full_cwa_true,
                    title=Text.assemble(
                        f"\n{prop_index}: ",
                        f"CWAs if ",
                        (f"{proposal} {letters[v_index]}", "b cyan"),
                        _highlight(f" True")
                    ),
                    permutation_order=True,
                    verifier_to_sort_by=v_index,
                    border_style="#58A500"
                )
    def _get_all_possible_answers_table(
            self,
            cwas,
            title                = "",
            permutation_order    = False,
            display_combo_number = True,
            verifier_to_sort_by  = None,
            tree_version         = False,
            num_empty_rows       = 0,     # used for tree tables
            **kwargs
        ):
        """
        permutation_order: if this is true and it's nightmare mode, prints the rule names in permutation order. If this is false and it's nightmare mode, print the rule names in standard order. Has no effect when not nightmare mode.

        verifier_to_sort_by: optionally sort results first by answer, and then by the unique id of the rule they assign to verifier_to_sort_by.

        All **kwargs passed to Table.
        """
        n_mode = (self.solver.problem.mode == NIGHTMARE)
        permutation_order = permutation_order and n_mode
        n_wo_p = n_mode and not(permutation_order)
        unzipped_cwa = list(zip(*cwas))
        (combos, permutations, answers) = (unzipped_cwa[0], unzipped_cwa[1], unzipped_cwa[-1])
        set_possible_answers = set(answers)
        final_answer = (len(set_possible_answers) == 1)

        if not("header_style" in kwargs):
            kwargs["header_style"] = "magenta"
        if not("title_style" in kwargs):
            kwargs["title_style"] = ""
        table = Table(title=title, **kwargs, row_styles=[''] if (tree_version) else ANSWER_TABLE_ROW_STYLES)
        self._make_answer_table_cols(
            table,
            permutation_order,
            final_answer,
            display_combo_number,
            verifier_to_sort_by,
            tree_version
        )
        # NOTE: Set LINES_BETWEEN_ANSWERS to True/False to enable/disable lines between new answers


        # TODO: consider making the row arguments its own function.
        sorted_cwas = sorted(cwas, key=_get_sort_key(n_mode, n_wo_p, verifier_to_sort_by))
        a_index = 0
        card_index_col_widths = _get_col_widths(
            [
                ([c[p_num].card_index for p_num in p] if (permutation_order) else [r.card_index for r in c])
                for (c, p) in zip(combos, permutations)
            ]
        )

        if(tree_version):
            if(permutation_order):
                card_index_col_widths = [num + 1 for num in card_index_col_widths]
            header_style=f"b bright_white on {TREE_BACKGROUND_COLOR}"
            default_tree_style = f"b bright_white on {TREE_BACKGROUND_COLOR}"
            table = Table(
                box=None,
                padding=(0, 1),
                collapse_padding=True,
                # style=default_tree_style,
                header_style=header_style,
                title_style=header_style
            )
            table.add_column("", style=f"on {TREE_BACKGROUND_COLOR}", justify="right") # combo index column
            table.add_column("", style=f"on {TREE_BACKGROUND_COLOR}") # Answer column
            for v_index in range(len(combos[0])):
                table.add_column(
                    # if column has even width, put the verifier name on right side of center.
                    (' ' if (card_index_col_widths[v_index] % 2 == 0) else '') + letters[v_index],
                    style=f"on {TREE_BACKGROUND_COLOR}",
                    justify="center",
                )
            table.caption_style=header_style

        for (c_index, cwa) in enumerate(sorted_cwas, start=1): # note that c_index starts at 1
            (c, a) = (cwa[0], cwa[-1])
            p = cwa[1] if (n_mode) else None
            new_ans = ((c_index == 1) or (a != sorted_cwas[c_index - 2][-1]))
            a_index += new_ans
            only_unique_answer_index = Text(str(a_index) if(new_ans) else '', style="white")
            if(new_ans and LINES_BETWEEN_ANSWERS):
                table.add_section()

            card_indexes_text = self._get_card_indexes_text(card_index_col_widths, c)
            r_names_texts_list = self._get_r_names_texts_list(
                c, p, permutation_order, verifier_to_sort_by, color_all=True
            )
            if(WRITE_ANSWERS_MULTIPLE_TIMES_COLOR):
                answer_color = self._answer_to_color_dict[a]
                answer_write = Text(str(a), style=f'b {answer_color}')
            else:
                answer_write = Text(str(a) if(new_ans) else '', "b bright_white")
            tree_index_num = (
                Text(str(c_index)) if(WRITE_ANSWERS_MULTIPLE_TIMES_COLOR) else
                only_unique_answer_index
            )
            if not(tree_version):
                t_row_args = (
                    (tuple() if (final_answer) else (only_unique_answer_index,)) +
                    (answer_write,) +
                    ((str(c_index),) if(display_combo_number) else tuple()) +
                    tuple(r_names_texts_list) +
                    (card_indexes_text,) + 
                    ( ( f'{" ".join([str(r_index) for r_index in p])}', )  if(n_mode) else tuple())
                )
            else:
                p = p if(permutation_order) else range(len(c))
                table_unique_id_list = [c[p_num].unique_id for p_num in p]
                table_color_list = [self._rule_to_color_dict[t_uid] for t_uid in table_unique_id_list]
                table_chars_list = [
                    f'{letters[rc_index] if(permutation_order) else ""}' +
                    f'{self.solver.flat_rule_list[t_uid].card_index}'
                    for (rc_index, t_uid) in zip(p, table_unique_id_list)
                ]
                # table_text_list = [Text("", f'on {tree_background_color}')] +\
                table_text_list = [
                    tree_index_num.append("." if(WRITE_ANSWERS_MULTIPLE_TIMES_COLOR or new_ans) else ''),
                    answer_write,
                ] +\
                [
                    Text(
                        text=f"{chars}",
                        style=f'b {"r " if ((col == verifier_to_sort_by) and not(n_wo_p)) else""}{color}',
                        justify="right"
                    )
                    for (col, (chars, color)) in
                    enumerate(zip(table_chars_list, table_color_list))
                ]

                # for (combo_index, c_index_str) in enumerate(card_indexes_strings_list):
                t_row_args = table_text_list
                # style=self.rule_to_color_dict[c[combo_index].unique_id]
                # card_indexes_text.append(Text(text=f'{c_index_str} ', style=style))
                # t_row_args = (card_indexes_text,)
            num_row_args = len(t_row_args)
            table.add_row(*t_row_args)
        for v_index in range(num_empty_rows):
            table.add_row(*['' * num_row_args])
        return(table)
    def _small_partition_to_text(self, small_partition, col_widths, full_cwas=None):
        """
        If using for cwa indexes that are 1-based and from a smaller cwas list, then `full_cwas` should be set to the list. If the cwa indexes are 0-based and from the solver full_cwas_list, then `full_cwas` should be None.
        """
        full_cwas = self.solver.full_cwas_list if(full_cwas is None) else full_cwas
        cwas_idx_subtract = 0 if(full_cwas is None) else 1
        texts = [' ' * (n + 1) for n in col_widths]
        for (p1_idx, p1_val) in enumerate(small_partition[::-1]):
            style = self._answer_to_color_dict[full_cwas[p1_val - cwas_idx_subtract][-1]]
            texts[-1 - p1_idx] = (f'{p1_val:>{col_widths[-1 - p1_idx]}} ', style)
        text = Text.assemble(*texts)
        return(text)
    def _large_partition_to_text(self, large_partition, col_widths, full_cwas=None):
        """
        If using for cwa indexes that are 1-based and from a smaller cwas list, then `full_cwas` should be set to the list. If the cwa indexes are 0-based and from the solver full_cwas_list, then `full_cwas` should be None.
        """
        full_cwas = self.solver.full_cwas_list if(full_cwas is None) else full_cwas
        cwas_idx_subtract = 0 if(full_cwas is None) else 1
        texts = [' ' * (n + 1) for n in col_widths]
        for(p2_idx, p2_val) in enumerate(large_partition):
            style = self._answer_to_color_dict[full_cwas[p2_val - cwas_idx_subtract][-1]]
            texts[p2_idx] = (f'{p2_val:>{col_widths[p2_idx]}} ', style)
        text = Text.assemble(*texts)
        return(text)
    def _combine_small_large_partition_texts(self, small_partition_text: Text, large_partition_text):
        sp_str = small_partition_text.plain
        if((len(sp_str) == 0) or sp_str.isspace()):
            return('')
        return(Text.assemble(small_partition_text, f'{PARTITION_DIVIDER} ' if(small_partition_text.plain) else '', large_partition_text))
    def _p_table_2_cwa_indexes_to_text(
        self,
        col_widths_info,
        full_cwas_dict_made,
        small_partition=None,
        large_partition=None,
    ):
        (col_widths_p1, col_widths_p2) = col_widths_info
        p1_text = self._small_partition_to_text(small_partition, col_widths_p1, full_cwas_dict_made)
        p2_text = self._large_partition_to_text(large_partition, col_widths_p2, full_cwas_dict_made)
        full_text = self._combine_small_large_partition_texts(p1_text, p2_text)
        return(full_text)
    def _raw_row_arg_to_row_arg(self, raw_row_arg, full_cwas_dict_made, col_widths_by_verifier_info):
        # FULL PARTITION TABLE
        row_arg = []
        (prop_index, proposal) = (raw_row_arg[0], raw_row_arg[1])
        row_arg.append(Text(f'{prop_index}', style=""))
        row_arg.append(Text(f'{proposal}', PROPOSAL_COLOR))
        for (v_index, verifier_partition) in enumerate(raw_row_arg[2:]):
            if(verifier_partition[0]): # if this verifier has any partitions
                (partition_1, partition_2) = verifier_partition
                row_arg.append(
                    self._p_table_2_cwa_indexes_to_text(
                        col_widths_info=col_widths_by_verifier_info[v_index],
                        full_cwas_dict_made=full_cwas_dict_made,
                        small_partition=partition_1,
                        large_partition=partition_2,
                    )
                )
            else: # if this verifier does not have partitions
                row_arg.append('')
        return(row_arg)
    def _get_small_partitions_texts_helper(self, small_partitions, col_widths, full_cwas):
        small_partitions_texts = [
            (
                self._small_partition_to_text(
                    sp,
                    col_widths,
                    full_cwas,
                ) 
                if len(sp) > 0
                else ''
            )
            for sp in small_partitions
        ]
        return(small_partitions_texts)
    def _get_large_partitions_texts_helper(self, large_partitions, col_widths, full_cwas):
        large_partitions_texts = [
            self._large_partition_to_text(
                lp,
                col_widths,
                full_cwas,
            )
            for lp in large_partitions
        ]
        return(large_partitions_texts)
    def _get_col_widths_small_partition(self, small_partitions):
        """
        Given a list of `small_partitions`, return a list representing the width of every column necessary to display them properly, from left to right.
        """
        max_elements_small_partition = max([len(sp) for sp in small_partitions])
        widths_by_col_small_partition = [0] * max_elements_small_partition
        for left_idx_col in range(max_elements_small_partition):
            widths_by_col_small_partition[left_idx_col] = max(
                [
                    Solver_Displayer._get_width_at_left_idx_col_small_p(
                        left_idx_col,
                        max_elements_small_partition,
                        sp
                    )
                    for sp in small_partitions
                ]
            )
        return(widths_by_col_small_partition)
    def _get_col_widths_large_partition(self, large_partitions):
        max_elements_large_partition = max([len(lp) for lp in large_partitions])
        widths_by_col_large_partition = [0] * max_elements_large_partition
        for left_idx_col in range(max_elements_large_partition):
            widths_by_col_large_partition[left_idx_col] = max(
                [
                    Solver_Displayer._get_width_at_left_idx_col_second_p(
                        left_idx_col,
                        lp
                    )
                    for lp in large_partitions
                ]
            )
        return(widths_by_col_large_partition)
    def _table_data_to_raw_row_args(self, table_data):
        """
        Returns
        -------
        raw_row_args : list[raw_row_arg]

            raw_row_arg: [index (1-based), proposal, [[small_partition_ints A], [large_partition_ints A]], [B], [C]...]

            Where each verifier list is: [[small_partition_ints], [large_partition_ints]].
        """
        raw_row_args = []
        curr_raw_row_arg = None
        previous_proposal = None
        proposal_index = 0
        for datum in table_data:
            (proposal, verifier_index, first_cwa_indexes, second_cwa_indexes) = datum
            if(proposal != previous_proposal):
                if(curr_raw_row_arg):
                    raw_row_args.append(curr_raw_row_arg)
                proposal_index += 1
                curr_raw_row_arg = [proposal_index, proposal]
                for verifier in range(self.solver.num_rcs):
                    v_lists = [[], []]
                    curr_raw_row_arg.append(v_lists)
                previous_proposal = proposal
            curr_raw_row_arg[2 + verifier_index][0] = first_cwa_indexes
            curr_raw_row_arg[2 + verifier_index][1] = second_cwa_indexes
        raw_row_args.append(curr_raw_row_arg)
        # console.print(raw_row_args)
        return(raw_row_args)
    def _get_partition_row_sort_key(self, verifiers_to_sort_by=None):
        if(verifiers_to_sort_by is None):
            return(lambda raw_row_arg: raw_row_arg[1]) # sort by proposal
        def sort_key(raw_row_arg):
            # first sort by length/alpa order of the small partition assigned to verifiers in order of verifiers_to_sort_by
            # then the length/alphabetical order of all the other small partititions, in verifier order.
            # then the proposal
            remaining_verifiers = [v for v in range(self.solver.num_rcs) if (v not in verifiers_to_sort_by)]
            vs_in_sort_order = verifiers_to_sort_by + remaining_verifiers
            proposal = raw_row_arg[1]
            criteria = []
            for v_index in vs_in_sort_order:
                small_partition_this_verifier = raw_row_arg[2 + v_index][0]
                criteria += Solver_Displayer.get_partition_sort_criteria(small_partition_this_verifier)
            criteria.append(proposal)
            return(criteria)
        return sort_key
    def _print_partition_table(self, table_data, cwas_when_dict_made, title, verifiers_to_sort_by):
        raw_row_args = self._table_data_to_raw_row_args(table_data)
        raw_row_args.sort(key=self._get_partition_row_sort_key(verifiers_to_sort_by))
        full_partition_texts_by_verifier = [None] * self.solver.num_rcs
        verifier_title_justify_lengths = [None] * self.solver.num_rcs
        for verifier_index in range(self.solver.num_rcs):
            partitions = [raw_row_arg[2 + verifier_index] for raw_row_arg in raw_row_args]
            (small_partitions, large_partitions) = list(zip(*partitions))
            # next 5 physical lines are solely to align the verifier name with the partition bar when displaying table (consider making this its own function)
            small_partitions_col_widths = self._get_col_widths_small_partition(small_partitions)
            num_elts_small_partition = len(small_partitions_col_widths)
            verifier_title_justify_lengths[verifier_index] = (
                sum(small_partitions_col_widths) + num_elts_small_partition + 1
            )

            full_partition_texts_by_verifier[verifier_index] = self.get_full_partitions_texts(
                small_partitions,
                large_partitions,
                cwas_when_dict_made
            )
        sorted_by_line_title = (
            '' if(verifiers_to_sort_by is None) else
            Text.assemble(
                " sorted by ",
                Text.assemble(
                    *([Text(letters[v], style=VERIFIER_COLORS[v]).append(' ') for v in verifiers_to_sort_by])
                )
            )
        )
        proposals = [x[1] for x in raw_row_args]
        table = Table(
            box=box.HORIZONTALS,
            title=Text.assemble(title, sorted_by_line_title),
            title_style="",
            collapse_padding=True,
            row_styles=PARTITION_TABLE_ROW_STYLES,
        )
        table.add_column("", justify="right")         # proposal index
        table.add_column("")                          # proposal
        for v_index in range(self.solver.num_rcs):  # consider not making columns for verifiers with no data
            table.add_column(
                Text(
                    f"{letters[v_index]:>{verifier_title_justify_lengths[v_index]}}",
                    justify="left",
                    style=VERIFIER_COLORS[v_index],
                )
            )
        previous_small_partition = None
        for z_idx in range(len(proposals)):
            cooked_row_arg = [
                Text(f'{z_idx + 1}', style=''),
                Text(f'{proposals[z_idx]}', style=PROPOSAL_COLOR),
            ]
            for v_index in range(self.solver.num_rcs):
                cooked_row_arg.append(full_partition_texts_by_verifier[v_index][z_idx])
            current_small_partition = (
                full_partition_texts_by_verifier[verifiers_to_sort_by[0]][z_idx]
                if(verifiers_to_sort_by is not None)
                else None
            )
            if(current_small_partition != previous_small_partition):
                table.add_section()
                previous_small_partition = current_small_partition
            table.add_row(*cooked_row_arg)
        console.print(table, justify="center")
    def _get_partition_table_data(
        self,
        qs_dict,
        cwa_set_when_dict_made,
        proposals_to_examine,
        verifier_indexes_to_examine,
    ):
        """
        Returns
        -------
        table_data : list[table_datum]

            table_datum: [proposal, verifier_index, [small_partition_ints], [large_partition_ints]]

                An example table_datum for proposal 512 on verifier E (index 4), which partitions
                the 5 CWAs into [2, 4] and [1, 3, 5] :

                    [512, 4, [2, 4], [1, 3, 5]]
        """
        table_data = []
        full_cwas = self.solver.full_cwa_list_from_cwa_set(cwa_set_when_dict_made)
        for (proposal, inner_dict) in qs_dict.items():
            if not((proposals_to_examine is None) or (proposal in proposals_to_examine)):
                continue
            for(verifier_index, q_info) in inner_dict.items():
                if not(
                    (verifier_indexes_to_examine is None) or
                    (verifier_index in verifier_indexes_to_examine)
                ):
                    continue
                (full_cwas_false, full_cwas_true) = [ # (cwas_false, cwas_true)
                    self.solver.full_cwa_list_from_cwa_set(
                        self.solver.intersect_gscwa_qinfocwa(cwa_set_when_dict_made, q_info_cwa_set)
                    )
                    for q_info_cwa_set in (q_info.cwa_set_false, q_info.cwa_set_true)
                ]
                (false_cwas_indexes, true_cwas_indexes) = ([], [])
                for (original_cwa_index, original_cwa) in enumerate(full_cwas, start=1):
                    list_to_append_to = (
                        false_cwas_indexes if(original_cwa in full_cwas_false) else true_cwas_indexes
                    )
                    list_to_append_to.append(original_cwa_index)
                # first compare lengths, then iff lengths are equal, compare the zeroeth CWA index
                min_max_key = lambda cwas_indexes: (
                    len(cwas_indexes), (cwas_indexes[0] if(len(cwas_indexes)) else -1)
                )
                false_true_cwas_indexes_tup = (false_cwas_indexes, true_cwas_indexes)
                first_cwas_indexes = min(false_true_cwas_indexes_tup, key=min_max_key)
                second_cwas_indexes = max(false_true_cwas_indexes_tup, key=min_max_key)
                assert (first_cwas_indexes != second_cwas_indexes)
                table_datum = [proposal, verifier_index, first_cwas_indexes, second_cwas_indexes]
                table_data.append(table_datum)
                # console.print(table_datum)
        return(table_data)
    def _short_q_info_printer_helper(
        self,
        qs_dict,
        cwa_set_when_dict_made,
        title,
        verifier_indexes_to_examine,
        proposals_to_examine,
        verifiers_to_sort_by = None,
    ):
        full_cwas = self.solver.full_cwa_list_from_cwa_set(cwa_set_when_dict_made)
        table_data = self._get_partition_table_data(
            qs_dict,
            cwa_set_when_dict_made,
            proposals_to_examine,
            verifier_indexes_to_examine,
        )
        self._print_partition_table(table_data, full_cwas, title, verifiers_to_sort_by)
        return
    def _get_bitset_Texts_int(self, bitset: int, base_16: bool, bits_per_verifier=None):
        """
        get the Texts for an int given the int, whether it should be displayed in base 16, and the number of bits per verifier (which is None if there are exactly as many bits per verifier as there are possible rules for that verifier).
        """
        num_possible_rules_by_verifier = [len(i) for i in self.solver.possible_rules_by_verifier]
        texts = []
        for v_index in range(self.solver.num_rcs):
            right_shift_amount = (
                sum(num_possible_rules_by_verifier[:v_index])
                if (bits_per_verifier is None)
                else (v_index * bits_per_verifier)
            )
            num_bits = (
                num_possible_rules_by_verifier[v_index]
                if (bits_per_verifier is None)
                else bits_per_verifier
            )
            bitset_for_verifier = (bitset >> right_shift_amount) & ((1 << num_bits) - 1)
            if(base_16):
                text_this_verifier = Text(
                    f"{hex(bitset_for_verifier).upper()[2:]:0>{math.ceil(num_bits/4)}}",
                    style=HEX_COLOR,
                )
            else:
                text_this_verifier_parts = []
                for bit_index in range(num_bits):
                    bit = (bitset_for_verifier >> bit_index) & 1
                    t = BIT_ONE_TEXT if bit else BIT_ZERO_TEXT
                    text_this_verifier_parts.append(t)
                text_this_verifier_parts.reverse()
                text_this_verifier = Text.assemble(*text_this_verifier_parts)
            texts.append(text_this_verifier)
        texts.reverse()
        return(texts)
    def _get_bitset_Texts_ndarr(self, bitset: np.ndarray, base_16):
        (num_verifiers, num_unint8_per_verifier) = bitset.shape
        return self._get_bitset_Texts_int(
            solver.solver_utils.bitset_to_int(bitset),
            base_16,
            bits_per_verifier = 8 * num_unint8_per_verifier
        )

    @staticmethod
    def get_partition_sort_criteria(partition):
        """
        Given a partition, return the sort key for that partition.
        """
        return([len(partition), partition])

    def get_small_partitions_texts(self, small_partitions, full_cwas=None):
        """
        Given a list of `small_partitions`, return a list of Texts to print that represent them.
        If using for cwa indexes that are 1-based and from a smaller cwas list, then `full_cwas` should be set to the list. If the cwa indexes are 0-based and from the solver full_cwas_list, then `full_cwas` should be None.
        """
        col_widths = self._get_col_widths_small_partition(small_partitions)
        return(self._get_small_partitions_texts_helper(small_partitions, col_widths, full_cwas))

    def get_large_partitions_texts(self, large_partitions, full_cwas=None):
        """
        Given a list of `large_partitions`, return a list of Texts to print that represent them.
        If using for cwa indexes that are 1-based and from a smaller cwas list, then `full_cwas` should be set to the list. If the cwa indexes are 0-based and from the solver full_cwas_list, then `full_cwas` should be None.
        """
        col_widths = self._get_col_widths_large_partition(large_partitions)
        return(self._get_large_partitions_texts_helper(large_partitions, col_widths, full_cwas))

    def get_full_partitions_texts(self, small_partitions, large_partitions, full_cwas=None):
        """
        Given a list of `small_partitions` and a list of `large_partitions` in corresponding order, return a list of Texts to print that represent the full partitions.
        If using for cwa indexes that are 1-based and from a smaller cwas list, then `full_cwas` should be set to the list. If the cwa indexes are 0-based and from the solver full_cwas_list, then `full_cwas` should be None.
        """
        sp_texts = self.get_small_partitions_texts(small_partitions, full_cwas)
        lp_texts = self.get_large_partitions_texts(large_partitions, full_cwas)
        combined_texts = [
            (self._combine_small_large_partition_texts(sp_text, lp_text) if(len(sp) > 0) else '')
            for (sp_text, lp_text, sp) in zip(sp_texts, lp_texts, small_partitions)
        ]
        return(combined_texts)

    def print_problem(self, rcs_list, problem, justify="center", active=True):
        """ if active is True, print a table representing the problem's rule cards, otherwise do nothing. """
        if(active):
            title = Text.assemble(
                f"\nProblem: ",
                (problem.identity, PROBLEM_TITLE_COLOR),
                (" Mode: "),
                (MODE_NAMES[problem.mode], STANDARD_EXTREME_NIGHTMARE_MODE_COLORS[problem.mode])
            )
            self.print_rcs_list(rcs_list, title, justify=justify, show_rc_nums=SHOW_RC_NUMS_IN_PROBLEM)

    def print_rcs_list(
        self,
        rcs_list: list[list[Rule]],
        title,
        border_style="blue",
        justify="center",
        indent=0,
        active=True,
        show_rc_nums=False,
        **kwargs
    ):
        """
        Prints a list of rules lists as a table.
        """
        if not(active):
            return
        table = Table(title=title, header_style="deep_sky_blue3", border_style=border_style, title_style='', **kwargs)
        table.add_column("Rule Index", justify="right")
        for c_index in range(len(rcs_list)):
            if(self.solver.problem.mode == EXTREME):
                rule_card_num_text = Text(f"({self.solver.problem.rc_nums_list[c_index * 2]}, {self.solver.problem.rc_nums_list[c_index * 2 + 1]})")
            else:
                rule_card_num_text = Text(f"({self.solver.problem.rc_nums_list[c_index]})")
            rule_card_num_text.style = "purple"
            if not(show_rc_nums):
                rule_card_num_text = Text("")
            rc_text = f'Rule Card {letters[c_index]}' + (' ' if show_rc_nums else '')
            min_width = max(self._max_rule_name_length, len(rc_text))
            table.add_column(Text(rc_text, justify="center").append(rule_card_num_text), min_width=min_width)
        zipped_rule_texts = zip_longest(*[[Text(r.name, style=self._rule_to_color_dict.get(r.unique_id, 'dim')) for r in rc] for rc in rcs_list], fillvalue='')
        for (i, zipped_rules) in enumerate(zipped_rule_texts):
            table.add_row(str(i), *zipped_rules)
        if(indent != 0):
            _print_indented_table(table, indent)
        else:
            console.print(table, justify=justify)

    def print_all_possible_answers(
            self,
            cwas,
            title                = "",
            permutation_order    = False,
            display_combo_number = True,
            verifier_to_sort_by  = None,
            active               = True,
            justify              = "center",
            custom_indent        = 0,
            **kwargs
    ):
        """
        Pretty prints a table of all the full combos_with_answers (cwas) given.
        title is the title of the table. Blank by default.
        permutation_order: if this is true and it's nightmare mode, prints the rule names in permutation order. If this is false and it's nightmare mode, print the rule names in standard order. Has no effect when not nightmare mode.

        verifier_to_sort_by: optionally sort results first by answer, and then by the unique id of the rule they assign to verifier_to_sort_by.

        active: if False, this function does nothing
        custom_indent: indent the table by this amount when printing.
        """
        if(not active):
            return
        table = self._get_all_possible_answers_table(
            cwas,
            title                = title,
            permutation_order    = permutation_order,
            display_combo_number = display_combo_number,
            verifier_to_sort_by  = verifier_to_sort_by,
            **kwargs
        )
        if(custom_indent == 0):
            console.print(table, justify=justify)
        else:
            _print_indented_table(table, custom_indent)

    def print_evaluations_cache_info(
            self,
            gs,
            name="game state",
            permutation_order=True,
            print_succeeding_game_states=True
        ):
        """
        Returns a tuple (gs_false, gs_true) for game states that could result from executing the best query. For use in interactive debugging sessions.
        NOTE: in interactive debugging session, use like this:
        (gs_false, gs_true) = sd.print_evaluations_cache_info(gs, name)
        """
        (
            best_mov,
            best_mov_cost_tup,
            best_gs_tup,
            best_expected_cost_tup
        ) = self.solver.get_move_mcost_gs_ncost_from_cache(gs)
        (gs_false, gs_true) = best_gs_tup
        full_cwa_remaining_if_false = self.solver.full_cwa_list_from_game_state(gs_false)
        num_cwa_false = len(full_cwa_remaining_if_false)

        full_cwa_remaining_if_true = self.solver.full_cwa_list_from_game_state(gs_true)
        num_cwa_true = len(full_cwa_remaining_if_true)

        num_cwa_now = len(self.solver.full_cwa_list_from_game_state(gs))
        p_true = num_cwa_true / num_cwa_now
        p_false = num_cwa_false / num_cwa_now

        # Remember that the cache does not contain already-won states.
        expected_cost_false = self.solver.get_move_mcost_gs_ncost_from_cache(
            gs_false,
            (None, None, None, (0,0))
        )[3]
        expected_cost_true = self.solver.get_move_mcost_gs_ncost_from_cache(
            gs_true,
            (None, None, None, (0,0))
        )[3]

        (ec_rounds, ec_queries) = best_expected_cost_tup
        self.print_game_state(gs, name=name, permutation_order=permutation_order, verifier_to_sort_by=best_mov[1])
        (r_cost, q_cost) = best_mov_cost_tup
        a = Text(f"Expected cost to win from current state: {ec_rounds:0.3f} rounds. {ec_queries:0.3f} queries.")
        b = Text(f"Best move: {mov_to_str(best_mov)}")
        b.stylize('b cyan', 12)
        c = Text(f"Cost of best move: {int(r_cost)} round{'' if (r_cost == 1) else 's'}. {q_cost} query.")
        d = Text(f"Probability query returns False: {p_false:0.3f}")
        e = Text(f"Probability query returns True : { p_true:0.3f}")
        f = Text(f"Expected cost to win after false query: {expected_cost_false[0]:0.3f} rounds." +
             f" {expected_cost_false[1]:0.3f} queries.")
        g = Text(f"Expected cost to win after true query : {expected_cost_true[0]:0.3f} rounds." +
             f" {expected_cost_true[1]:0.3f} queries.")
        l = _highlight(a,b,c,d,e,f,g)
        grid = _combine(*l)
        center_print(grid)
        title_false = Text.assemble((f"{mov_to_str(best_mov)}", "b cyan"), " returns ❌")
        title_true = Text.assemble((f"{mov_to_str(best_mov)}", "b cyan"), " returns ✅")
        if(print_succeeding_game_states):
            self.print_game_state(
                gs_false, title_false, verifier_to_sort_by=best_mov[1], permutation_order=permutation_order, border_style="indian_red1"
            )
            self.print_game_state(
                gs_true, title_true, verifier_to_sort_by=best_mov[1], permutation_order=permutation_order, border_style="chartreuse1"
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
            name="Game State",
            verifier_to_sort_by=None,
            permutation_order=True,
            active=True,
            **kwargs
        ):
        if(not active):
            return
        q_str = _highlight(f' Queries this round: {gs.num_queries_this_round}.')
        prop_str = _highlight(f' Proposal this round: {gs.proposal_used_this_round}.')
        self.print_all_possible_answers(
            cwas=self.solver.full_cwa_list_from_game_state(gs),
            title=Text.assemble(name, q_str, prop_str),
            permutation_order=permutation_order,
            verifier_to_sort_by=verifier_to_sort_by,
            **kwargs
        )

    def print_useful_qs_dict_info(
        self,
        useful_qs_dict,
        cwa_set_when_q_dict_made,
        title : str | Text ="Queries Dictionary",
        verifier_indexes: list[int] | int | None = None,
        proposals_to_examine : list[int] | int | None = None,
        see_all_combos=True,
        short=True,
        verifiers_to_sort_by : list[int] | int = None,
    ):
        """
        Displays all information about queries in the useful_queries_dict with a specific verifier card/proposal, such as the rules it's true for, the cwa sets that would result from it being true or false, etc. Can print out a less verbose printing with `short` set to True. See _print_partition_table to understand how the partition table is made.

        Parameters
        ----------
        useful_qs_dict
            The query dict to print information about.
        title : str | Text
            What to title the partition table when displaying in `short` form. Can be a string or a Text object.
        cwa_set_when_q_dict_made: set of cwa
            The set of all cwas that were possible when the `useful_qs_dict` was created.
        verifier_indexes: list[int] | int | None
            The verifiers, or single verifier, for which this will print queries. If None, will print queries about all verifiers.
        proposals_to_examine: list[proposals] | proposal | None
            A list of proposals to print queries for, or a single proposal to print queries for, or None to print queries for all proposals.Note that if a proposal is not a useful proposal for the given `verifier_index` (or any `verifier_index`, if it's None), will print no information about it.
        short: bool
            If this is True, instead of printing all the information mentioned above, will only print out the partition info.
        verifiers_to_sort_by: list[int] | int, optional
            Only affects the short (partitions) table. The order of verifiers to use when sorting the partition table. Can be a single integer, or a list of integers. If this is not set, will order the table by proposal. If this is set, will order by the list, and section the table by the first verifier in the list.

        Examples
        --------
        sd.print_useful_qs_dict_info(
            qs_dict,
            game_state.cwa_set,
            verifier_indexes=None,
            proposals_to_examine=None,
            short=True,
            verifiers_to_sort_by=[E, C]
        )
        """
        if(type(proposals_to_examine) == int):
            proposals_to_examine = [proposals_to_examine]
        if(type(verifier_indexes) == int):
            verifier_indexes = [verifier_indexes]
        if(type(verifiers_to_sort_by) == int):
            verifiers_to_sort_by = [verifiers_to_sort_by]
        if(short):
            self._short_q_info_printer_helper(
                useful_qs_dict,
                cwa_set_when_q_dict_made,
                title,
                verifier_indexes,
                proposals_to_examine,
                verifiers_to_sort_by=verifiers_to_sort_by,
            )
            return
        for possible_v_index in range(len(self.solver.rcs_list)):
            if((verifier_indexes is None) or (possible_v_index in verifier_indexes)):
                self._print_useful_qs_dict_info_helper(
                    useful_qs_dict,
                    cwa_set_when_q_dict_made,
                    possible_v_index,
                    proposals_to_examine,
                    see_all_combos,
                )

    def print_eval_cache_size(self):
        """
        Print out the memory usage of the evaluation cache of the solver, if the solver has chosen to record it.
        """
        if not(hasattr(self.solver, "size_of_evaluations_cache_in_bytes")):
            console.print("This solver did not record the size of its evaluations cache.")
            return
        size = self.solver.size_of_evaluations_cache_in_bytes
        table = Table.grid(padding=(0, 1))
        if(size > 0):
            if(size >= (2 ** 30)):
                table.add_row("       Gigabytes:", Text(f"{size /(2 ** 30):,.2f}", COLOR_OF_SPACE))
            if(size >= (2 ** 20)):
                table.add_row("       Megabytes:", Text(f"{size /(2 ** 20):,.2f}", COLOR_OF_SPACE))
            table.add_row(Text("     Bytes:", justify="right"), Text(f"{size:,}", COLOR_OF_SPACE))
            console.print(table)

    def end_play_display(self, current_gs, v_to_sort_by, query_history, current_score):
        """
        Used by controller.play_from_solver to play a game.
        """
        full_cwa = self.solver.full_cwa_list_from_game_state(current_gs)
        answers_table = self._get_all_possible_answers_table(
            full_cwa, "ANSWER", permutation_order=P_ORDER, verifier_to_sort_by=v_to_sort_by
        )
        answer = full_cwa[0][-1]
        q_history_table = _get_query_history_table(query_history, self.solver.num_rcs)
        ans_num_style = f'b {self._answer_to_color_dict[answer]}'
        ans_line = f"Answer: [{ans_num_style}]{answer}[/{ans_num_style}]"
        score_line = f"Final Score: Rounds: {current_score[0]}. Total Queries: {current_score[1]}."
        console.print(_combine(answers_table, q_history_table, ans_line, score_line), justify="center")
    def get_problem_id_text(self):
        return(Text(self.solver.problem.identity, style=PROBLEM_TITLE_COLOR))

############################### BITSET WERK #################################################################
    def get_bitset_Texts(self, bitset: int, base_16=False) -> list[Text]:
        """
        Given a bitset (currently in the form of a Python integer, but other formats to be added soon), return a list of Texts that can be used to pretty print it.

        Parameters
        ---------
        bitset : int
            Currently only accepts bitsets that are integers.

        hex : bool
            Whether to return the Texts for each verifier in base 16
        Returns
        -------
        list[Text], where list[0] corresponds to last verifier, and in general, the list[i] is in reverse order of the verifiers.
        """
        if(type(bitset) == int):
            return self._get_bitset_Texts_int(bitset, base_16)
        if(type(bitset) == np.ndarray):
            return self._get_bitset_Texts_ndarr(bitset, base_16)
        raise NotImplementedError(f"get_bitset_Texts not implemented for bitsets of type {type(bitset)}")


    def print_table_bitsets(self, bitsets, title=None, base_16=False, active=True, single_bitset=False):
        """
        Print a table of bitsets. NOTE: `bitsets` can be a list or a single bitset.

        Parameters
        ---------
        bitsets : list[bitset] | bitset
            The bitsets to print. Can be a list of bitsets, or a single bitset.

        title : str | None
            The title of the table. If left as None, will default to CWA Bitset (with an s at end or Hex).

        base_16 : bool
            Whether to print the bits as bits or in base 16.

        active : bool
            If active is False, this function will not do anything.

        single_bitset : bool
            A boolean which tells the function whether bitsets is a single bitset or not.
        """
        if not active:
            return
        if(title is None):
            title = "CWA Bitset" + ("s" if (len(bitsets) > 1) else '') + (" Hex" if base_16 else "")
        if(single_bitset):
            bitsets = [bitsets]
        t = Table(
            title=title,
            title_style="",
            header_style="magenta",
            row_styles=['', 'on #262626']
        )
        if(len(bitsets) > 1):
            t.add_column("", justify="right") # index of bitset. Starts at 1.
        t.add_column(Text("Int", justify="center"), justify="right") # full integer corresponding to bitset
        t.add_column(Text("Hex", justify="center"), justify="right") # hex of the integer column
        for v_index in range(self.solver.num_rcs - 1, -1, -1):
            t.add_column(Text(f"{letters[v_index]}", justify="center"), justify="right")
        for (bs_index, bs) in enumerate(bitsets):
            index_list = [f"{bs_index + 1}"] if(len(bitsets) > 1) else []
            bitset_int = solver.solver_utils.bitset_to_int(bs)
            int_list = [
                Text(f"{bitset_int:,}", style="cyan"),
                Text(f"{hex(bitset_int).upper()[2:]:}", style=HEX_COLOR),
            ]
            row_args = index_list + int_list + self.get_bitset_Texts(bs, base_16=base_16)
            t.add_row(*row_args)
        console.print(t, justify="center")
############################### BITSET WERK #################################################################
class Tree:
    show_combos_in_tree = False # a class variable so don't have to include it in every tree initializer
    max_combos_by_depth = []    # array[i] is the maximum number of combos of an internal node at depth i, considering the root to be at depth 0. Set when making each tree.
    def __init__(
            self,
            gs                        : Game_State,
            solver                    : solver.Solver,
            prob=1.0,
            cost_to_get_here=(0, 0),
            move_made_to_get_here=None,
            depth=0,
            tree_type='gs',
            move=None,                  # NOTE: not currently used. Intended to be used for 'move' type trees, which show multiple move options other than best move, if that gets implemented.
    ):
        # prob is the probability of getting to this gs from the query above it in the best move tree
        self.gs = gs
        self.solver = solver
        self.prob = prob
        self.cost_to_get_here = cost_to_get_here
        self.move_made_to_get_here = move_made_to_get_here
        self.depth = depth

        # TODO: fields to be added to be used for 'move' type trees:
        self.type = tree_type
        self.move = move
        # prob_tup # probabilities of the move being (false, true)
        # gs_tup   # resulting game states from the move being false, true
        # m_cost   # the cost the move in self.move

def _get_max_string_height_by_depth(tree: Tree):
    """
    Given a tree, returns a list l, where l[i] is the maximum number of combinations of an internal node at that height.
    """
    answer = []
    q = deque()
    q.append(tree)
    while(q):
        curr_node : Tree = q.popleft()
        full_cwas_current_node = tree.solver.full_cwa_list_from_cwa_set(curr_node.gs.cwa_set)
        if not(solver.one_answer_left(tree.solver.full_cwas_list, curr_node.gs.cwa_set)): # internal node
            num_combinations = len(full_cwas_current_node)
            if(curr_node.depth == len(answer)):
                answer.append(num_combinations)
            else:
                answer[curr_node.depth] = max(answer[curr_node.depth], num_combinations)
            children = _get_children(curr_node)
            for child in children:
                q.append(child)
    return(answer)

def _eliminate_trailing_zeros(s: str):
    """
    Take a string representing a decimal number and remove any trailing 0s, and also remove the decimal point if there are no nonzero-digits after it.
    """
    end_range = len(s)
    while(s[end_range - 1] == '0'):
        end_range -= 1
    if(s[end_range - 1] == '.'):
        end_range -= 1
    return(s[:end_range])

def _get_children(tree: Tree):
    if (solver.one_answer_left(tree.solver.full_cwas_list, tree.gs.cwa_set)):
        return([])
    result = tree.solver.get_move_mcost_gs_ncost_from_cache(tree.gs)
    assert (result is not None)
    (best_move, best_move_cost, gs_tup, total_expected_cost) = result
    full_cwas_node = tree.solver.full_cwa_list_from_game_state(tree.gs)
    current_num_combos = len(full_cwas_node)
    full_cwas_if_q_true = tree.solver.full_cwa_list_from_game_state(gs_tup[1])
    num_combos_if_q_true = len(full_cwas_if_q_true)
    p_true = num_combos_if_q_true / current_num_combos
    p_false = 1 - p_true
    prob_tup = (p_false, p_true)
    children = [
        Tree(
            gs=gs_tup[i],
            solver=tree.solver,
            prob=prob_tup[i],
            cost_to_get_here=add_tups(tree.cost_to_get_here, best_move_cost),
            move_made_to_get_here = best_move,
            depth=tree.depth+1
        ) for i in range(2)
    ]
    return(children)

def _node_to_str_table(tree: Tree):
    sd = Solver_Displayer(tree.solver)
    nl = '\n'
    if not(solver.one_answer_left(tree.solver.full_cwas_list, tree.gs.cwa_set)):
        result = tree.solver.get_move_mcost_gs_ncost_from_cache(tree.gs)
        (best_move, best_move_cost, gs_tup, total_expected_cost) = result
        verifier_to_sort_by = (
            None if (tree.move_made_to_get_here is None) else tree.move_made_to_get_here[1]
        )
        prob_str = f"{tree.prob:0.3f}" # Note: in format 0.123
        prob_str = _eliminate_trailing_zeros(f"{prob_str[2:4]}.{prob_str[4]}") + "%"
        cost_of_node_str = ' '.join(
            [
                f'{add_tups(tree.cost_to_get_here, total_expected_cost)[i]:.3f}'
                for i in range(2)
            ]
        )
        move_str = mov_to_str(best_move)
        # NOTE: comment out below if block to not mark new rounds in the best move tree
        if(best_move_cost[0] == 1): # if the best move costs a round
            move_str += ' (R)'
        if(not tree.show_combos_in_tree):
            tree_lines = (
                ((prob_str,) if (tree.prob != 1) else tuple()) +
                (cost_of_node_str, move_str)
            )
            max_line_length = max([len(l) for l in tree_lines])
            lines = [f"{l:^{max_line_length}}" for l in tree_lines] # the ^ centers the lines
            node_str = f"{nl.join(lines)}"
            rich_obj_to_print = Text(node_str, style=f"white on {TREE_BACKGROUND_COLOR}")
        else:
            num_combos = len(tree.solver.full_cwa_list_from_game_state(tree.gs))
            num_empty_rows = Tree.max_combos_by_depth[tree.depth] - num_combos
            node_table = sd._get_all_possible_answers_table(
                cwas=tree.solver.full_cwa_list_from_game_state(tree.gs),
                permutation_order=P_ORDER,
                display_combo_number=True,
                verifier_to_sort_by=verifier_to_sort_by,
                tree_version=True,
                num_empty_rows=num_empty_rows
            )

            title = ""
            if(tree.prob != 1): # don't show probability for root node
                title = f"{prob_str}\n"
            node_table.title = f'{title}{cost_of_node_str}'
            node_table.caption = move_str
            rich_obj_to_print = node_table
        node_list_lines = _rich_obj_to_list_lines(rich_obj_to_print)
        node_str = '\n'.join(node_list_lines).strip()
        return(node_str)
    else: # leaf node
        full_cwas_node = tree.solver.full_cwa_list_from_game_state(tree.gs)
        answer = full_cwas_node[0][-1]
        t = Table.grid()
        leaf_foreground_color = (
            f"b {sd._answer_to_color_dict[answer]}" if WRITE_ANSWERS_MULTIPLE_TIMES_COLOR 
            else "b bright_white"
        )
        leaf_style = f"{leaf_foreground_color} on {TREE_BACKGROUND_COLOR}"
        answer_text = Text(f" {str(answer)} ", style=leaf_style)
        t.add_row(answer_text)
        t_str = ''.join(_rich_obj_to_list_lines(answer_text))
        return(t_str)

def print_best_move_tree(gs, show_combos, solver):
    print()
    Tree.show_combos_in_tree = show_combos
    tree = Tree(gs=gs, solver=solver)
    Tree.max_combos_by_depth = _get_max_string_height_by_depth(tree)
    table_tree = PrettyPrintTree(_get_children, _node_to_str_table, color='')
    table_tree(tree)

