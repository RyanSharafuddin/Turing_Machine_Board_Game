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
SHOW_RC_NUMS_IN_PROBLEM    = True          # Display rule card numbers when displaying a problem?
PROBLEM_TITLE_COLOR        = "#FFAF00" # problem titles when displaying problem; not in the problem table.
PROPOSAL_COLOR             = "#00FFAA" # currently only used in partition tables
HEX_COLOR                  = "#FFD7AF" # color of hex numbers when displaying bitsets.
# verifier colors used for partition table column titles/canonical form bitsets. + look pretti in VSCode c:
VERIFIER_COLORS = ["#FF00EA", "#D84B60", "#14A990", "#3E53DE", "#FFE600", "#FF7B00"]

# Settings for displaying the available problems table
PROBLEM_TABLE_HEADER_COLOR = "#D700D7"
RULE_CARD_NUMS_COLOR       = "#FFAFFF"
PROBLEM_ID_COLOR           = "#00D7FF"
PROBLEM_TABLE_BORDER       = "#FF8700"
STACK_EXTREME_RULE_CARDS   = True # stack the rule card numbers on top of each other in extreme mode?
STANDARD_EXTREME_NIGHTMARE_MODE_COLORS = ['#00FF00', "#FFFF00", "#FF0000"]

# Used for printing out info related to where pickles are stored and how much time and space solvers used.
FILENAME_COLOR = "#00FF00"
COLOR_OF_TIME  = "#FF00B7"
COLOR_OF_SPACE = "#00FFFF"

# whether to print each unique answer in a unique color, or only print it once in the tables
WRITE_ANSWERS_MULTIPLE_TIMES_COLOR = True
SHOW_COMBOS_IN_TREE   = False # Print combos in trees in display_problem_solution()
P_ORDER               = True  # Display tables in permutation order in nightmare mode (no effect other modes)
LINES_BETWEEN_ANSWERS = False # print a line b/t every unique answer in answer tables
DISPLAY               = True  # display the problem when asked to solve
PRINT_COMBOS          = True  # print remaining combos after every query in play()

# Solver workings
DISABLE_GC                   = True  # disable the garbage collector while solve()ing.
CACHE_END_STATES             = False # whether to cache the end states into the evaluations_cache
S_MODE_PROGRESS_BARS_DICT    = {     # dictionary of num_verifiers : num_progress_bars in standard mode

}
S_MODE_DEFAULT_PROGRESS_BARS = 1     # default number of progress bars in standard mode
N_MODE_PROGRESS_BARS_DICT    = {     # dictionary of num_verifiers : num_progress_bars in nightmare mode
    4: 4,
    5: 7,
    6: 7,
}
N_MODE_DEFAULT_PROGRESS_BARS = 4     # default number of progress bars in nightmare mode
STANDARD_BITSET_TYPE         = (     # cache game state set type in standard mode. Choose 1.
    set
    # int
    # np.ndarray
)
NIGHTMARE_BITSET_TYPE        = (     # cache game state set type in standard mode. Choose 1.
    int
    # np.ndarray
)

# Change How Debugging Information Is Displayed
PARTITION_DIVIDER          = '│' # options: '│' and '|'. For printing partition dictionary.
PARTITION_TABLE_ROW_STYLES = ["", "on #1f1f1f"] # options: [""] for all same or ["", "on #1f1f1f"] to zebra
ANSWER_TABLE_ROW_STYLES    = PARTITION_TABLE_ROW_STYLES
CWA_BITSETS_BASE_16        = True # whether to display cwa bit sets in base 16 (if they are to be displayed)

# Change Whether Debugging Informations Is Displayed
PRINT_POST_SOLVE_DEBUG_INFO = False  # WARN: takes a lot of memory/time. See post_solve_printing() for details.
PRINT_SD_COLOR_DICT         = False # Print the Solver_Displayer's answer to color dictionary?
DISPLAY_CWA_BITSETS         = True  # Display all the cwa bitsets at the beginning when displaying problem?

# Directory paths, from perspective of controller.py.
PICKLE_DIRECTORY      = "src/problems/Pickles/cache_working_cwa" # Where all pickled solvers go.
USER_PROBS_FILE_NAME  = "src/problems/user_problems.txt"
TIME_PICKLE_FILE_NAME = "src/problems/Pickles/time_pickle_file.bin"
