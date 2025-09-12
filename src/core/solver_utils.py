import math, itertools, copy
import numpy as np
from .definitions import Query_Info, all_125_possibilities_set, Rule, Game_State, console # TODO: delete console
from .hashable_numpy_array import Hashable_Numpy_Array

############################## PRIVATE FUNCTIONS #################################################
def _get_all_rules_combinations(rcs_list):
    """
    Returns all combinations of rules from the rules cards, whether possible or not. Does not depend on card_index or any rule ID.
    """
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

def _is_combo_possible(combo: list[Rule]):
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
def _compare_two_proposals_small_partition_sets(sp_1: frozenset, sp_2: frozenset):
    """
    Returns one of 4 values:
    _ISOMORPHIC     if the 2 proposals are isomorphic.
    _NOT_ISOMORPHIC if they are not isomorphic and should be in separate isomorphic proposal lists.
    _EXCLUDE_FIRST  if the first is strictly less useful than the second and should not be in any list.
    _EXCLUDE_SECOND if the second is strictly less useful than the first and should not be in any list.
    """
    s1_len = len(sp_1)
    s2_len = len(sp_2)
    if(s1_len < s2_len):
        if(sp_1.issubset(sp_2)):
            return _EXCLUDE_FIRST
        return _NOT_ISOMOPHIC
    if(s1_len == s2_len):
        if(sp_1.issubset(sp_2)):
            return _ISOMORPHIC
        return _NOT_ISOMOPHIC
    if(s1_len > s2_len):
        if(sp_1.issuperset(sp_2)):
            return _EXCLUDE_SECOND
        return _NOT_ISOMOPHIC

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

def _get_isomorphic_proposals_lol(small_partition_set_dict: dict):
    """
    Get a list of lists of isomorphic queries. If one query is strictly less useful than another (isomorphic to it for all verifiers it can be used on, but the set of verifiers it can be used on is a strict subset of the verifiers the other query can be used on), then it won't appear in any output list.
    """
    # TODO: instead of making the full list of list, just directly make the flat list of proposals you need right here. i.e. if you find that a proposal is isomorphic to something before it, don't append it to that list; just don't include it at all. Have this function return a flat list of all the proposals you need to include. Maybe make a debug mode function that does make the full lol.
    isomorphic_proposals_lol = []
    representative_info_list = [] # same type as what is used to compare in compare_two_proposals
    # global iso_filter_list_to_print # TODO: comment_out testing
    # iso_filter_list_to_print = [] # TODO: comment_out testing
    for (proposal, small_partition_set) in small_partition_set_dict.items():
        for (list_index, (isomorphic_list, representative_info)) in enumerate(
            zip(isomorphic_proposals_lol, representative_info_list)
        ):
            # TODO: when change this function to return a flat list, check if the representative_info is None, rather than the isomorphic_list.
            if(isomorphic_list is None):
                # this list was found to be strictly less useful than a later list
                continue
            comparison_result = _compare_two_proposals_small_partition_sets(
                small_partition_set,
                representative_info,
            )
            if(comparison_result is _ISOMORPHIC):
                isomorphic_list.append(proposal)
                break
            elif(comparison_result is _EXCLUDE_FIRST):
                # debug mode print out a proposal got eliminated
                # iso_filter_list_to_print.append(
                #     f"{proposal} is strictly [red]less[/red] useful than list {list_index:>3} {isomorphic_proposals_lol[list_index][0]}."
                # ) # TODO: comment_out testing
                break
            elif(comparison_result is _EXCLUDE_SECOND):
                # debug mode print out a proposal list is about to get eliminated
                # if you're in debug mode, can print out something here to show which proposals are about to be eliminated. Consider looking into if __debug__ and see if there's a way to optimize it away when running for real without changing code.
                # iso_filter_list_to_print.append(
                #     f"{proposal} is strictly [green]more[/green] useful than list {list_index:>3} {isomorphic_proposals_lol[list_index]}",
                # ) # TODO: comment_out testing
                isomorphic_proposals_lol[list_index] = None
                # TODO: when make this function return a flat list, do representative_info_list[list_index] = None in addition to setting isomorphic_proposals_lol[list_index] = None
                # NOTE: should NOT break out of loop early here, b/c even though this proposal is guaranteed to not be isomorphic to any of the other proposals in any isomorphic proposals list, it could still eliminate more future isomorphic proposals lists from the LOL, and if you broke out of this loop right now, those future isomorphic proposals lists that should have been eliminated will not be eliminated.
            # otherwise, this proposal is not isomorphic to this list, but also not strictly more or less useful, so need to keep looking.
        else:
            # Found a new group of isomorphic queries
            isomorphic_proposals_lol.append([proposal])
            representative_info_list.append(small_partition_set)

    isomorphic_proposals_lol = [lst for lst in isomorphic_proposals_lol if (lst is not None)]
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

