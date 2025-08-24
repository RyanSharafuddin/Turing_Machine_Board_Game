import math, itertools
# from definitions import *
from .definitions import Query_Info, NIGHTMARE, console, all_125_possibilities_set
from . import config

############################## PRIVATE FUNCTIONS #################################################
def _get_all_rules_combinations(rcs_list):
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

def _is_combo_possible(combo):
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

def _get_possible_rules_combos_with_answers(rules_cards_list):
    all_rules_combos = _get_all_rules_combinations(rules_cards_list)
    return([(c, a) for (c,a) in [(c, _is_combo_possible(c)) for c in all_rules_combos] if(a is not None)])

_ISOMORPHIC    = 0
_NOT_ISOMOPHIC = 1
_EXCLUDE_FIRST = 2
_EXCLUDE_SECOND = 3
def _compare_two_proposals_inner_dicts(inner_dict_1: dict, inner_dict_2: dict, num_verifiers):
    """
    Returns one of 4 values:
    _ISOMORPHIC     if the 2 proposals are isomorphic.
    _NOT_ISOMORPHIC if they are not isomorphic and should be in separate isomorphic proposal lists.
    _EXCLUDE_FIRST  if the first is strictly less useful than the second and should not be in any list.
    _EXCLUDE_SECOND if the second is strictly less useful than the first and should not be in any list.
    """
    first_useful_on_something_second_isnt = False
    second_useful_on_something_first_isnt = False
    for v_index in range(num_verifiers):
        q_info1 = inner_dict_1.get(v_index, None)
        q_info2 = inner_dict_2.get(v_index, None)
        if(q_info1 is None):
            if(q_info2 is None):
                # both are None
                continue
            # 1 is None; q_info_2 is not None
            second_useful_on_something_first_isnt = True
            continue
        else:
            if(q_info2 is None):
                # 1 is not None; 2 is None
                first_useful_on_something_second_isnt = True
                continue

        # neither are None
        if not (
            # cwa_set representation_change (if numpy arrays for example, will have to change how they compare equal, by using == .all(), or something like that.)
            ((q_info1[0] == q_info2[0]) and (q_info1[1] == q_info2[1])) or
            ((q_info1[0] == q_info2[1]) and (q_info1[1] == q_info2[0]))
        ):
            return(_NOT_ISOMOPHIC)
    if(first_useful_on_something_second_isnt):
        if(second_useful_on_something_first_isnt):
            # They both cover verifiers the other doesn't.
            return(_NOT_ISOMOPHIC)
        else:
            # first is strictly more useful than second.
            return(_EXCLUDE_SECOND)
    else:
        if(second_useful_on_something_first_isnt):
            # second is strictly more useful than first
            return(_EXCLUDE_FIRST)
        else:
            # Neither covers a verifier the other doesn't
            return(_ISOMORPHIC)

def _init_base_qs_dict(full_cwas_list, flat_rule_list, n_mode):
    base_queries_dict = dict()
    rules_by_verifier = get_set_r_unique_ids_vs_from_full_cwas(full_cwas_list, n_mode)
    for (unsolved_verifier_index, possible_rule_ids_this_verifier) in enumerate(rules_by_verifier):
        if(len(possible_rule_ids_this_verifier) < 2):
            continue # this verifier is solved and has no useful queries, so on to the next one
        possible_rules_this_verifier = [flat_rule_list[r_id] for r_id in possible_rule_ids_this_verifier]
        for proposal in all_125_possibilities_set:
            rejecting_rules_ids = set()
            for possible_rule in possible_rules_this_verifier:
                if(proposal in possible_rule.reject_set):
                    rejecting_rules_ids.add(possible_rule.unique_id)
            if(0 < len(rejecting_rules_ids) < len(possible_rules_this_verifier)): # useful query
                # cwa_set representation_change
                cwa_set_true = set()
                cwa_set_false = set()
                for (cwa_index, cwa) in enumerate(full_cwas_list):
                    (c, p) = (cwa[0], cwa[1])
                    combo_rule_id = c[(
                        p[unsolved_verifier_index] if(n_mode) else unsolved_verifier_index
                    )].unique_id
                    # cwa_set representation_change
                    if(combo_rule_id in rejecting_rules_ids):
                        cwa_set_false.add(cwa_index)
                    else:
                        cwa_set_true.add(cwa_index)

                query_info = Query_Info(
                    cwa_set_true,
                    cwa_set_false
                )
                if(proposal in base_queries_dict):
                    inner_dict = base_queries_dict[proposal]
                    assert (not(unsolved_verifier_index in inner_dict))
                    inner_dict[unsolved_verifier_index] = query_info
                else:
                    base_queries_dict[proposal] = {
                        unsolved_verifier_index: query_info
                    }
    return(base_queries_dict)

