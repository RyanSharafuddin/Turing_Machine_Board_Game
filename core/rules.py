import string
from .definitions import Rule, all_125_possibilities_set, int_to_tri_sq_ci_tuple, Problem, STANDARD, NIGHTMARE, EXTREME

# rule 1
def triangle_eq_1(triangle, square, circle):
    return(triangle == 1)
def triangle_gt_1(triangle, square, circle):
    return(triangle > 1)
# rule 2
def triangle_lt_3(triangle, square, circle):
    return(triangle < 3)
def triangle_eq_3(triangle, square, circle):
    return(triangle == 3)
def triangle_gt_3(triangle, square, circle):
    return(triangle > 3)
#rule 3
def square_lt_3(triangle, square, circle):
    return(square < 3)
def square_eq_3(triangle, square, circle):
    return(square == 3)
def square_gt_3(triangle, square, circle):
    return(square > 3)
#rule 4
def square_lt_4(triangle, square, circle):
    return(square < 4)
def square_eq_4(triangle, square, circle):
    return(square == 4)
def square_gt_4(triangle, square, circle):
    return(square > 4)
#rule 5
def triangle_even(triangle, square, circle):
    return((triangle % 2) == 0)
def triangle_odd(triangle, square, circle):
    return((triangle % 2) == 1)
#rule 6
def square_even(triangle, square, circle):
    return((square % 2) == 0)
def square_odd(triangle, square, circle):
    return((square % 2) == 1)
#rule 7
def circle_even(triangle, square, circle):
    return((circle % 2) == 0)
def circle_odd(triangle, square, circle):
    return((circle % 2) == 1)
# rule 8
def zero_1(triangle, square, circle):
    return((triangle, square, circle).count(1) == 0)
def one_1(triangle, square, circle):
    return((triangle, square, circle).count(1) == 1)
def two_1(triangle, square, circle):
    return((triangle, square, circle).count(1) == 2)
def three_1(triangle, square, circle):
    return((triangle, square, circle).count(1) == 3)

#rule 9
def zero_3(triangle, square, circle):
    return((triangle, square, circle).count(3) == 0)
def one_3(triangle, square, circle):
    return((triangle, square, circle).count(3) == 1)
def two_3(triangle, square, circle):
    return((triangle, square, circle).count(3) == 2)
def three_3(triangle, square, circle):
    return((triangle, square, circle).count(3) == 3)
#rule 10
def zero_4(triangle, square, circle):
    return((triangle, square, circle).count(4) == 0)
def one_4(triangle, square, circle):
    return((triangle, square, circle).count(4) == 1)
def two_4(triangle, square, circle):
    return((triangle, square, circle).count(4) == 2)
def three_4(triangle, square, circle):
    return((triangle, square, circle).count(4) == 3)

# rule 11
def triangle_lt_square(triangle, square, circle):
    return(triangle < square)
def triangle_eq_square(triangle, square, circle):
    return(triangle == square)
def triangle_gt_square(triangle, square, circle):
    return(triangle > square)

# rule 12
def triangle_lt_circle(triangle, square, circle):
    return(triangle < circle)
def triangle_eq_circle(triangle, square, circle):
    return(triangle == circle)
def triangle_gt_circle(triangle, square, circle):
    return(triangle > circle)

#rule 14
def triangle_strict_min(triangle, square, circle):
    return((triangle < square) and (triangle < circle))
def square_strict_min(triangle, square, circle):
    return((square < triangle) and (square < circle))
def circle_strict_min(triangle, square, circle):
    return((circle < triangle) and (circle < square))

# rule 15
def triangle_strict_max(triangle, square, circle):
    return((triangle > square) and (triangle > circle))
def square_strict_max(triangle, square, circle):
    return((square > triangle) and (square > circle))
def circle_strict_max(triangle, square, circle):
    return((circle > triangle) and (circle > square))

# rule 16
def more_evens(triangle, square, circle):
    return(len([i for i in (triangle, square, circle) if ((i % 2) == 0)]) > 1)
def more_odds(triangle, square, circle):
    return(len([i for i in (triangle, square, circle) if ((i % 2) == 0)]) <= 1)

