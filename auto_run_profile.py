import os
from rich.console import Console

console = Console()

def replace_line_in_file(file_name, new_content):
    """
    NOTE: WARN: all line_nums should be given 1-indexed, to match up with line numbers reported by VS Code.
    NOTE:       Don't include the newline in the end of line_num.
    new_content is a list of tuples [
        (line_num, new_content)
    ]
    """
    with open(file_name, "r") as f:
        file_lines_list = f.readlines()

    for (line_num, new_line_contents) in new_content:
        file_lines_list[line_num - 1] = new_line_contents + '\n'

    with open(file_name, 'w') as new_f:
        for line in file_lines_list:
            print(line, end="", file=new_f)

# WARN: line numbers below need changing if you edit the file above that point
solver_len_content = [
    (257, "        # if(one_answer_left(game_state.fset_cwa_indexes_remaining)):"),
    (258, "        if(len(fset_answers_from_cwa_iterable(game_state.fset_cwa_indexes_remaining)) == 1):")
]

solver_one_answer_content = [
    (257, "        if(one_answer_left(game_state.fset_cwa_indexes_remaining)):"),
    (258, "        # if(len(fset_answers_from_cwa_iterable(game_state.fset_cwa_indexes_remaining)) == 1):")
]


def solver_len():
    replace_line_in_file("solver.py", solver_len_content)
def solver_one_answer():
    replace_line_in_file("solver.py", solver_one_answer_content)

def write_problem_controller(prob_var_name, display = False):
    replace_line_in_file("controller.py", [
        (300, f'DISPLAY = {"True" if(display) else "False"} # WARN line 300 to be clobbered by auto_run_profile'),
        (301, f'latest = {prob_var_name} # WARN ditto line 301'),
        (302, "s = get_or_make_solver(latest, force_overwrite=False, no_pickles=True) # WARN: ditto line 302")
    ])


def run_regular():
    os.system("python controller.py")

def run_line_profile():
    os.system("LINE_PROFILE=1 python controller.py")

def print_line_profiler_output_line():
    with open("profile_output.txt", 'r') as f:
        lines = f.readlines()
        for line in lines:
            if(("257" == line.strip()[:3]) or ("258" == line.strip()[:3])):
                console.print(line, end="")

def profile_problem(line_profile: bool, one_answer: bool, prob_var_name: str, display=False):
    if(one_answer):
        solver_one_answer()
    else:
        solver_len()
    write_problem_controller(prob_var_name, display)
    # command = f"{'LINE_PROFILE=1 ' if(line_profile) else ''}python controller.py"
    line_in_use = "one_answer" if (one_answer) else "len"
    if(line_profile):
        run_line_profile()
        profiler_output_file = f"profiler_output/line_profiler/{prob_var_name}_{line_in_use}.lprof"
        os.system(f"mv profile_output.lprof {profiler_output_file}")
        # os.system(f"python -m line_profiler -rtmz {profiler_output_file}")
        print_line_profiler_output_line()
    else:
        run_regular()
    style = 'b r green on white' if (one_answer) else 'b r purple on white'
    console.rule()
    console.print(f"[b r blue on white]{prob_var_name}[/b r blue on white] run on [{style}]{line_in_use}[/{style}].")
    console.rule()

def profile_problem_4_way(prob_var_name):
    for line_profile in [0, 1]:
        for one_answer in [0, 1]:
            profile_problem(
                line_profile,
                one_answer,
                prob_var_name,
                display = (line_profile == one_answer == 0)
            )
    os.system("rm profile_output_*txt")

profile_problem_4_way("f5x") # ~ 3 m
profile_problem_4_way("f43") # ~ 1 hr
profile_problem_4_way("p1_n")
profile_problem_4_way("p2_n")
