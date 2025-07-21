# rule 1
def triangle_eq_1(triangle, square, circle):
    return(triangle == 1)
def triangle_greater_1(triangle, square, circle):
    return(triangle > 1)
# rule 2
def triangle_less_3(triangle, square, circle):
    return(triangle < 3)
def triangle_eq_3(triangle, square, circle):
    return(triangle == 3)
def triangle_greater_3(triangle, square, circle):
    return(triangle > 3)
#rule 3
def square_less_3(triangle, square, circle):
    return(square < 3)
def square_eq_3(triangle, square, circle):
    return(square == 3)
def square_greater_3(triangle, square, circle):
    return(square > 3)
#rule 4
def square_less_4(triangle, square, circle):
    return(square < 4)
def square_eq_4(triangle, square, circle):
    return(square == 4)
def square_greater_4(triangle, square, circle):
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
def triangle_less_square(triangle, square, circle):
    return(triangle < square)
def triangle_eq_square(triangle, square, circle):
    return(triangle == square)
def triangle_greater_square(triangle, square, circle):
    return(triangle > square)

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


def sum_digits_even(triangle, square, circle):
    return(((triangle + square + circle) % 2) == 0)
def sum_digits_odd(triangle, square, circle):
    return(((triangle + square + circle) % 2) == 1)

def strictly_ascending(triangle, square, circle):
    return(triangle < square < circle)
def strictly_descending(triangle, square, circle):
    return(triangle > square > circle)
def neither_asc_nor_desc(triangle, square, circle):
    return(not(strictly_ascending(triangle, square, circle) or strictly_descending(triangle, square, circle)))



rcs_deck = { #dict from num: rules list. Dictionary rather than list for ease of reading/changing
    1: [triangle_eq_1, triangle_greater_1],
    2: [triangle_less_3, triangle_eq_3, triangle_greater_3],
    3: [square_less_3, square_eq_3, square_greater_3],
    4: [square_less_4, square_eq_4, square_greater_4],
    5: [triangle_even, triangle_odd],
    6: [square_even, square_odd],
    7: [circle_even, circle_odd],

    9: [zero_3, one_3, two_3, three_3],
    10: [zero_4, one_4, two_4, three_4],
    11: [triangle_less_square, triangle_eq_square, triangle_greater_square],


    14: [triangle_strict_min, square_strict_min, circle_strict_min],
    15: [triangle_strict_max, square_strict_max, circle_strict_max],


    18: [sum_digits_even, sum_digits_odd],



    22: [strictly_ascending, strictly_descending, neither_asc_nor_desc]
}

max_rule_name_length = max([max([len(r.__name__) for r in rc]) for rc in rcs_deck.values()])