# rule 17
def zero_evens(triangle, square, circle):
    return(len([i for i in (triangle, square, circle) if ((i % 2) == 0)]) == 0)
def one_even(triangle, square, circle):
    return(len([i for i in (triangle, square, circle) if ((i % 2) == 0)]) == 1)
def two_evens(triangle, square, circle):
    return(len([i for i in (triangle, square, circle) if ((i % 2) == 0)]) == 2)

#rule 18
def sum_digits_even(triangle, square, circle):
    return(((triangle + square + circle) % 2) == 0)
def sum_digits_odd(triangle, square, circle):
    return(((triangle + square + circle) % 2) == 1)

#rule 19
def tri_plus_sq_lt_6(triangle, square, circle):
    return((triangle + square) < 6)
def tri_plus_sq_eq_6(triangle, square, circle):
    return((triangle + square) == 6)
def tri_plus_sq_gt_6(triangle, square, circle):
    return((triangle + square) > 6)

# rule 20:
def triple_rep(triangle, square, circle):
    return(triangle == square == circle)
def double_rep(triangle, square, circle):
    if(triple_rep(triangle, square, circle)):
        return(False)
    return((triangle == square) or (triangle == circle) or (square == circle))
def no_rep(triangle, square, circle):
    return(not(double_rep(triangle, square, circle) or triple_rep(triangle, square, circle)))

# rule 21:
def no_pairs(triangle, square, circle):
    return(not(double_rep(triangle, square, circle)))

#rule 22
def strictly_ascending(triangle, square, circle):
    return(triangle < square < circle)
def strictly_descending(triangle, square, circle):
    return(triangle > square > circle)
def neither_asc_desc(triangle, square, circle):
    return(not(strictly_ascending(triangle, square, circle) or strictly_descending(triangle, square, circle)))

# rule 23
def sum_digits_lt_6(triangle, square, circle):
    return((triangle + square + circle) < 6)
def sum_digits_eq_6(triangle, square, circle):
    return((triangle + square + circle) == 6)
def sum_digits_gt_6(triangle, square, circle):
    return((triangle + square + circle) > 6)

#rule 24
def cons_seq_cons_asc_3(triangle, square, circle):
    return(((square == (triangle + 1)) and (circle == (square + 1))))
def cons_seq_cons_asc_2(triangle, square, circle):
    return(((square == (triangle + 1)) != (circle == (square + 1))))
def cons_seq_cons_asc_0(triangle, square, circle):
    return(not((square == (triangle + 1)) or (circle == (square + 1))))

#rule 25
def cons_seq_cons_0(triangle, square, circle):
    return(not (cons_seq_cons_2(triangle, square, circle) or cons_seq_cons_3(triangle, square, circle)))
def cons_seq_cons_2(triangle, square, circle):
    return(cons_seq_cons_asc_2(triangle, square, circle) or ((square == (triangle - 1)) != (circle == (square - 1))))
def cons_seq_cons_3(triangle, square, circle):
    return(cons_seq_cons_asc_3(triangle, square, circle) or ((square == (triangle - 1)) and (circle == (square - 1))))

# rule 27
# rule 28
def square_eq_1(triangle, square, circle):
    return(square == 1)
def circle_eq_1(triangle, square, circle):
    return(circle == 1)

# rule 30 (all rules found in other cards)

#rule 31
# rule 0 on card 31 is the same as rule 1 on card 1
def square_gt_1(triangle, square, circle):
    return(square > 1)
def circle_gt_1(triangle, square, circle):
    return(circle > 1)

# rule 33 (all rules found in other cards)
# rule 34
def triangle_a_min(triangle, square, circle):
    return((triangle <= square) and (triangle <= circle))
def square_a_min(triangle, square, circle):
    return((square <= triangle) and (square <= circle))
def circle_a_min(triangle, square, circle):
    return((circle <= triangle) and (circle <= square))

# rule 36
def sum_dig_3x(triangle, square, circle):
    return(((triangle + square + circle) % 3) == 0)
def sum_dig_4x(triangle, square, circle):
    return(((triangle + square + circle) % 4) == 0)