def _get_small_partition(cwa_set_1, cwa_set_2):
    """
    Given the cwa_sets of integers representing which cwas would be remaining for the 2 outcomes of a query (in either order), return a set of integers representing the small partition corresponding to this query.
    Note that since cwa_set_1 and cwa_set_2 are frozensets, this returns a frozenset.
    TODO: Consider returning sorted tuples as the small partition, rather than frozensets.
    """
    s1_len = len(cwa_set_1)
    s2_len = len(cwa_set_2)
    if(s1_len == s2_len):
        # TODO: consider if there are any less expensive ways (than taking min()) of disambiguating
        # b/t equally-sized cwa sets to be the 'small' partition
        return(cwa_set_1 if(min(cwa_set_1) < min(cwa_set_2)) else cwa_set_2)
    return(cwa_set_1 if(s1_len < s2_len) else cwa_set_2)

def _get_updated_qs_dict_and_pset_dict(qs_dict: dict, current_cwa_set):
    """
    Returns
    -------
    (updated_qs_dict, small_partition_set_dict) : tuple
    `updated_qs_dict` : dict
        A new qs_dict that has useless queries removed and where each q_info contains the minimum possible amount of cwas.
    `small_partition_set_dict` : dict
        A dictionary from {proposal to small partition set}
    """
    new_qs_dict = dict()
    small_partition_set_dict = dict() # dict from proposal : small_partition_set
    for (proposal, inner_dict) in qs_dict.items():
        have_put_proposal_into_new_dict = False
        for (v_index, q_info) in inner_dict.items():
            (q_info_true, q_info_false) =  q_info
            # put the game state's frozenset first to keep result a frozenset.
            cwa_set_true = current_cwa_set & q_info_true
            if(0 < len(cwa_set_true) < len(current_cwa_set)): # *potentially* useful query
                cwa_set_false = current_cwa_set & q_info_false
                new_q_info = Query_Info(cwa_set_true=cwa_set_true, cwa_set_false=cwa_set_false)
                small_partition = _get_small_partition(cwa_set_true, cwa_set_false)
                if not have_put_proposal_into_new_dict: # proposal's first useful query
                    small_partition_set = set()
                    small_partition_set_dict[proposal] = small_partition_set
                    small_partition_set.add(small_partition)
                    new_inner_dict = {v_index: new_q_info}
                    new_qs_dict[proposal] = new_inner_dict
                    have_put_proposal_into_new_dict = True
                else:
                    previous_small_partition_set_length = len(small_partition_set)
                    small_partition_set.add(small_partition)
                    if(len(small_partition_set) != previous_small_partition_set_length):
                        # due to Python's stupid set API, calling add() on a set returns None
                        # and it does not tell you whether the add operation changed the set or not
                        # so you have to either check if the item was in the set before, wasting time on
                        # doing 2 hashes and set lookups, or check the length of the set twice, wasting time
                        # on 2 len function calls and a compare.
                        # consider answer 2 in the link below and if you can use it here.
                        # https://stackoverflow.com/questions/27427067/how-to-check-if-an-item-was-freshly-added-to-a-set-without-doing-lookup-thus-ca
                        # only add this query if it adds something to this proposal's small_partition set.
                        new_inner_dict[v_index] = new_q_info
    return((new_qs_dict, small_partition_set_dict))

