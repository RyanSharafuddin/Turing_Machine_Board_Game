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
    "#38B5A9",
    "#BE7437",
    "#72D080",
    "#FFBF00",
    "#00FFFF",
    "#D7AF00"
]

# Display
TREE_BACKGROUND_COLOR = "#690969"
TREE_BACKGROUND_COLOR = "#420342" # Both seem reasonable
# whether to print each unique answer in a unique color, or only print it once in the tables
WRITE_ANSWERS_MULTIPLE_TIMES_COLOR = True
SHOW_COMBOS_IN_TREE = True       # Print combos in trees in display_problem_solution()
P_ORDER =             True       # Whether to display tables in permutation order for nightmare mode
                                 # (no effect in other modes)
# whether to print a line b/t every unique answer in the tables
LINES_BETWEEN_ANSWERS = False
DISPLAY =             True       # Whether controller displays the problems it asks solver to solve
PRINT_COMBOS        = True       # whether or not to print remaining combos after every query in play()



# Solver workings
PICKLE_DIRECTORY = "Pickles/IsomorphicQueryFilter" # "Pickles"       # Directory where all pickled solvers go.
# PICKLE_DIRECTORY = "Pickles/DreamCatcher" # "Pickles"       # Directory where all pickled solvers go.
# PICKLE_DIRECTORY = "Pickles/Nightmare" # "Pickles"       # Directory where all pickled solvers go.
DISABLE_GC = False               # Whether to disable the garbage collector while solve()ing.
                                 # Increases speed on many problems, but on other problems, such as I4BYJK (nightmare), causes the process to be terminated with a Killed: 9. signal. because it used too much memory.
CACHE_END_STATES = True          # whether to cache the end states into the evaluations_cache
# USE_NIGHTMARE_CALCULATE = True
