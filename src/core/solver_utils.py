import math, itertools, copy
import numpy as np
from rich import progress
from .definitions import Query_Info, all_125_possibilities_set, Rule, Game_State, console
from .config import REL_TOL, A_TOL
from .data_structures.hashable_numpy_array import Hashable_Numpy_Array

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

def _convert_cache_bitset_to_canonical_nparray(cache_bitset: np.ndarray) -> np.ndarray :
    """
    Given a cache_bitset in the form of an np.ndarray, return the canonical form of this cache bitset (creates a new np array). NOTE: when the cache_bitsets are ints, the 'canonical form' is the one that leads to the smallest bitset int, in contrast to when the cache_bitsets are np arrays, in which case the canonical form is the one that leads to the largest np int. This does not affect the rest of the program, because only one canonical form function is used within a run of the program.

    Returns
    -------
    canonical_form: np.ndarray
        A move on verifier index V of the original is equivalent to a move on verifier index permutation[V] of the canonical form.
    """
    permutation = np.lexsort(cache_bitset.T)
    return cache_bitset[permutation]

def _convert_cache_bitset_to_canonical_int(
        cache_bitset : int,
        shift_amounts,
        int_verifier_bit_mask,
    ) -> int:
    """
    Given a cache_bitset in the form of an int, return the canonical form of this cache bitset. NOTE: when the cache_bitsets are np arrays, the 'canonical form' is the one that leads to the largest bitset int, in contrast to when the cache_bitsets are ints, in which case the canonical form is the one that leads to the smallest np int. This does not affect the rest of the program, because only one canonical form function is used within a run of the program.

    Returns
    -------
    canonical_form: int
        A move on verifier index V of the original is equivalent to a move on verifier index permutation[V] of the canonical form.
    """
    bitset_ints_by_verifier = [
        ((cache_bitset >> shift_amount) & int_verifier_bit_mask)
        for shift_amount in shift_amounts
    ]
    bitset_ints_by_verifier.sort(reverse=True)
    result = 0
    for (bitset, shift_amount) in zip(bitset_ints_by_verifier, shift_amounts):
        result |= (bitset << shift_amount)
    return result

def _working_cwa_set_to_cache_bitset(
        working_cwa_set,
        all_cwa_bitsets : np.ndarray,
    ):
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

def _do_not_convert_gs(working_gs, *other_args):
    return working_gs

def _convert_working_gs_to_cache_gs_nightmare_int(
        nightmare_solver, # this is of type Solver_Nightmare, but don't import it here b/c would have to restructure a lot of things.
        working_gs: Game_State,
        working_cwa_set_convert_cache : dict,
    ) -> Game_State :
    cache_bitset_canonical_form = working_cwa_set_convert_cache.get(working_gs.cwa_set)
    if cache_bitset_canonical_form is None:
        cache_bitset = _working_cwa_set_to_cache_bitset(
            working_gs.cwa_set,
            nightmare_solver.all_cwa_bitsets,
        )
        cache_bitset_canonical_form = _convert_cache_bitset_to_canonical_int(
            cache_bitset,
            nightmare_solver.shift_amounts,
            nightmare_solver.int_verifier_bit_mask
        )
        working_cwa_set_convert_cache[working_gs.cwa_set] = cache_bitset_canonical_form
    cache_gs = Game_State(
        num_queries_this_round=working_gs.num_queries_this_round,
        proposal_used_this_round=working_gs.proposal_used_this_round,
        cwa_set=cache_bitset_canonical_form
    )
    return cache_gs

def _convert_working_gs_to_cache_gs_nightmare_nparray(
        nightmare_solver, # this is of type Solver_Nightmare, but don't import it here b/c would have to restructure a lot of things.
        working_gs: Game_State,
        working_cwa_set_convert_cache : dict,
    ) -> Game_State:
    cache_bitset_canonical_form = working_cwa_set_convert_cache.get(working_gs.cwa_set)
    if cache_bitset_canonical_form is None:
        cache_bitset = _working_cwa_set_to_cache_bitset(
            working_gs.cwa_set,
            nightmare_solver.all_cwa_bitsets,
        )
        cache_bitset_canonical_form_raw = _convert_cache_bitset_to_canonical_nparray(cache_bitset)
        cache_bitset_canonical_form = Hashable_Numpy_Array(cache_bitset_canonical_form_raw)
        working_cwa_set_convert_cache[working_gs.cwa_set] = cache_bitset_canonical_form
    cache_gs = Game_State(
        num_queries_this_round=working_gs.num_queries_this_round,
        proposal_used_this_round=working_gs.proposal_used_this_round,
        cwa_set=cache_bitset_canonical_form
    )
    return cache_gs

def _python_index(seq, item):
    return seq.index(item)

