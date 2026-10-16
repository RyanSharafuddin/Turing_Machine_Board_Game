# Example Usages:
# sh compare_versions.sh master vpt
# sh compare_versions.sh master vpt -n
# sh compare_versions.sh master vpt -s

# Given 2 git commit-ishes that have different version names, solve all problems in both and compare time/mem.
# Can optionally specify -n or -s at the end to avoid wasting time on solving problems of other modes.
# i.e. -n means only solve nightmare problems, -s means only standard or extreme.
# Note that this MUST be the third argument.

function solve_problems {
    python compare_solver_version_stats.py -r # make a temporary file of problems that need to be solved.
    temp_file_name=$(grep "^TEMP_PROBLEM_FILE[ ]*=" src/core/config.py | cut -d "\"" -f 2)
    while read -r p_id; do
        python controller.py -fo $p_id
    done < $temp_file_name
}

git checkout $1 -q
v1=$(grep "^VERSION_NAME[ ]*=" src/core/config.py | cut -d "\"" -f 2)
solve_problems

git checkout $2 -q
v2=$(grep "^VERSION_NAME[ ]*=" src/core/config.py | cut -d "\"" -f 2)
solve_problems
python compare_solver_version_stats.py -c $v1 $v2 $3