def sum_dig_5x(triangle, square, circle):
    return(((triangle + square + circle) % 5) == 0)

#rule 37
def tri_plus_sq_4(triangle, square, circle):
    return((triangle + square) == 4)
def tri_plus_ci_4(triangle, square, circle):
    return((triangle + circle) == 4)
def sq_plus_ci_4(triangle, square, circle):
    return((square + circle) == 4)

#rule 40
#reuses all 6 rules from rule 2 and 3
def circle_lt_3(triangle, square, circle):
    return(circle < 3)
def circle_eq_3(triangle, square, circle):
    return(circle == 3)
def circle_gt_3(triangle, square, circle):
    return(circle > 3)

# rule 41
def triangle_lt_4(triangle, square, circle):
    return(triangle < 4)
def triangle_eq_4(triangle, square, circle):
    return(triangle == 4)
def triangle_gt_4(triangle, square, circle):
    return(triangle > 4)
def circle_lt_4(triangle, square, circle):
    return(circle < 4)
def circle_eq_4(triangle, square, circle):
    return(circle == 4)
def circle_gt_4(triangle, square, circle):
    return(circle > 4)

# rule 44
def square_lt_circle(triangle, square, circle):
    return(square < circle)
def square_eq_circle(triangle, square, circle):
    return(square == circle)
def square_gt_circle(triangle, square, circle):
    return(square > circle)
rcs_deck = { #dict from num: rules list. Dictionary rather than list for ease of reading/changing
     1: [triangle_eq_1, triangle_gt_1],
     2: [triangle_lt_3, triangle_eq_3, triangle_gt_3],
     3: [square_lt_3, square_eq_3, square_gt_3],
     4: [square_lt_4, square_eq_4, square_gt_4],
     5: [triangle_even, triangle_odd],
     6: [square_even, square_odd],
     7: [circle_even, circle_odd],
     8: [zero_1, one_1, two_1, three_1],
     9: [zero_3, one_3, two_3, three_3],
    10: [zero_4, one_4, two_4, three_4],
    11: [triangle_lt_square, triangle_eq_square, triangle_gt_square],
    12: [triangle_lt_circle, triangle_eq_circle, triangle_gt_circle],
    13: [square_lt_circle, square_eq_circle, square_gt_circle],
    14: [triangle_strict_min, square_strict_min, circle_strict_min],
    15: [triangle_strict_max, square_strict_max, circle_strict_max],
    16: [more_evens, more_odds],
    17: [zero_evens, one_even, two_evens],
    18: [sum_digits_even, sum_digits_odd],
    19: [tri_plus_sq_lt_6, tri_plus_sq_eq_6, tri_plus_sq_gt_6],
    20: [triple_rep, double_rep, no_rep],
    21: [no_pairs, double_rep],
    22: [strictly_ascending, strictly_descending, neither_asc_desc],
    23: [sum_digits_lt_6, sum_digits_eq_6, sum_digits_gt_6],
    24: [cons_seq_cons_asc_3, cons_seq_cons_asc_2, cons_seq_cons_asc_0],
    25: [cons_seq_cons_0, cons_seq_cons_2, cons_seq_cons_3],

    27: [triangle_lt_4, square_lt_4, circle_lt_4],
    28: [triangle_eq_1, square_eq_1, circle_eq_1],

    30: [triangle_eq_4, square_eq_4, circle_eq_4],
    31: [triangle_gt_1, square_gt_1, circle_gt_1],

    33: [triangle_even, triangle_odd, square_even, square_odd, circle_even, circle_odd],
    34: [triangle_a_min, square_a_min, circle_a_min],

    36: [sum_dig_3x, sum_dig_4x, sum_dig_5x],
    37: [tri_plus_sq_4, tri_plus_ci_4, sq_plus_ci_4],


    40: [
            triangle_lt_3, triangle_eq_3, triangle_gt_3,
            square_lt_3, square_eq_3, square_gt_3,
            circle_lt_3, circle_eq_3, circle_gt_3
        ],
    41: [
            triangle_lt_4, triangle_eq_4, triangle_gt_4,
            square_lt_4, square_eq_4, square_gt_4,
            circle_lt_4, circle_eq_4, circle_gt_4,
        ],

    43: [triangle_lt_square, triangle_eq_square, triangle_gt_square,
         triangle_lt_circle, triangle_eq_circle, triangle_gt_circle],
    44: [triangle_lt_square, triangle_eq_square, triangle_gt_square,
         square_lt_circle, square_eq_circle, square_gt_circle],

    46: [zero_3, one_3, two_3, zero_4, one_4, two_4],
    47: [zero_1, one_1, two_1, zero_4, one_4, two_4]

}