def _numpy_index(nparray, item):
    return np.argwhere(nparray == item)[0, 0]

############################## PUBLIC FUNCTIONS #################################################
def get_cwa_bitsets(solver) -> np.ndarray :
    """
    Get the list of bitsets corresponding to the cwas of the problem, or None if `set_type` is set.

    Parameters
    ----------
    full_cwas_list : list[full_cwas]
        The list of full cwas in the solver object.

    possible_rules_by_verifier : list[list[Rule]]
        a list where list[i] corresponds to verifier i, and verifier_list[i] is the ith rule that is possible for that verifier at the beginning (i.e. out of all rules that are possible for that verifier in this problem).

    n_mode : bool
        Whether this is a nightmare mode problem.

    set_type : type
        The type of the bitsets returned. If this is set, will return None, b/c then will use Python sets of int indexes, rather than bitsets.

    Returns
    -------
    cwa_bitsets : np.ndarray (each element of cwa_bitsets is a combo. if set_type is int, each combo is a Python integer. if set_type is np.ndarray, each combo is itself an ndarray where each element of the combo is a np.ndarray of uint8 representing a verifier).
        cwa_bitsets[i] is the bitset corresponding to the cwa that is solver.full_cwas_list[i].
    """
    if (solver.bitset_type is set):
        return None
    return np.array(
        [
            _single_cwa_to_bitset(cwa, solver.possible_rules_by_verifier, solver.n_mode, solver.bitset_type)
            for cwa in solver.full_cwas_list
        ],
        dtype=(np.uint8 if (solver.bitset_type is np.ndarray) else object)
    )

def bitset_to_int(bitset) -> int:
    """
    Given a bitset, return the integer that corresponds to it. Note that bitset may be of different types. Intended for use only for non-performance-sensitive tasks like displaying. Raises NotImplementedError if it receives an unexpected type of bitset (this is a critical part of this function's contract).
    """
    if(type(bitset) is int):
        return bitset
    if(type(bitset) is np.ndarray):
        return _nd_array_to_int(bitset)
    if(type(bitset) is Hashable_Numpy_Array):
        return _nd_array_to_int(bitset.nparray)
    raise NotImplementedError(f"bitset_to_int not implemented for bitsets of type {type(bitset)}")

def get_convert_working_to_cache_gs_standard(bitset_type):
    if(bitset_type is int):
        return _convert_working_gs_to_cache_gs_standard_int
    if(bitset_type is np.ndarray):
        return _convert_working_gs_to_cache_gs_standard_nparray
    if(bitset_type is set):
        return _do_not_convert_gs
    raise NotImplementedError(
        f"Convert working game state to cache game state standard not implemented for bitset_type {bitset_type}"
    )

def get_convert_working_to_cache_gs_nightmare(bitset_type):
    if(bitset_type is int):
        return _convert_working_gs_to_cache_gs_nightmare_int
    if(bitset_type is np.ndarray):
        return _convert_working_gs_to_cache_gs_nightmare_nparray
    raise NotImplementedError(
        f"Convert working game state to cache game state nightmare not implemented for bitset_type {bitset_type}"
    )

def get_index_function(bitset_type):
    if bitset_type is int:
        return _python_index
    if bitset_type is np.ndarray:
        return _numpy_index

def get_permutation(nightmare_solver, working_gs: Game_State):
    """ WARN: only use for printing visualizations to aid debugging; not for anything performance related."""
    cache_bitset = _working_cwa_set_to_cache_bitset(
            working_gs.cwa_set,
            nightmare_solver.all_cwa_bitsets,
        )
    if type(cache_bitset) is np.ndarray:
        return np.lexsort(cache_bitset.T)
    if type(cache_bitset) is not int:
        console.print(type(cache_bitset))
        raise Exception(f"O noes! Type of cache_bitset is unexpectedly {type(cache_bitset)}")
    # cache_bitset is of type int
    bitset_ints_by_verifier_with_indexes = [
        (((cache_bitset >> shift_amount) & nightmare_solver.int_verifier_bit_mask), index)
        for (index, shift_amount) in enumerate(nightmare_solver.shift_amounts)
    ]
    bitset_ints_by_verifier_with_indexes.sort(key=lambda t: t[0], reverse=True)
    (bitsets, indexes) = zip(*bitset_ints_by_verifier_with_indexes)
    return indexes

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

def make_useful_qs_dict(solver, gs: Game_State):
    """
    Get the initial queries dictionary that the solver starts with. gs is the state to use for filtering queries initially.
    """
    if not solver.full_cwas_list: # only happens on invalid problems.
        return None
    base_qs_dict = _init_base_qs_dict(
        solver.full_cwas_list,
        solver.flat_rule_list,
        solver.n_mode
    )
    useful_qs_dict = full_filter(base_qs_dict, gs.cwa_set)
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