def _get_dict_filtered_of_isomorphic_proposals(base_qs_dict, small_partition_set_dict):
    """ TODO: update docstring. Given a queries dict, returns a NEW queries dict with the isomorphic queries filtered out. """
    isomorphic_proposals_lol = _get_isomorphic_proposals_lol(small_partition_set_dict)
    filtered_qs_dict = _filter_out_isomorphic_proposals(base_qs_dict, isomorphic_proposals_lol)
    return(filtered_qs_dict)

def _flat_list_bools_to_int(list_bools):
    return sum((1 << b_index) for (b_index, b) in enumerate(list_bools) if b)

def _nd_array_to_int(ndarr : np.ndarray):
    """
    Given a nested packed bit `ndarr`, where `ndarr[i]` is a packed bool list for the ith verifier, and all `ndarr[i]` are the same length, return a corresponding integer.
    """
    (num_verifiers, num_unint8_per_verifier) = ndarr.shape
    answer = 0
    for v_index in range(num_verifiers):
        for uint8_index in range(num_unint8_per_verifier):
            answer += int(ndarr[v_index, uint8_index]) << (
                (v_index * num_unint8_per_verifier * 8) + (uint8_index * 8)
            )
    return answer

def _homogenize_bool_lol(bool_lol):
    """
    Given a list of lists of bools, make a new lol where each list within the list is extended to the same length by appending Falses to the shorter lists. Returns a copy of the bool lol.
    """
    bool_lol_copy = copy.deepcopy(bool_lol)
    length_to_extend_to = max([len(l) for l in bool_lol_copy])
    for l in bool_lol_copy:
        for extend_index in range(length_to_extend_to - len(l)):
            l.append(False)
    return(bool_lol_copy)

def _true_false_lists_to_bitset(true_false_list_by_verifier: list[list[bool]], set_type):
    """
    true_false_list_by_verifier[i] is a list corresponding to verifier i. In that list, l[x] is a bool that says whether rule x is the one assigned to verifier i in the combo the whole list corresponds to.
    """
    flat_list_bools = [b for v_list in true_false_list_by_verifier for b in v_list]
    if(set_type == int):
        # NOTE: bit[i] corresponds to the ith rule in the flat list of verifier rules
        return _flat_list_bools_to_int(flat_list_bools)
    if(set_type == np.ndarray):
        # NOTE: bitset[i] corresponds to verifier i here and is a list of uint8.
        homogenized_bool_lol = _homogenize_bool_lol(true_false_list_by_verifier)
        return np.packbits(homogenized_bool_lol, axis=1, bitorder='little')
    raise NotImplementedError(
        f"solver_utils._true_false_lists_to_bitset not implemented for bitsets of type {set_type}."
    )

def _single_cwa_to_bitset(single_full_cwa, possible_rules_by_verifier, n_mode, set_type):
    (c, p) = [single_full_cwa[i] for i in [0, 1]]
    true_false_list_by_verifier = []
    for (v_index, verifier_list) in enumerate(possible_rules_by_verifier):
        rule_in_combo = c[p[v_index]] if n_mode else c[v_index]
        true_false_list_this_v_index = [(r is rule_in_combo) for r in verifier_list]
        true_false_list_by_verifier.append(true_false_list_this_v_index)
    return(_true_false_lists_to_bitset(true_false_list_by_verifier, set_type=set_type))

def _invert_permutation(permutation):
    """
    querying verifier V in original form is equivalent to querying verifier answer[V] in canonical form.
    """
    answer = np.empty(shape=len(permutation), dtype=np.uint8)
    for (index, num) in enumerate(permutation):
        answer[num] = index
    return answer

