# Example Usage: sh compare_versions.sh master vpt
# Given 2 git branches/commits with different version names, solve all problems in both and compare time/mem.

function solve_problems {
    python compare_solver_version_stats.py -r # make a temporary file of problems that need to be solved.
    temp_file_name=$(grep "^TEMP_PROBLEM_FILE[ ]*=" src/core/config.py | cut -d "\"" -f 2)
    while read -r p_id; do
        python controller.py -fo $p_id
    done < $temp_file_name
}

git checkout $1
v1=$(grep "^VERSION_NAME[ ]*=" src/core/config.py | cut -d "\"" -f 2)
solve_problems

git checkout $2
v2=$(grep "^VERSION_NAME[ ]*=" src/core/config.py | cut -d "\"" -f 2)
solve_problems
python compare_solver_version_stats.py -c $v1 $v2
