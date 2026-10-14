function solve_problems {
    while read -r line
    do
        p_id=`echo "$line" | cut -d"'" -f 2`
        echo $p_id
        # python controller.py -fo $p_id
    done < src/problems/curated_compare_problems.txt
}
git checkout $1
v1=$(grep "^VERSION_NAME[ ]*=" src/core/config.py | cut -d "\"" -f 2)
solve_problems

git checkout $2
v2=$(grep "^VERSION_NAME[ ]*=" src/core/config.py | cut -d "\"" -f 2)
solve_problems
python compare_solver_version_stats.py -c $v1 $v2