def _get_isomorphic_proposals_lol(base_qs_dict: dict, num_verifiers):
    """
    Get a list of lists of isomorphic queries. If one query is strictly less useful than another (isomorphic to it for all verifiers it can be used on, but the set of verifiers it can be used on is a strict subset of the verifiers the other query can be used on), then it won't appear in any output list.
    """
    # TODO: instead of making the full list of list, just directly make the flat list of proposals you need right here. i.e. if you find that a proposal is isomorphic to something before it, don't append it to that list; just don't include it at all. Have this function return a flat list of all the proposals you need to include. Maybe make a debug mode function that does make the full lol.
    isomorphic_proposals_lol = []
    representative_info_list = [] # same type as what is used to compare in compare_two_proposals
    for (proposal, inner_dict) in base_qs_dict.items():
        for (list_index, (isomorphic_list, representative_info)) in enumerate(
            zip(isomorphic_proposals_lol, representative_info_list)
        ):
            if(isomorphic_list is None):
                # this list was found to be strictly less useful than a later list
                continue
            comparison_result = _compare_two_proposals_inner_dicts(
                inner_dict,
                representative_info,
                num_verifiers
            )
            if(comparison_result is _ISOMORPHIC):
                isomorphic_list.append(proposal)
                break
            elif(comparison_result is _EXCLUDE_FIRST):
                # debug mode print out a proposal got eliminated
                # console.print(f"{proposal} is strictly [red]less[/red] useful than list {list_index:>3}.")
                break
            elif(comparison_result is _EXCLUDE_SECOND):
                # debug mode print out a proposal list is about to get eliminated
                # if you're in debug mode, can print out something here to show which proposals are about to be eliminated. Consider looking into if __debug__ and see if there's a way to optimize it away when running for real without changing code.
                # console.print(f"{proposal} is strictly [green]more[/green] useful than list {list_index:>3}.")
                isomorphic_proposals_lol[list_index] = None
                # NOTE: should NOT break out of loop early here, b/c even though this proposal is guaranteed to not be isomorphic to any of the other proposals in any isomorphic proposals list, it could still eliminate more future isomorphic proposals lists from the LOL, and if you broke out of this loop right now, those future isomorphic proposals lists that should have been eliminated will not be eliminated.
            # otherwise, this proposal is not isomorphic to this list, but also not strictly more or less useful, so need to keep looking.
        else:
            # Found a new group of isomorphic queries
            isomorphic_proposals_lol.append([proposal])
            representative_info_list.append(inner_dict)

    isomorphic_proposals_lol = [isomorphic_l for isomorphic_l in isomorphic_proposals_lol if (isomorphic_l is not None)]
    return(isomorphic_proposals_lol)

def _filter_out_isomorphic_proposals(base_qs_dict, isomorphic_proposals_lol):
    """
    Given a queries dict and a an isomorphic_qs_lol, returns a new qs dict that contains only one of each isomorphic query.
    WARN: pay attention to whether this mutates the dict or returns a new one. Currently returns new. 
    """
    return_dict = dict()
    for isomorphic_proposals_list in isomorphic_proposals_lol:
        proposal = isomorphic_proposals_list[0]
        return_dict[proposal] = base_qs_dict[proposal]
        # return_dict = base_qs_dict
        # for proposal in isomorphic_list[1:]:
        #     del(base_qs_dict[proposal])
    return(return_dict)

############################## PUBLIC FUNCTIONS #################################################
def get_set_r_unique_ids_vs_from_full_cwas(full_cwas, n_mode: bool):
    """
    Given a full_cwas iterable, returns a list, where list[i] contains a set of the unique_ids for all possible rules for verifier i. Note: this is used in display.py for printing useful_qs_dict info, to display what rules are possible for each verifier.
    """
    num_vs = len(full_cwas[0][0])
    # TODO: consider optimizing the 'sets' belows w/ bitarray or python int or numpy packed bits or something.
    possible_rule_ids_by_verifier = [set() for _ in range(num_vs)]
    for cwa in full_cwas:
        (c, p) = (cwa[0], cwa[1])
        for (v_index, rule) in enumerate(c):
            corresponding_set = possible_rule_ids_by_verifier[v_index]
            possible_rule = c[p[v_index]] if(n_mode) else rule
            corresponding_set.add(possible_rule.unique_id)
    return(possible_rule_ids_by_verifier)