def _convert_cache_bitset_to_canonical_nparray(cache_bitset: np.ndarray):
    """
    Given a cache_bitset in the form of an np.ndarray, return the canonical form of this cache bitset (creates a new np array) as well as the permutation that transforms moves on the original into moves on the canonical form. Takes `*args` to absorb arguments given to the int version of this.

    Returns
    -------
    (canonical_form, permutation)
        A move on verifier index V of the original is equivalent to a move on verifier index permutation[V] of the canonical form.
        NOTE: this has not been tested. Test by pretty printing.
    """
    permutation = np.lexsort(cache_bitset.T)
    return (cache_bitset[permutation], _invert_permutation(permutation))

def _convert_cache_bitset_to_canonical_int(
        cache_bitset : int,
        shift_amounts,
        int_verifier_bit_mask,
    ):
    """
    TODO: test by displaying.
    """
    bitset_ints_by_verifier_with_indices = [
        ((cache_bitset >> shift_amount) & int_verifier_bit_mask, index)
        for (index, shift_amount) in enumerate(shift_amounts)
    ]
    # console.print(bitset_ints_by_verifier_with_indices)
    bitset_ints_by_verifier_with_indices.sort(key=lambda t: t[0], reverse=True)
    # console.print(bitset_ints_by_verifier_with_indices)
    (bitsets, indices) = zip(*bitset_ints_by_verifier_with_indices)
    result = 0
    for (bitset, shift_amount) in zip(bitsets, shift_amounts):
        result |= (bitset << shift_amount)
    return (result, _invert_permutation(indices))

def _working_cwa_set_to_cache_bitset(working_cwa_set, all_cwa_bitsets : np.ndarray):
    bitsets_to_include = all_cwa_bitsets[list(working_cwa_set)] # bitwise or reduce these ints
    return np.bitwise_or.reduce(bitsets_to_include, axis=0)

def _convert_working_gs_to_cache_gs_standard_int(
        working_gs: Game_State,
        all_cwa_bitsets, # NOTE: will not be necessary once switch working_gs cwa set from ints to np array
    ):
    cache_bitset = _working_cwa_set_to_cache_bitset(working_gs.cwa_set, all_cwa_bitsets)
    cache_game_state = Game_State(
        num_queries_this_round=working_gs.num_queries_this_round,
        proposal_used_this_round=working_gs.proposal_used_this_round,
        cwa_set=cache_bitset
    )
    return cache_game_state

def _convert_working_gs_to_cache_gs_standard_nparray(
        working_gs: Game_State,
        all_cwa_bitsets, # NOTE: eliminate once change working_gs cwa set
    ):
    cache_bitset = Hashable_Numpy_Array(_working_cwa_set_to_cache_bitset(working_gs.cwa_set, all_cwa_bitsets))
    cache_game_state = Game_State(
        num_queries_this_round=working_gs.num_queries_this_round,
        proposal_used_this_round=working_gs.proposal_used_this_round,
        cwa_set=cache_bitset
    )
    return cache_game_state

def _convert_working_gs_to_cache_gs_nightmare_int(
        working_gs: Game_State,
        all_cwa_bitsets, # NOTE: eliminate once change working_gs cwa set
        shift_amounts,
        int_verifier_bit_mask
    ):
    cache_bitset = _working_cwa_set_to_cache_bitset(working_gs.cwa_set, all_cwa_bitsets)
    (cache_bitset_canonical_form, permutation) = _convert_cache_bitset_to_canonical_int(
        cache_bitset,
        shift_amounts,
        int_verifier_bit_mask
    )
    cache_gs = Game_State(
        num_queries_this_round=working_gs.num_queries_this_round,
        proposal_used_this_round=working_gs.proposal_used_this_round,
        cwa_set=cache_bitset_canonical_form
    )
    return (cache_gs, permutation)

