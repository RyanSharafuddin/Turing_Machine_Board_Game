from fractions import Fraction
import argparse
from src.core.definitions import *
from src.core import display
from src.core.display import Text, Table
from src.core import config
import src.problems.problems as problems

# Don't show stats for problems that don't take at least MIN_SEC seconds and MIN_BYTES bytes to solve,
# b/c they are too easy and distort stats.
MIN_SEC = 5
MIN_BYTES = int(.01 * (2 ** 30))
PERCENT_PREC = 1 # number decimal digits to show for percentages
DISPLAY_SIGN = False # Whether to display a sign in front of improvement percentages.
COLOR_1 = ""
COLOR_2 = ""
def get_improvement_percent_Text(val1, val2, prec=PERCENT_PREC):
    improvement_percent = round(Fraction((val2 - val1), val1) * 100, prec)
    if (improvement_percent == 0):
        color = "grey69"
    else:
        color = "green" if (improvement_percent < 0) else "red"
    if DISPLAY_SIGN:
        leading_sign = "+" if (improvement_percent > 0) else "-"
    else:
        leading_sign = ""
    return Text(f"{leading_sign}{abs(improvement_percent):{3 + prec}.{prec}f}", style=color)

def display_compare_versions(v_name_1: str, v_name_2: str):
    """
    Given 2 version names, displays a table showing version 2's improvements/disimprovements relative to version 1.
    """
    prob_info_dict_v1 = problems.get_problem_stats_for_version(v_name_1)
    prob_info_dict_v2 = problems.get_problem_stats_for_version(v_name_2)
    raw_row_data = [] # [(display_data, sort_key) . . .]
    for (p_id, v1_stats) in prob_info_dict_v1.items():
        v2_stats = prob_info_dict_v2.get(p_id)
        if (v2_stats is None):
            continue
        (v1_time, v1_cost, v1_bytes_used) = v1_stats[0:3]
        (v2_time, v2_cost, v2_bytes_used) = v2_stats[0:3]
        if ((max(v1_time, v2_time) < MIN_SEC) or (max(v1_bytes_used, v2_bytes_used) < MIN_BYTES)):
            continue
        if (v1_cost != v2_cost):
            console.print(
                Text("WARN", style=config.BIG_WARN),
                f": Costs for problem {p_id} are not equal b/t {v_name_1} and {v_name_2}. ",
                f"cost1: {v1_cost}. cost2: {v2_cost}.",
            )
        time_improvement = get_improvement_percent_Text(v1_time, v2_time)
        memory_improvement = get_improvement_percent_Text(v1_bytes_used, v2_bytes_used)
        (mode, num_vs, sort_key) = problems.get_mode_num_vs_and_sort_key_from_pid(p_id)
        if (mode is None):
            console.print(
                Text("WARN", style=config.BIG_WARN),
                f"Problem '{p_id}' does not exist in the current user_problems.txt. Skipping."
            )
            continue
        raw_row_data.append(
            (
                (
                    p_id,
                    Text(f"{num_vs}", style=["purple", "deep_pink4", "gold3"][num_vs - 4], justify="right"),
                    Text(problems.get_mode_Text(mode).plain, justify="right"),
                    f"{v1_time:,}",
                    time_improvement,
                    f"{v2_time:,}",
                    display.get_gigabytes_Text(v1_bytes_used).plain,
                    memory_improvement,
                    display.get_gigabytes_Text(v2_bytes_used).plain,
                ),
                sort_key
            )
        )
    raw_row_data.sort(key=lambda r:r[1])
    raw_row_data = [r[0] for r in raw_row_data]
    table = Table(
        # title=Text.assemble(Text(v_name_1, COLOR_1), " vs. ", Text(v_name_2, COLOR_2)),
        title=f"{v_name_1} vs. {v_name_2}",
        title_style="bright_white",
        header_style=config.PROBLEM_TABLE_HEADER_COLOR,
        border_style=config.PROBLEM_TABLE_BORDER,
        row_styles=["", "on #1c1c1c"],
    )
    table.add_column(Text("ID", justify="center"), justify="right", style=config.PROBLEM_ID_COLOR)
    table.add_column(Text("# Vs", justify="center"))
    table.add_column(Text("Mode", justify="center"))
    table.add_column(Text("Time 1", justify="center", style=COLOR_1), justify="right")
    table.add_column(Text("Time %", justify="center"), justify="right")
    table.add_column(Text("Time 2", justify="center", style=COLOR_2), justify="right")
    table.add_column(Text("Memory 1", justify="center", style=COLOR_1), justify="right")
    table.add_column(Text("Memory %", justify="center"), justify="right")
    table.add_column(Text("Memory 2", justify="center", style=COLOR_2), justify="right")
    for (index, raw_row_datum) in enumerate(raw_row_data):
        prev_mode = raw_row_data[index-1][2]
        curr_mode = raw_row_datum[2]
        if(prev_mode != curr_mode):
            table.add_section()
        table.add_row(*raw_row_datum)
    print()
    console.print(table)

# NOTE: may want to put in an argument to write all problems that haven't been solved, instead of
#       only those whose memory usage hasn't been recorded.
def write_file_problems_to_solve():
    prob_info_dict = problems.get_problem_stats_for_version(config.VERSION_NAME)
    with open(config.TEMP_PROBLEM_FILE, 'w') as f:
        for p in problems.get_all_matching_problems():
            if p.identity in config.KNOWN_KILLED_9_PROBLEMS:
                continue
            problem_stats = prob_info_dict.get(p.identity, (None, None, -1))
            (seconds_used, cost, bytes_used) = problem_stats[0:3]
            if (bytes_used == -1):
                f.write(f"{p.identity}\n")

def make_parser():
    parser = argparse.ArgumentParser(
        description="Ways To Use: 'python compare_solver_version_stats.py -c version1_name version2_name' to display a table comparing two versions, or 'python compare_solver_version_stats.py -r' to write the p_ids of all problems (except a set of problems specified in config.py that are known to crash the program) whose memory usage hasn't been recorded to a temporary file."
    )
    parser.add_argument(
        "arg0",
        type=str,
        nargs="?",
        default="",
    )
    parser.add_argument(
        "arg1",
        type=str,
        nargs="?",
        default="",
    )
    parser.add_argument(
        "--compare",
        "-c",
        action="store_true",
        help="Compare the two version names you provided as arg0 and arg1."
    )

    parser.add_argument(
        "--record",
        "-r",
        action="store_true",
        help="Write the problem ids of problems whose memory usage has not been recorded to a temporary text file."
    )
    return parser

if(__name__ == "__main__"):
    parser = make_parser()
    args = parser.parse_args()

    if args.record:
        write_file_problems_to_solve()
        exit()

    if args.compare:
        # python compare_solver_version_stats.py -c v1_name v2_name
        display_compare_versions(args.arg0, args.arg1)