# max_rule_name_length = max([max([len(r.__name__) for r in rc]) for rc in rcs_deck.values()])
# longest_rule_name = max([max([(len(r.__name__), r.__name__) for r in rc]) for rc in rcs_deck.values()])[1]
# print(longest_rule_name, max_rule_name_length)
# card_index is the rule's index within the list that is the card. (i.e. 0th rule, 1st rule, 2nd rule, etc.)
_unique_id = -1
def _func_to_Rule(func, card_index):
    reject_set = {p for p in all_125_possibilities_set if not(func(*(int_to_tri_sq_ci_tuple(p))))}
    global _unique_id
    _unique_id += 1
    return(Rule(func.__name__, reject_set, func, card_index, _unique_id))

for (rule_card_num, rule_card) in rcs_deck.items():
    rcs_deck[rule_card_num] = [_func_to_Rule(f, i) for (i, f) in enumerate(rule_card)]
    # now rcs_deck is a dict from rule_card_num to a list of Rules (see definitions.py)

def rule_with_new_id(old_rule, new_id):
    return(Rule(old_rule.name, old_rule.reject_set, old_rule.func, old_rule.card_index, new_id))

def rc_with_new_ids(rc, new_id_start):
    curr_new_id = new_id_start
    for rule_index in range(len(rc)):
        rc[rule_index] = rule_with_new_id(rc[rule_index], curr_new_id)
        curr_new_id += 1

def rcs_list_with_new_ids(rcs_list):
    curr_new_id = 0
    for rc_index in range(len(rcs_list)):
        rc_with_new_ids(rcs_list[rc_index], curr_new_id)
        curr_new_id += len(rcs_list[rc_index])

def make_rcs_list(problem: Problem) -> list[list[Rule]]:
    if((problem.mode == STANDARD) or (problem.mode == NIGHTMARE)):
        rcs_list = [rcs_deck[num] for num in problem.rc_nums_list]
    if(problem.mode == EXTREME):
        rcs_list = [
            (rcs_deck[problem.rc_nums_list[2 * n]] + rcs_deck[problem.rc_nums_list[(2 * n) + 1]]) for n in range(len(problem.rc_nums_list) // 2)
        ]
        # deduplicate rules in each rules card, b/c some extreme problems, like F5XTDF, have duplicates
        for rc_index in range(len(rcs_list)):
            rc = rcs_list[rc_index]
            new_rc = []
            rc_reject_sets_dict = dict() # key: reject set. value: name of the rule with that reject set.
            for rule in rc:
                fs_reject_set = frozenset(rule.reject_set)
                if(fs_reject_set in rc_reject_sets_dict):
                    print(f'{rule.name} is the same as {rc_reject_sets_dict[fs_reject_set]} in rule card {string.ascii_uppercase[rc_index]}.')
                else:
                    new_rc.append(rule)
                    rc_reject_sets_dict[fs_reject_set] = rule.name
            rcs_list[rc_index] = new_rc
            # changing the card_index of each rule for each rc in extreme mode, since cards are combined. Making new Rules b/c the fields of tuples aren't assignable.
            for (i, r) in enumerate(new_rc):
                new_rc[i] = Rule(r.name, r.reject_set, r.func, i, r.unique_id)
    rcs_list_with_new_ids(rcs_list)
    return(rcs_list)

def make_flat_rule_list(rcs_list) -> list[Rule]:
    flat_rule_index = 0
    flat_rule_list = []
    for rc in rcs_list:
        for r in rc:
            assert(r.unique_id == flat_rule_index)
            flat_rule_list.append(r)
            flat_rule_index += 1
    return(flat_rule_list)