def _convert_working_gs_to_cache_gs_nightmare_nparray(
        working_gs: Game_State,
        all_cwa_bitsets, # NOTE: eliminate once change working_gs cwa set
        *args, # for accepting the 2 last arguments given in the int version
    ):
    cache_bitset = _working_cwa_set_to_cache_bitset(working_gs.cwa_set, all_cwa_bitsets)
    (cache_bitset_canonical_form, permutation) = _convert_cache_bitset_to_canonical_nparray(cache_bitset)
    cache_bitset_canonical_form = Hashable_Numpy_Array(cache_bitset_canonical_form)
    cache_gs = Game_State(
        num_queries_this_round=working_gs.num_queries_this_round,
        proposal_used_this_round=working_gs.proposal_used_this_round,
        cwa_set=cache_bitset_canonical_form
    )
    return (cache_gs, permutation)

############################## PUBLIC FUNCTIONS #################################################
def get_cwa_bitsets(full_cwas_list, possible_rules_by_verifier, n_mode, set_type) -> np.ndarray :
    """
    Get the list of bitsets corresponding to the cwas of the problem.

    Parameters
    ----------
    full_cwas_list : list[full_cwas]
        The list of full cwas in the solver object.

    possible_rules_by_verifier : list[list[Rule]]
        a list where list[i] corresponds to verifier i, and verifier_list[i] is the ith rule that is possible for that verifier at the beginning (i.e. out of all rules that are possible for that verifier in this problem).

    n_mode : bool
        Whether this is a nightmare mode problem.

    set_type : type
        The type of the bitsets returned. Currently only int is supported; will add Hashable_Numpy_Array next.

    Returns
    -------
    cwa_bitsets : np.ndarray (each element of cwa_bitsets is a combo. if set_type is int, each combo is a Python integer. if set_type is np.ndarray, each combo is itself an ndarray where each element of the combo is a np.ndarray of uint8 representing a verifier).
        cwa_bitsets[i] is the bitset corresponding to the cwa that is solver.full_cwas_list[i].
    """
    return np.array(
        [_single_cwa_to_bitset(cwa, possible_rules_by_verifier, n_mode, set_type) for cwa in full_cwas_list],
        dtype=(np.uint8 if (set_type == np.ndarray) else object)
    )

def bitset_to_int(bitset):
    """
    Given a bitset, return the integer that corresponds to it. Note that bitset may be of different types. Intended for use only for non-performance-sensitive tasks like displaying.
    """
    if(type(bitset) == int):
        return bitset
    if(type(bitset) == np.ndarray):
        return _nd_array_to_int(bitset)
    raise NotImplementedError(f"bitset_to_int not implemented for bitsets of type {type(bitset)}")

def get_convert_working_to_cache_gs_standard(bitset_type):
    if(bitset_type is int):
        return _convert_working_gs_to_cache_gs_standard_int
    if(bitset_type is np.ndarray):
        return _convert_working_gs_to_cache_gs_standard_nparray
    raise NotImplementedError(
        f"Convert working game state to cache game state not implemented for bitset_type {bitset_type}"
    )

def get_convert_working_to_cache_gs_nightmare(bitset_type):
    if(bitset_type is int):
        return _convert_working_gs_to_cache_gs_nightmare_int
    if(bitset_type is np.ndarray):
        return _convert_working_gs_to_cache_gs_nightmare_nparray
    raise NotImplementedError(
        f"Convert working game state to cache game state not implemented for bitset_type {bitset_type}"
    )

def get_set_r_unique_ids_vs_from_full_cwas(full_cwas, n_mode: bool):
    """
    Given a full_cwas iterable, returns a list, where list[i] contains a set of the unique_ids for all possible rules for verifier i. Note: this is used in display.py for printing useful_qs_dict info, to display what rules are possible for each verifier.
    """
    num_vs = len(full_cwas[0][0])
    possible_rule_ids_by_verifier = [set() for _ in range(num_vs)]
    for cwa in full_cwas:
        (c, p) = (cwa[0], cwa[1])
        for (v_index, rule) in enumerate(c):
            corresponding_set = possible_rule_ids_by_verifier[v_index]
            possible_rule = c[p[v_index]] if(n_mode) else rule
            corresponding_set.add(possible_rule.unique_id)
    return(possible_rule_ids_by_verifier)