def make_full_cwas_list(problem, rcs_list):
    possible_combos_with_answers = _get_possible_rules_combos_with_answers(rcs_list)
    if(problem.mode == NIGHTMARE):
        nightmare_possible_combos_with_answers = []
        vs = list(range(len(rcs_list))) # vs = [0, 1, 2, . . . for number of verifiers]
        verifier_permutations = tuple(itertools.permutations(vs))
        for original_cwa in possible_combos_with_answers:
            for v_permutation in verifier_permutations:
                nightmare_possible_combos_with_answers.append((original_cwa[0], v_permutation, original_cwa[1]))
        possible_combos_with_answers = nightmare_possible_combos_with_answers
        # possible_combos_with_answers is now [(full rule combo, full permutation, answer), ...]
    # sort the possible cwas by answer. Will be helpful in calculating one_answer_left when switch to bitsets.
    possible_combos_with_answers.sort(key=lambda t:t[-1])
    return(possible_combos_with_answers)

def get_dict_filtered_of_isomorphic_proposals(base_qs_dict, num_verifiers):
    """ Given a queries dict, returns a NEW queries dict with the isomorphic queries filtered out. """
    isomorphic_proposals_lol = _get_isomorphic_proposals_lol(base_qs_dict, num_verifiers)
    filtered_qs_dict = _filter_out_isomorphic_proposals(base_qs_dict, isomorphic_proposals_lol)
    return(filtered_qs_dict)

def make_useful_qs_dict(full_cwas_list, flat_rule_list, n_mode):
    if not full_cwas_list: # only happens on invalid problems.
        return None
    base_qs_dict = _init_base_qs_dict(
        full_cwas_list,
        flat_rule_list,
        n_mode
    )
    num_verifiers = len(full_cwas_list[0][0])
    isomorphic_proposals_lol = _get_isomorphic_proposals_lol(base_qs_dict, num_verifiers)
    useful_qs_dict = _filter_out_isomorphic_proposals(base_qs_dict, isomorphic_proposals_lol)

    if(config.PRINT_ISOMORPHIC_LOL):
        print("Isomorphic lol printed from solver_utils.make_useful_qs_dict")
        for (index, isomorphic_list) in enumerate(isomorphic_proposals_lol):
            console.print(f'{index:>3,}', isomorphic_list, end=" ")
        console.print(f"Saved {len(base_qs_dict) - len(isomorphic_proposals_lol)} proposals out of {len(base_qs_dict)}!")
    return(useful_qs_dict)

def filter_useless_and_update_qs_dict(qs_dict: dict, current_cwa_set):
    """
    Given a qs dict and a current set of cwas, returns a new qs dict that has useless queries removed and where each q_info contains the minimum possible amount of cwas.
    """
    new_qs_dict = dict()
    for (proposal, inner_dict) in qs_dict.items():
        have_put_proposal_into_new_dict = False
        for (v_index, q_info) in inner_dict:
            (q_info_true, q_info_false) =  q_info
            cwa_set_true = q_info_true & current_cwa_set
            cwa_set_false = q_info_false & current_cwa_set
            if(bool(cwa_set_false) and bool(cwa_set_true)):
                new_q_info = Query_Info(cwa_set_true=cwa_set_true, cwa_set_false=cwa_set_false)
                if not have_put_proposal_into_new_dict:
                    new_qs_dict[proposal] = {v_index: new_q_info}
                    have_put_proposal_into_new_dict = True
                else:
                    new_qs_dict[proposal][v_index] = new_q_info
    return(new_qs_dict)

# NOTE: all calculate_*_cost functions need to take the same 3 parameters, regardless of whether they use them
def calculate_expected_cost(mcost, probs, gss_costs):
    (mcost_rounds, mcost_queries) = mcost
    (p_false, p_true) = probs
    ((gs_false_round_cost, gs_false_query_cost), (gs_true_round_cost, gs_true_query_cost)) = gss_costs
    expected_r_cost = mcost_rounds + (p_false * gs_false_round_cost) + (p_true * gs_true_round_cost)
    expected_q_cost = mcost_queries + (p_false * gs_false_query_cost) + (p_true * gs_true_query_cost)
    return((expected_r_cost, expected_q_cost))
def calculate_worst_case_cost(mcost, probs, gss_costs):
    bigger_cost_tup = max(gss_costs)
    # WARN: don't use the add_tups function from definitions.py here, b/c this is very time-sensitive and Python is very slow. On problem f5x, using add_tups here single-handedly causes it to take 94 seconds instead of 80.
    # tie_breaker = calculate_expected_cost(mcost, probs, gss_costs)
    # return((bigger_cost_tup[0] + mcost[0], bigger_cost_tup[1] + 1, tie_breaker))
    # Using a tiebreaker to differentiate b/t nodes with the same worst case costs is pretty interesting, but rather expensive, as it adds +10% total time.
    return((bigger_cost_tup[0] + mcost[0], bigger_cost_tup[1] + 1))
