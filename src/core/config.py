# see https://www.eggradients.com/shades-of-color or https://rgbcolorpicker.com/random/true
# also see https://rich.readthedocs.io/en/latest/appendix/colors.html#appendix-colors for more colors
COLORS = [
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
    "#6A26A2",
    "#00FF7F",
    "#FF7780",
    "#F22410",
    "#EE8727",
    "#AF4109",
    "#F2E32D",
    "#BC0B6F",
    "#2BAE7B",
    "#80AA33",
    "#01796F",
    "#CE5908",
    "#A94064",
    "#FF007F",
    "#FF77FF",
    "#FF66CC",
    "#EDC9AF",
    "#F0DC82",
    "#0095FD",
    "#38B5A9",
    "#BE7437",
    "#72D080",
    "#659653",
    "#00FFFF",
    "#D7AF00"
]

# Displaying
# TREE_BACKGROUND_COLOR      = "#690969"
TREE_BACKGROUND_COLOR      = "#420342" # Both seem reasonable
SHOW_RC_NUMS_IN_PROBLEM    = True # whether displaying a problem should also show the rule card numbers.
PROBLEM_TITLE_COLOR        = "#FFAF00" # problem titles when displaying problem; not in the problem table.
PROPOSAL_COLOR = "#00FFAA" # currently only used in partition tables
# verifier colors currently only used for partition table column titles. Also they look pretti in VSCode c:
VERIFIER_COLORS = ["#FF00EA", "#D84B60", "#00FFD5", "#88FF00", "#FFE600", "#FF7B00"]
HEX_COLOR = "#FFD7AF"

# Colors for the problems table
PROBLEM_TABLE_HEADER_COLOR = "#D700D7"
RULE_CARD_NUMS_COLOR       = "#FFAFFF"
PROBLEM_ID_COLOR           = "#00D7FF"
PROBLEM_TABLE_BORDER       = "#FF8700"
STACK_EXTREME_RULE_CARDS   = True # print out a problems table with this true or false to see what this does.
STANDARD_EXTREME_NIGHTMARE_MODE_COLORS = ['#00FF00', "#FFFF00", "#FF0000"]

# Used for printing out info related to where pickles are stored and how much time and space solvers used.
FILENAME_COLOR = "#00FF00"
COLOR_OF_TIME  = "#FF00B7"
COLOR_OF_SPACE = "#00FFFF"

# whether to print each unique answer in a unique color, or only print it once in the tables
WRITE_ANSWERS_MULTIPLE_TIMES_COLOR = True
SHOW_COMBOS_IN_TREE                = False       # Print combos in trees in display_problem_solution()
P_ORDER                            = True       # Whether to display tables in permutation order for 
                                                # nightmare mode (no effect in other modes)
# whether to print a line b/t every unique answer in the tables
LINES_BETWEEN_ANSWERS = False
DISPLAY               = True       # Whether controller displays the problems it asks solver to solve
PRINT_COMBOS          = True       # whether or not to print remaining combos after every query in play()



# Solver workings
DISABLE_GC = False              # Whether to disable the garbage collector while solve()ing.
# Increases speed on many problems, but *may* use more memory (does it actually, though? Test this with fil-profiler), and some problems already get killed due to out of memory even without this.
CACHE_END_STATES = False        # whether to cache the end states into the evaluations_cache


# Settings To Use For Debugging/Displaying Debugging Information
PRINT_POST_SOLVE_DEBUG_INFO = False # WARN: this will cause your program to use up a lot of memory and time if you set it to true. See solver.py/post_solve_printing() for details.
PARTITION_DIVIDER = '│' # options: '│' and '|'
PARTITION_TABLE_ROW_STYLES = ["", "on #1f1f1f"] # options: [""] for all same or ["", "on #1c1c1c"] to zebra
ANSWER_TABLE_ROW_STYLES = PARTITION_TABLE_ROW_STYLES
PRINT_SD_COLOR_DICT = False

DISPLAY_CWA_BITSETS = True  # whether to display all the cwa bitsets at the beginning when displaying problem
CWA_BITSETS_BASE_16 = False # the base in which to display the cwa bitsets, if they are to be displayed.

# Where things are, from perspective of controller.py.
PICKLE_DIRECTORY = "src/problems/Pickles/Bit_Sets" # "Pickles" # Directory where all pickled solvers go.
# PICKLE_DIRECTORY = "src/problems/Pickles/Partition_Set_Filter"
USER_PROBS_FILE_NAME = "src/problems/user_problems.txt"
TIME_PICKLE_FILE_NAME = "src/problems/Pickles/time_pickle_file.bin"