def progress_initialize():
    p = progress.Progress(
        progress.TextColumn("[progress.description]{task.description}"),
        progress.BarColumn(),
        progress.MofNCompleteColumn(),
        progress.TaskProgressColumn(),
        progress.TimeElapsedColumn(),
        refresh_per_second=1,
        console=console,
    )
    return(p)

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
def calculate_expected_with_depth_cost(move_cost, probs, gss_costs):
    """
    Return a triplet (average round cost, average query cost, worst case round depth).
    """
    (mcost_rounds, mcost_queries) = move_cost
    (p_false, p_true) = probs
    ((gsf_round_cost, gsf_query_cost, gsf_depth), (gst_round_cost, gst_query_cost, gst_depth)) = gss_costs
    expected_r_cost = mcost_rounds + (p_false * gsf_round_cost) + (p_true * gst_round_cost)
    expected_q_cost = mcost_queries + (p_false * gsf_query_cost) + (p_true * gst_query_cost)
    # TODO: is the below line faster than using the max() function?
    worst_depth = mcost_rounds + (gsf_depth if (gsf_depth > gst_depth) else gst_depth)
    return (expected_r_cost, expected_q_cost, worst_depth)

def rqd_to_str(rqd):
    (r, q, d) = rqd
    return f"({r:0.3f}, {q:0.3f}, max_depth: {d:>3})"

def overall_depth_handler(move_rqd_tups:list):
    """
    Returns
    -------
    (a, b, c, d, e)

    a:
        boolean for is min depth counterexample,
    b:
        the min depth move,
    c:
        the depth difference,
    d:
        the difference in average cost
    e:
        min_depth_index
    """
    move_rqd_tups.sort(key = lambda move_rqd_tup: move_rqd_tup[1])
    if not move_rqd_tups:
        return (False, None, None, None, None)
    min_depth_index = min(range(len(move_rqd_tups)), key=lambda i:move_rqd_tups[i][1][2])
    (lcm_rounds, lcm_qs, lcm_depth) = move_rqd_tups[0][1]
    (min_depth_move, (md_rounds, md_qs, md_depth)) = move_rqd_tups[min_depth_index]
    is_counterexample = (
        (lcm_depth > md_depth) and
        roughly_gt_2tup((md_rounds, md_qs), (lcm_rounds, lcm_qs))
    )
    depth_diff = lcm_depth - md_depth
    avg_cost_diff = (md_rounds - lcm_rounds, md_qs - lcm_qs)
    return (is_counterexample, min_depth_move, depth_diff, avg_cost_diff, min_depth_index)

def roughly_geq_2tup(node_cost, corresponding_threshold):
    """
    Returns True if `node_cost` >= `corresponding_threshold`, using floating point tolerance to compare for 'equality'.
    """
    (node_rounds, node_queries) = node_cost
    (threshold_rounds, threshold_queries) = corresponding_threshold
    # NOTE: consider using np.isclose() instead of what currently doing.
    # Alternatively, consider using Python's built in math.isclose(). They are different.
    # See https://numpy.org/doc/stable/reference/generated/numpy.isclose.html to understand how they differ.
    # Also, consider setting REL_TOL to 1e-9 instead of 0.
    rounds_close_py = math.isclose(node_rounds, threshold_rounds, rel_tol=REL_TOL, abs_tol=A_TOL)
    if rounds_close_py:
        queries_close_py = math.isclose(node_queries, threshold_queries, rel_tol=REL_TOL, abs_tol=A_TOL)
        if queries_close_py:
            return True
        return (node_queries > threshold_queries)
    return (node_rounds > threshold_rounds)

def roughly_geq_rqd(node_cost, corresponding_threshold):
    """
    Returns True if `node_cost` >= `corresponding_threshold`, using floating point tolerance to compare for 'equality'.
    """
    (node_rounds, node_queries, node_depth) = node_cost
    (threshold_rounds, threshold_queries, threshold_depth) = corresponding_threshold
    # NOTE: consider using np.isclose() instead of what currently doing.
    # Alternatively, consider using Python's built in math.isclose(). They are different.
    # See https://numpy.org/doc/stable/reference/generated/numpy.isclose.html to understand how they differ.
    # Also, consider setting REL_TOL to 1e-9 instead of 0.
    rounds_close_py = math.isclose(node_rounds, threshold_rounds, rel_tol=REL_TOL, abs_tol=A_TOL)
    if rounds_close_py:
        queries_close_py = math.isclose(node_queries, threshold_queries, rel_tol=REL_TOL, abs_tol=A_TOL)
        if queries_close_py:
            return True
        return (node_queries > threshold_queries)
    return (node_rounds > threshold_rounds)

