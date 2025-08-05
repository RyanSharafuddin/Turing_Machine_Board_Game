import math, string, itertools
import display, rules
from definitions import *

def get_all_rules_combinations(rcs_list):
    """ Returns all combinations of rules from the rules cards, whether possible or not. """
    num_rules_cards = len(rcs_list)
    rcs_lengths = [len(rules_card) for rules_card in rcs_list]
    total_num_combinations = math.prod(rcs_lengths)
    rules_combos = [
        [
            rcs_list[rc_index][
                (combo_num // math.prod(rcs_lengths[rc_index + 1:])) % rcs_lengths[rc_index]
            ]
            for rc_index in range(num_rules_cards)
        ] for combo_num in range(total_num_combinations)
    ]
    # print all combos, possible or not.
    # for (combo_num, combo) in enumerate(rules_combos, start=1):
    #     print(f'{combo_num}: {[rule.name for rule in combo]}')
    return(rules_combos)

def is_combo_possible(combo):
    """
    WARN: can return None.
    In Turing Machine, there are 2 requirements that any valid combination of verifiers/rules must satisfy:
    1) There must be exactly one possible answer.
    2) Each verifier eliminates at least one possibility that is not eliminated by any other verifier.
    If the rules in combo satisfy those requirements, this function will return the one answer that satisfies all verifiers. Otherwise, this function will return None.
    """
    reject_sets = [rule.reject_set for rule in combo]
    reject_sets_unions = set.union(*reject_sets)
    if(len(reject_sets_unions) != (len(all_125_possibilities_set) - 1)):
        return(None)
    answer = (all_125_possibilities_set - reject_sets_unions).pop()
    for (i, reject_set) in enumerate(reject_sets):
        all_other_reject_sets = reject_sets[0 : i] + reject_sets[i + 1 :]
        other_reject_sets_union = set.union(*all_other_reject_sets)
        if(not(reject_set - other_reject_sets_union)):
            return(None) # means that this rule is redundant.
    return(answer)

def get_possible_rules_combos_with_answers(rules_cards_list):
    all_rules_combos = get_all_rules_combinations(rules_cards_list)
    return([(c, a) for (c,a) in [(c, is_combo_possible(c)) for c in all_rules_combos] if(a is not None)])


def get_unsolved_verifier_indices(rc_infos):
    unsolved_verifier_indices = [verifier_index for (verifier_index, rc_info) in enumerate(rc_infos) if(len(rc_info) > 1)]
    return(unsolved_verifier_indices)

def populate_useful_qs_dict(rcs_list, all_125_possibilities_set, possible_combos_with_answers, mode):
    useful_queries_dict = dict()
    rc_infos = Solver.make_rc_infos(len(rcs_list), possible_combos_with_answers, mode)
    # unzipped_full_cwa = list(zip(*possible_combos_with_answers))
    # (possible_combos, possible_permutations, possible_answers) = [unzipped_full_cwa[i] for i in (0, 1, -1)]

    # TODO: delete testing lines from here down to exit()
    # for rc_index in range(len(rcs_list)):
    #     display.print_rc_info(rc_infos, rc_index, mode)
    # END delete testing lines

    # set_possible_answers = frozenset(possible_answers)
    # current_num_possible_combos = len(possible_combos)
    # current_num_possible_answers = len(set_possible_answers)
    for unsolved_verifier_index in get_unsolved_verifier_indices(rc_infos):
        corresponding_rc_info = rc_infos[unsolved_verifier_index]
        possible_rules_this_verifier = \
            [rcs_list[rc_index][rule_index] for (rc_index, rule_index) in corresponding_rc_info.keys()] \
            if(mode == NIGHTMARE) else \
            [rcs_list[unsolved_verifier_index][rule_index] for rule_index in corresponding_rc_info.keys()]

        for possible_query in all_125_possibilities_set:
            accepting_rules_ids = set()
            rejecting_rules_ids = set()
            for possible_rule in possible_rules_this_verifier:
                if(possible_query in possible_rule.reject_set):
                    rejecting_rules_ids.add(possible_rule.unique_id)
                else:
                    accepting_rules_ids.add(possible_rule.unique_id)
            if(bool(accepting_rules_ids) and bool(rejecting_rules_ids)):
                # TODO: make both of the below sets right off the bat if you're going to make new useful queries dicts while solving the problem. And make them the set of (card_indices_combo, answer) immediately; don't waste time with anything unnecessary, like appending to any lists of full combos or calculating expected info gain. And get rid of the set_answers remaining (NOT the set_cwa_remaining)
                possible_combos_with_answers_remaining_if_true = []
                possible_combos_with_answers_remaining_if_false = []
                for combo_with_answer in possible_combos_with_answers:
                    (combo, permutation, answer) = [combo_with_answer[i] for i in (0, 1, -1)]
                    combo_rule_id = \
                        combo[permutation[unsolved_verifier_index]].unique_id \
                        if(mode == NIGHTMARE) else \
                        combo[unsolved_verifier_index].unique_id
                    if(combo_rule_id in accepting_rules_ids):
                        possible_combos_with_answers_remaining_if_true.append(combo_with_answer)
                    elif(combo_rule_id in rejecting_rules_ids):
                        possible_combos_with_answers_remaining_if_false.append(combo_with_answer)
                    else:
                        print("Teh program is broken if this happens")
                        exit()

                # TODO: don't really need this block here, since each combo_with_answer is put into exactly one of the remaining if true or if false.
                # num_combos_remaining_if_true = len(possible_combos_with_answers_remaining_if_true)
                # num_combos_remaining_if_false = len(possible_combos_with_answers_remaining_if_false)
                # if((num_combos_remaining_if_true + num_combos_remaining_if_false) != current_num_possible_combos):
                #     raise Exception("FAIL")

                # (combos_remaining_if_true, answers_remaining_if_true) = zip(*possible_combos_with_answers_remaining_if_true)
                # # WARN: do not use set_answers_remaining... unless you plan to recalculate q_infos every query.
                # set_answers_remaining_if_true = set(answers_remaining_if_true)
                # num_answers_remaining_if_true = len(set_answers_remaining_if_true)

                # (combos_remaining_if_false, answers_remaining_if_false) = zip(*possible_combos_with_answers_remaining_if_false)
                # # WARN: see warning above
                # set_answers_remaining_if_false = set(answers_remaining_if_false)
                # num_answers_remaining_if_false = len(set_answers_remaining_if_false)


                # NOTE: It's okay if the number of answers remaining when true and when false don't add up to the number of answers currently, because it's not the case that every answer remains only when true or only when false. Every *combo* remains only when true or only when false, but sometimes one answer can have multiple combos, so it it remains when the query is true and when it's false. To see an example of this, uncomment the block below and try on problem [9, 22, 24, 31, 37, 40] ("C63 0YV B" online).
                # if((num_answers_remaining_if_true + num_answers_remaining_if_false) != current_num_possible_answers):
                #     print(f"Failed when considering query: {possible_query} on card {string.ascii_uppercase[unsolved_card_index]}")
                #     display.print_all_possible_answers("Combos remaining if true:", set_answers_remaining_if_true, possible_combos_with_answers_remaining_if_true)
                #     display.print_all_possible_answers("Combos remaining if false:", set_answers_remaining_if_false, possible_combos_with_answers_remaining_if_false)
                #     exit()

                # p_true = num_combos_remaining_if_true / current_num_possible_combos
                # answer_info_gain_true = math.log2(
                #     current_num_possible_answers / num_answers_remaining_if_true
                # )
                # combo_info_gain_true = math.log2(
                #     current_num_possible_combos / num_combos_remaining_if_true
                # )
                # p_false = num_combos_remaining_if_false / current_num_possible_combos
                # answer_info_gain_false = math.log2(
                #     current_num_possible_answers / num_answers_remaining_if_false
                # )
                # combo_info_gain_false = math.log2(
                #     current_num_possible_combos / num_combos_remaining_if_false
                # )
                # expected_answer_info_gain = (
                #     (p_true * answer_info_gain_true) + (p_false * answer_info_gain_false)
                # )
                # expected_combo_info_gain = (
                #     (p_true * combo_info_gain_true) + (p_false * combo_info_gain_false)
                # )

                query_info = Query_Info(
                    # possible_combos_with_answers_remaining_if_true,
                    # possible_combos_with_answers_remaining_if_false,
                    # p_true,
                    # answer_info_gain_true,
                    # answer_info_gain_false,
                    # expected_answer_info_gain,
                    # expected_combo_info_gain,
                    set(
                        [
                            ((tuple([r.card_index for r in cwa[0]]),) + cwa[1:]) for cwa in
                            possible_combos_with_answers_remaining_if_true
                        ]
                    ),
                    set(
                        [
                            ((tuple([r.card_index for r in cwa[0]]),) + cwa[1:]) for cwa in
                            possible_combos_with_answers_remaining_if_false
                        ]
                    )
                )
                if(possible_query in useful_queries_dict):
                    inner_dict = useful_queries_dict[possible_query]
                    if(unsolved_verifier_index in inner_dict):
                        print("This shouldn't happen, because you're going over every card/every possible query to that card only once.")
                        exit()
                    else:
                        inner_dict[unsolved_verifier_index] = query_info
                else:
                    useful_queries_dict[possible_query] = {
                        unsolved_verifier_index: query_info
                    }

    # TODO delete this block
    for v_index in range(len(rcs_list)):
        sd.print_useful_qs_dict_info(useful_queries_dict, v_index, rc_infos, rcs_list, mode)
        # sd.print_useful_qs_dict_info(useful_queries_dict, v_index, rc_infos, rcs_list, mode, see_all_combos=(mode != NIGHTMARE))
        pass
    # exit()
    return(useful_queries_dict)

def fset_answers_from_cwa_iterable(cwa_iterable):
    return(frozenset([cwa[-1] for cwa in cwa_iterable]))

def create_move_info(num_combos_currently, game_state, num_queries_this_round, q_info, move, cost):
    """
    num_queries_this_round is the number there will be after making this move.
    WARN: could be None
    """
    fset_indexes_cwa_remaining_true = game_state.fset_cwa_indexes_remaining & q_info.set_indexes_cwa_remaining_true
    fset_indexes_cwa_remaining_false = game_state.fset_cwa_indexes_remaining & q_info.set_indexes_cwa_remaining_false
    if(bool(fset_indexes_cwa_remaining_false) and bool(fset_indexes_cwa_remaining_true)):
        # this is a useful query.
        num_combos_remaining_true = len(fset_indexes_cwa_remaining_true)
        p_true = num_combos_remaining_true / num_combos_currently
        p_false = 1 - p_true
        p_tuple = (p_false, p_true)
        proposal_used_this_round = None if(num_queries_this_round == 0) else move[0]
        game_state_false = Game_State(
            num_queries_this_round = num_queries_this_round,
            proposal_used_this_round = proposal_used_this_round,
            fset_cwa_indexes_remaining = fset_indexes_cwa_remaining_false,
        )
        game_state_true = Game_State(
            num_queries_this_round = num_queries_this_round,
            proposal_used_this_round = proposal_used_this_round,
            fset_cwa_indexes_remaining = fset_indexes_cwa_remaining_true,
        )
        gs_tuple = (game_state_false, game_state_true)
        move_info = (move, cost, gs_tuple, p_tuple)
    else:
        # this is not a useful query. Take move out of the game state frozen set representing remaining moves, if you implement it. Actually, take out all such useless moves before making the next game states. Will require some refactoring.
        move_info = None
    return(move_info)

def get_and_apply_moves(game_state, qs_dict):
    """
    yields from a list of [(move, cost, (game_state_false, game_state_true), (p_false, p_true))].
    move is a tuple (proposal tuple, rc_index of verifier to query).
    cost is a tuple (round cost, query cost)
    """
    # calling len() to figure out num_combos_currently here so don't have to do it repeatedly inside loop
    num_combos_currently = len(game_state.fset_cwa_indexes_remaining)
    if (game_state.proposal_used_this_round is not None):
        # There is an existing proposal that you've used in this game state that you can use again without incurring a round cost.
        inner_dict_this_proposal = qs_dict.get(game_state.proposal_used_this_round)
        if(not(inner_dict_this_proposal is None)): # If this proposal still has potentially useful queries
            cost = (0, 1) # considering all queries that don't incur a round cost
            next_num_queries = (game_state.num_queries_this_round + 1) % 3
            for (rc_index, q_info) in inner_dict_this_proposal.items():
                move = (game_state.proposal_used_this_round, rc_index)
                move_info = create_move_info(num_combos_currently, game_state, next_num_queries, q_info, move, cost)
                if(move_info is not None):
                    yield(move_info)
                else:
                    pass # not a useful query. See other comments.

    # Have finished yielding all moves that don't incur a round cost (if there were any). Now consider all moves which do incur a round cost.
    cost = (1, 1)
    next_num_queries = 1
    for (proposal, inner_dict) in qs_dict.items():
        if(proposal == game_state.proposal_used_this_round):
            continue # no sense starting a new round when you could have remained on same round.
        for (rc_index, q_info) in inner_dict.items():
            move = (proposal, rc_index)
            move_info = create_move_info(num_combos_currently, game_state, next_num_queries, q_info, move, cost)
            if(move_info is not None):
                yield(move_info)
            else:
                pass # not a useful query

def calculate_expected_cost(mcost, probs, gss_costs):
    (mcost_rounds, mcost_queries) = mcost
    (p_false, p_true) = probs
    ((gs_false_round_cost, gs_false_query_cost), (gs_true_round_cost, gs_true_query_cost)) = gss_costs
    expected_r_cost = mcost_rounds + (p_false * gs_false_round_cost) + (p_true * gs_true_round_cost)
    expected_q_cost = mcost_queries + (p_false * gs_false_query_cost) + (p_true * gs_true_query_cost)
    return((expected_r_cost, expected_q_cost))

def fset_cwa_indexes_remaining_from_full_cwa(full_cwa):
    fset_cwa_indexes_remaining = frozenset(
            [(tuple([r.card_index for r in cwa[0]]),) + cwa[1:] for cwa in full_cwa]
        )
    return(fset_cwa_indexes_remaining)

def make_rcs_list(problem):
    if((problem.mode == STANDARD) or (problem.mode == NIGHTMARE)):
        rcs_list = [rules.rcs_deck[num] for num in problem.rc_nums_list]
    if(problem.mode == EXTREME):
        rcs_list = [(rules.rcs_deck[problem.rc_nums_list[2 * n]] + rules.rcs_deck[problem.rc_nums_list[(2 * n) + 1]]) for n in range(len(problem.rc_nums_list) // 2)]
        # deduplicate rules in each rules card, b/c some extreme problems, like F5XTDF, have duplicates
        for rc_index in range(len(rcs_list)):
            rc = rcs_list[rc_index]
            new_rc = []
            rc_reject_sets_dict = dict() # key: reject set. value: name of the rule with that reject set.
            for rule in rc:
                fs_reject_set = frozenset(rule.reject_set)
                if(fs_reject_set in rc_reject_sets_dict):
                    print(f'{rule.name} is the same as {rc_reject_sets_dict[fs_reject_set]} in rc {string.ascii_uppercase[rc_index]}')
                else:
                    new_rc.append(rule)
                    rc_reject_sets_dict[fs_reject_set] = rule.name
            rcs_list[rc_index] = new_rc
            # changing the card_index of each rule for each rc in extreme mode, since cards are combined. Making new Rules b/c the fields of tuples aren't assignable.
            for (i, r) in enumerate(new_rc):
                new_rc[i] = Rule(r.name, r.reject_set, r.func, i, r.unique_id)
    return(rcs_list)

def make_full_cwa(problem, rcs_list):
    possible_combos_with_answers = get_possible_rules_combos_with_answers(rcs_list)
    if(problem.mode == NIGHTMARE):
        nightmare_possible_combos_with_answers = []
        vs = list(range(len(rcs_list))) # vs = [0, 1, 2, . . . for number of verifiers]
        verifier_permutations = tuple(itertools.permutations(vs))
        for original_cwa in possible_combos_with_answers:
            for v_permutation in verifier_permutations:
                nightmare_possible_combos_with_answers.append((original_cwa[0], v_permutation, original_cwa[1]))
        possible_combos_with_answers = nightmare_possible_combos_with_answers
        # possible_combos_with_answers is now [(full rule combo, full permutation, answer), ...]
    if(not(possible_combos_with_answers)):
        display.print_problem(rcs_list, problem)
        print("User error: you have entered a problem which has no valid solutions. Check that you entered the problem in correctly and that you defined the rules correctly in rules.py. Exiting.")
        exit()
    return(possible_combos_with_answers)

class Solver:
    def __init__(self, problem):
        self.problem            = problem
        self.evaluations_cache  = dict()
        self.rcs_list           = make_rcs_list(problem)
        self.full_cwa           = make_full_cwa(problem, self.rcs_list)
        self.initial_game_state = Game_State(0, None, fset_cwa_indexes_remaining_from_full_cwa(self.full_cwa))

        # TODO delete testing lines below
        display.print_problem(self.rcs_list, problem)
        display.print_all_possible_answers("\nAll possible answers:", self.full_cwa, problem.mode)
        # END delete testing lines

        # self.rc_indexes_cwa_to_full_combos_dict # TODO eliminate in favor of simple possible_combos_with_answers list + integer indices everywhere, like in game states and q infos.
        self.rc_indexes_cwa_to_full_combos_dict = {
            (tuple([r.card_index for r in cwa[0]]),) + cwa[1:] : cwa for cwa in self.full_cwa
        }

        # TODO delete the testing lines below
        global sd
        sd = display.Solver_Displayer(self)

        self.qs_dict        = populate_useful_qs_dict(
            self.rcs_list, all_125_possibilities_set, self.full_cwa, problem.mode
        )

    @staticmethod
    def make_rc_infos(num_rcs, possible_combos_with_answers, mode):
        """ O(n) in length of possible_combos_with_answers """
        rc_infos = [dict() for _ in range(num_rcs)]
        for cwa in possible_combos_with_answers:
            (c, p, a) = (cwa[0], cwa[1], cwa[-1]) # p is permutation if mode is NIGHTMARE
            for (verifier_index, rule) in enumerate(c):
                rc_info_dict = rc_infos[verifier_index]
                # in NIGHTMARE mode, the outer key is a tuple of ints
                # outer key = (index of the rc this verifier corresponds to, index of the rule within that rc)
                # otherwise, it's just an int that is the index of the rule within that rc
                outer_key = (p[verifier_index], c[p[verifier_index]].card_index) if (mode == NIGHTMARE) else rule.card_index
                inner_val_list_item = (c, p) if (mode == NIGHTMARE) else c
                if(outer_key in rc_info_dict):
                    this_rule_s_inner_dict = rc_info_dict[outer_key]
                    if(a) in this_rule_s_inner_dict:
                        this_rule_s_inner_dict[a].append(inner_val_list_item)
                    else:
                        this_rule_s_inner_dict[a] = [inner_val_list_item]
                else:
                    rc_info_dict[outer_key] = {a: [inner_val_list_item]}
        return(rc_infos)

    # see get_moves docstring for definitions of move and cost.
    # NOTE: don't use the class's qs_dict just yet. Keep passing it down, in case you want to make new ones in the future. See todo.txt.
    def calculate_best_move(self, qs_dict, game_state):
        """
        Returns a tuple (best move in this state, mov_cost_tup, gs_tup, expected cost to win from game_state (this is a tuple of (expected rounds, expected total queries))).
        best_move_tup is a tup of (proposal, rc_index)
        """
        if(game_state in self.evaluations_cache):
            return(self.evaluations_cache[game_state])
        if(len(fset_answers_from_cwa_iterable(game_state.fset_cwa_indexes_remaining)) == 1):
            # don't bother filling up the cache with already-won states.
            return( (None, None, None, (0,0)) )
        best_expected_cost = (float('inf'), float('inf'))
        found_zero_more_round_sol = False
        exist_moves_that_dont_cost_a_round = False
        for move_info in get_and_apply_moves(game_state, qs_dict):
            (move, mcost, gs_tup, p_tup) = move_info
            if(mcost[0] == 0):
                exist_moves_that_dont_cost_a_round = True
            if((mcost[0] == 1) and (exist_moves_that_dont_cost_a_round or found_zero_more_round_sol)):
                # there are moves that don't cost a new round, so don't consider any moves that cost a round.
                # or have found a 0 round soln, so don't consider any moves that do cost a round.
                # NOTE: although exist_moves_that_dont_cost_a_round significantly prunes the tree, I'm not convinced this will necessarily find a best move.
                break
            gs_false_expected_cost = self.calculate_best_move(qs_dict, gs_tup[0])[3]
            gs_true_expected_cost = self.calculate_best_move(qs_dict, gs_tup[1])[3]
            gss_costs = (gs_false_expected_cost, gs_true_expected_cost)
            expected_cost_tup = calculate_expected_cost(mcost, p_tup, gss_costs)
            if(expected_cost_tup < best_expected_cost):
                if(expected_cost_tup[0] == 0):
                    found_zero_more_round_sol = True
                best_expected_cost = expected_cost_tup
                best_move = move
                best_mov_cost = mcost
                best_gs_tup = gs_tup
                if((expected_cost_tup == (0, 1)) or ((expected_cost_tup == (1, 1)) and game_state.proposal_used_this_round is None)): # can solve within 1 query and 0 rounds, or 1 query and all queries cost a round, so return early
                    break
        answer = (best_move, best_mov_cost, best_gs_tup, best_expected_cost)
        self.evaluations_cache[game_state] = answer
        return(answer)

    def solve(self):
        """
        Sets up evaluations_cache with the evaluations of all necessary game states.
        """
        self.calculate_best_move(qs_dict = self.qs_dict, game_state = self.initial_game_state)

    def full_cwa_from_game_state(self, gs):
        return([self.rc_indexes_cwa_to_full_combos_dict[cwa] for cwa in gs.fset_cwa_indexes_remaining])

def solve(problem):
    s = Solver(problem)
    s.solve()
    return(s)