def make_full_cwas_list(n_mode: bool, rcs_list: list[list[Rule]]):
    """
    Make a full list of cwas given a boolean of n_mode and the rule cards list.
    NOTE: This does not depend on any property of the problem other than these, so you can use this function to get a full cwas list if the rcs_list contains only a proper subset of rule cards/rules.
    """
    possible_combos_with_answers = _get_possible_rules_combos_with_answers(rcs_list)
    if(n_mode):
        nightmare_possible_combos_with_answers = []
        vs = list(range(len(rcs_list))) # vs = [0, 1, 2, . . . for number of verifiers]
        verifier_permutations = tuple(itertools.permutations(vs))
        for original_cwa in possible_combos_with_answers:
            for v_permutation in verifier_permutations:
                nightmare_possible_combos_with_answers.append(
                    (original_cwa[0], v_permutation, original_cwa[1])
                )
        possible_combos_with_answers = nightmare_possible_combos_with_answers
        # possible_combos_with_answers is now [(full rule combo, full permutation, answer), ...]
    # sort the possible cwas by answer. Will be helpful in calculating one_answer_left when switch to bitsets.
    possible_combos_with_answers.sort(key=lambda t:t[-1])
    return(possible_combos_with_answers)

def make_useful_qs_dict(full_cwas_list, cwa_set, flat_rule_list, n_mode):
    """
    Get the initial queries dictionary that the solver starts with.
    """
    if not full_cwas_list: # only happens on invalid problems.
        return None
    base_qs_dict = _init_base_qs_dict(
        full_cwas_list,
        flat_rule_list,
        n_mode
    )
    useful_qs_dict = full_filter(base_qs_dict, cwa_set)
    return(useful_qs_dict)

def full_filter(qs_dict: dict, current_cwa_set):
    """
    Given the current cwa_set for a game state and the qs dict, return a *new* qs_dict that is completely updated: all useless/isomorphic queries are filtered out.
    """
    (updated_qs_dict, small_partition_set_dict) = _get_updated_qs_dict_and_pset_dict(qs_dict, current_cwa_set)
    new_qs_dict = _get_dict_filtered_of_isomorphic_proposals(updated_qs_dict, small_partition_set_dict)
    return(new_qs_dict)

def get_num_queries_in_qs_dict(qs_dict: dict):
    """
    Return the number of queries contained in a qs dict. For debugging/information displaying purposes.
    """
    return(sum([len(inner_dict) for inner_dict in qs_dict.values()]))

# NOTE: all calculate_*_cost functions need to take the same 3 parameters, regardless of whether they use them
def calculate_expected_cost(move_cost, probs, gss_costs):
    (mcost_rounds, mcost_queries) = move_cost
    (p_false, p_true) = probs
    ((gs_false_round_cost, gs_false_query_cost), (gs_true_round_cost, gs_true_query_cost)) = gss_costs
    expected_r_cost = mcost_rounds + (p_false * gs_false_round_cost) + (p_true * gs_true_round_cost)
    expected_q_cost = mcost_queries + (p_false * gs_false_query_cost) + (p_true * gs_true_query_cost)
    return((expected_r_cost, expected_q_cost))
def calculate_worst_case_cost(move_cost, probs, gss_costs):
    bigger_cost_tup = max(gss_costs)
    # WARN: don't use the add_tups function from definitions.py here, b/c this is very time-sensitive and Python is very slow. On problem f5x, using add_tups here single-handedly causes it to take 94 seconds instead of 80.
    # tie_breaker = calculate_expected_cost(mcost, probs, gss_costs)
    # return((bigger_cost_tup[0] + mcost[0], bigger_cost_tup[1] + 1, tie_breaker))
    # Using a tiebreaker to differentiate b/t nodes with the same worst case costs is pretty interesting, but rather expensive, as it adds +10% total time.
    return((bigger_cost_tup[0] + move_cost[0], bigger_cost_tup[1] + 1))