def roughly_gt_2tup(node_cost, corresponding_threshold):
    """
    Returns True if `node_cost` > `corresponding_threshold`, using floating point tolerance to compare for 'equality'.
    """
    (node_rounds, node_queries) = node_cost
    (threshold_rounds, threshold_queries) = corresponding_threshold
    # NOTE: consider using np.isclose() instead of what currently doing.
    # Alternatively, consider using Python's built in math.isclose(). They are different.
    # See https://numpy.org/doc/stable/reference/generated/numpy.isclose.html to understand how they differ.
    # Also, consider setting REL_TOL to 1e-9 instead of 0.
    rounds_close_py = math.isclose(node_rounds, threshold_rounds, rel_tol=REL_TOL, abs_tol=A_TOL)
    if rounds_close_py:
        queries_close_py = math.isclose(node_queries, threshold_queries, rel_tol=REL_TOL, abs_tol=A_TOL)
        if queries_close_py:
            return False
        return (node_queries > threshold_queries)
    return (node_rounds > threshold_rounds)

def roughly_lt_2tup(node_cost, corresponding_threshold):
    """
    Returns True if `node_cost` < `corresponding_threshold`, using floating point tolerance to compare for 'equality'.
    """
    (node_rounds, node_queries) = node_cost
    (threshold_rounds, threshold_queries) = corresponding_threshold
    # NOTE: consider using np.isclose() instead of what currently doing.
    # Alternatively, consider using Python's built in math.isclose(). They are different.
    # See https://numpy.org/doc/stable/reference/generated/numpy.isclose.html to understand how they differ.
    # Also, consider setting REL_TOL to 1e-9 instead of 0.
    rounds_close_py = math.isclose(node_rounds, threshold_rounds, rel_tol=REL_TOL, abs_tol=A_TOL)
    if rounds_close_py:
        queries_close_py = math.isclose(node_queries, threshold_queries, rel_tol=REL_TOL, abs_tol=A_TOL)
        if queries_close_py:
            return False
        return (node_queries < threshold_queries)
    return (node_rounds < threshold_rounds)

def roughly_lt_rqd(node_cost, corresponding_threshold):
    """
    Returns True if `node_cost` < `corresponding_threshold`, using floating point tolerance to compare for 'equality'.
    """
    (node_rounds, node_queries, node_depth) = node_cost
    (threshold_rounds, threshold_queries, threshold_depth) = corresponding_threshold
    # NOTE: consider using np.isclose() instead of what currently doing.
    # Alternatively, consider using Python's built in math.isclose(). They are different.
    # See https://numpy.org/doc/stable/reference/generated/numpy.isclose.html to understand how they differ.
    # Also, consider setting REL_TOL to 1e-9 instead of 0.
    rounds_close_py = math.isclose(node_rounds, threshold_rounds, rel_tol=REL_TOL, abs_tol=A_TOL)
    if rounds_close_py:
        queries_close_py = math.isclose(node_queries, threshold_queries, rel_tol=REL_TOL, abs_tol=A_TOL)
        if queries_close_py:
            return False
        return (node_queries < threshold_queries)
    return (node_rounds < threshold_rounds)

def fp_lt(a, b):
    """
    Returns True if a is *strictly floating point less* than b. Note that if they are equal or 'close', returns False.
    """
    if math.isclose(a, b, rel_tol=REL_TOL, abs_tol=A_TOL):
        return False
    return (a < b)

def fp_eq(a, b):
    """
    Returns True iff a is 'equal' to b. a and b are single numbers.
    """
    return math.isclose(a, b, rel_tol=REL_TOL, abs_tol=A_TOL)

def fp_eq_tup(a, b):
    """
    Returns True if a is approximately equal to b, where a and b are 2-tuples.

    Params
    ------
    a: tuple [number, number]

    b: tuple [number, number]
    """
    return (
        math.isclose(a[0], b[0], rel_tol=REL_TOL, abs_tol=A_TOL) and
        math.isclose(a[1], b[1], rel_tol=REL_TOL, abs_tol=A_TOL)
    )
    # return np.allclose(a, b, rtol=REL_TOL, atol=A_TOL)

def fp_leq(a, b):
    """
    floating point less than or equal
    """
    if math.isclose(a, b, rel_tol=REL_TOL, abs_tol=A_TOL):
        return True
    return (a < b)

def fp_cmp(a, b):
    """
    Params
    ------
    a: float

    b: float

    Returns
    -------
    (less_than, equal):
        less_than is True if a is 'less than' b

        equal is true if a is 'equal' to b
    """
    if math.isclose(a, b, rel_tol=REL_TOL, abs_tol=A_TOL):
        return (False, True)
    return ((a < b), False)
