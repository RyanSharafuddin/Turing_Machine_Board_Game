from pympler.asizeof import asizeof # TODO: delete
from line_profiler import profile
import time
import rules, config, solver_utils
from definitions import *


def fset_answers_from_cwa_iterable(cwa_iterable):
    return(frozenset([cwa[-1] for cwa in cwa_iterable]))
def fset_cwa_indexes_remaining_from_full_cwa(full_cwa):
    fset_cwa_indexes_remaining = frozenset(
            [(tuple([r.card_index for r in cwa[0]]),) + cwa[1:] for cwa in full_cwa]
        )
    return(fset_cwa_indexes_remaining)
def one_answer_left(fset_cwa_indexes):
    """
    Given a set of CWA as stored in the game state object, returns a boolean according to whether or not there is exactly one unique answer remaining in the CWA set. Faster than just making the entire answer set and calling len() on it, b/c instead of going through every CWA, this returns the moment it finds a second answer.
    NOTE: if you change the game_state cwa sets to be implemented using a set of integers, or a list of booleans, or numpy bit pack, or a single long integer, or something else, will need to change the parameters: will need to add full_cwa as a parameter of this function.
    """
    seen_answer_set = set()
    # See comments in definitions.Game_State for the format game_state_cwa_set is in.
    # May not be a literal Python set object.
    iterator = iter(fset_cwa_indexes)
    zeroth_cwa_representation = next(iterator)
    seen_answer_set.add(zeroth_cwa_representation[-1])
    current_cwa_representation = next(iterator, None)

    while(current_cwa_representation is not None):
        if(current_cwa_representation[-1] not in seen_answer_set):
            return(False)
        current_cwa_representation = next(iterator, None)
    return(True)
# TODO: define a length method if switch to another set representation

# useless_queries = 0
# useful_queries = 0
def create_move_info(num_combos_currently, game_state, num_queries_this_round, q_info, move, cost):
    """
    num_queries_this_round is the number there will be after making this move.
    WARN: could be None
    """
    fset_indexes_cwa_remaining_true = \
        game_state.fset_cwa_indexes_remaining & q_info.set_indexes_cwa_remaining_true
    fset_indexes_cwa_remaining_false = \
        game_state.fset_cwa_indexes_remaining &  q_info.set_indexes_cwa_remaining_false
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
        # global useful_queries
        # useful_queries += 1
    else:
        # this is not a useful query. Take move out of the game state frozen set representing remaining moves, if you implement it. Actually, take out all such useless moves before making the next game states. Will require some refactoring.
        move_info = None
        # global useless_queries
        # useless_queries += 1
    return(move_info)

def get_and_apply_moves(game_state : Game_State, qs_dict: dict):
    """
    yields from a list of [(move, cost, (game_state_false, game_state_true), (p_false, p_true))].
    move is a tuple (proposal tuple, rc_index of verifier to query).
    cost is a tuple (round cost, query cost)
    """
    # calling len() to figure out num_combos_currently here so don't have to do it repeatedly inside loop
    num_combos_currently = len(game_state.fset_cwa_indexes_remaining)
    if(game_state.proposal_used_this_round is None):
        # Yield all proposals b/c it's a new round.
        cost = (1, 1)
        next_num_queries = 1
        for (proposal, inner_dict) in qs_dict.items():
            # 2 possibilites:
                # 1 whenever start a new round early, give this function a proposal_already_explored parameter, so it doesn't explore that proposal again.
                # 2 make a new qs_dict every round, so you won't waste time on useless proposals at all. Try 2 first, and only do 1 if 2 does not save you time.
            # if(proposal == game_state.proposal_used_this_round):
                # continue # no sense starting a new round when you could have remained on same round.
            for (verifier_to_query, q_info) in inner_dict.items():
                move = (proposal, verifier_to_query)
                move_info = create_move_info(
                    num_combos_currently,
                    game_state,
                    next_num_queries,
                    q_info,
                    move,
                    cost
                )
                if(move_info is not None):
                    yield(move_info)
                else:
                    pass # not a useful query

    else:
        # There is an existing proposal that you've used in this game state that you can use again without incurring a round cost.
        inner_dict_this_proposal = qs_dict.get(game_state.proposal_used_this_round)
        if(not(inner_dict_this_proposal is None)): # If this proposal still has potentially useful queries
            cost = (0, 1) # considering all queries that don't incur a round cost
            next_num_queries = (game_state.num_queries_this_round + 1) % 3
            for (verifier_to_query, q_info) in inner_dict_this_proposal.items():
                move = (game_state.proposal_used_this_round, verifier_to_query)
                move_info = create_move_info(
                    num_combos_currently,
                    game_state,
                    next_num_queries,
                    q_info,
                    move,
                    cost
                )
                if(move_info is not None):
                    yield(move_info)
                else:
                    # TODO: use line profiling to figure out how many times you're hitting this line (as well as the equivalent line in the block below), and get an estimate of how much time you spend on the set intersection operation in create_move_info on useless queries, and, if it's substantial, consider making a new qs_dict with every call to calculate_best_move that doesn't include known useless queries. But maybe before doing this, replace the set_indexes_cwa in game_states and q_infos with simple ints that are indexes into the solver.full possible combos list (not tuples for index, answer; just ints), and make a function called contains_one_answer(cwa_index_list, full_cwa_list). This way, performing set intersection should take substantially less time, which will better inform you if making new qs_dicts with every calculate_best_move call is worth it.
                    pass # not a useful query. See other comments.

class Solver:
    null_answer = (None, (0,0))
    initial_best_cost = (float('inf'), float('inf'))
    def __init__(self, problem: Problem):
        self.problem            = problem
        self.n_mode             = (problem.mode == NIGHTMARE)
        self.evaluations_cache  = dict()
        self.rcs_list           = rules.make_rcs_list(problem)
        self.num_rcs            = len(self.rcs_list)
        self.flat_rule_list     = rules.make_flat_rule_list(self.rcs_list)
        self.full_cwa           = solver_utils.make_full_cwa(problem, self.rcs_list)
        self.cost_calulator     = solver_utils.calculate_expected_cost # can also be calculate_worst_case_cost
        # self.cost_calulator     = solver_utils.calculate_worst_case_cost # can also be calculate_worst_case_cost
        self.testing_stuff() # WARN TODO: delete
        self.initial_game_state = Game_State(
            0,
            None,
            fset_cwa_indexes_remaining_from_full_cwa(self.full_cwa)
        )
        self.seconds_to_solve   = -1 # have not called solve() yet.
        if(not(self.full_cwa)):
            return

        # self.rc_indexes_cwa_to_full_combos_dict # TODO eliminate (see big optimization)
        self.rc_indexes_cwa_to_full_combos_dict = {
            (tuple([r.card_index for r in cwa[0]]),) + cwa[1:] : cwa for cwa in self.full_cwa
        }

        self.qs_dict        = solver_utils.make_useful_qs_dict(
            all_125_possibilities_set, self.full_cwa, self.flat_rule_list, self.n_mode
        )

    def testing_stuff(self):
        # if(not config.USE_NIGHTMARE_CALCULATE):
        #     self.calculator = self.calculate_best_move
        import display
        global sd
        sd = display.Solver_Displayer(self)
        # sd.print_problem(self.rcs_list, self.problem)
        # exit()

    # called_calculate = 0
    # cache_hits = 0
    # NOTE: don't use the class's qs_dict just yet. Keep passing it down, in case you want to make new ones in the future. See todo.txt.
    @profile
    def calculate_best_move(self, qs_dict, game_state: Game_State):
        """
        Returns a tuple (best move in this state, mov_cost_tup, gs_tup, expected cost to win from game_state (this is a tuple of (expected rounds, expected total queries))).
        best_move_tup is a tup of (proposal, rc_index)
        """
        # self.called_calculate += 1
        if(game_state in self.evaluations_cache):
            # self.cache_hits += 1
            return(self.evaluations_cache[game_state])
        if(one_answer_left(game_state.fset_cwa_indexes_remaining)):
            if(config.CACHE_END_STATES):
                self.evaluations_cache[game_state] = Solver.null_answer
            return(Solver.null_answer)
        best_node_cost = Solver.initial_best_cost
        found_moves = False
        # console.print("Calculating best move on gs:")
        # sd.print_game_state(game_state)
        for move_info in get_and_apply_moves(game_state, qs_dict):
            (move, mcost, gs_tup, p_tup) = move_info
            # console.print(f"Consider move {move}")
            gs_false_node_cost = self.calculate_best_move(qs_dict, gs_tup[0])[1]
            gs_true_node_cost = self.calculate_best_move(qs_dict, gs_tup[1])[1]
            gss_costs = (gs_false_node_cost, gs_true_node_cost)
            node_cost_tup = self.cost_calulator(mcost, p_tup, gss_costs)
            if(node_cost_tup < best_node_cost):
                found_moves = True
                best_node_cost = node_cost_tup
                best_move = move
                if(
                    (node_cost_tup == (0, 1)) or
                    ((node_cost_tup == (1, 1)) and (game_state.proposal_used_this_round is None))
                ):
                    # can solve within 1 query and 0 rounds, or 1 query and all queries cost a round, so return early
                    break
        if(found_moves):
            # uncomment below line for use with worst_case_cost with tiebreaker
            # best_node_cost = (best_node_cost[0], best_node_cost[1])
            answer = (best_move, best_node_cost)
        else:
            new_gs = Game_State(
                num_queries_this_round=0,
                proposal_used_this_round=None,
                fset_cwa_indexes_remaining=game_state.fset_cwa_indexes_remaining
            )
            answer = self.calculate_best_move(qs_dict=qs_dict, game_state=new_gs)

        # comment out else block above and uncomment this to try starting new rounds early as well.
        # if(game_state.num_queries_this_round != 0):
        #     new_gs = Game_State(
        #         num_queries_this_round=0,
        #         proposal_used_this_round=None,
        #         fset_cwa_indexes_remaining=game_state.fset_cwa_indexes_remaining
        #     )
        #     end_round_early_result = self.calculate_best_move(qs_dict=qs_dict, game_state=new_gs)
        #     if(end_round_early_result[1] < best_node_cost):
        #         # breakpoint here to see if there are situations where ending the round early is better.
        #         # can even label the evaluations result with this info, and see if that node makes it into the best move tree.
        #         answer = end_round_early_result

        self.evaluations_cache[game_state] = answer
        return(answer)

    def solve(self):
        """
        Sets up evaluations_cache with the evaluations of all necessary game states.
        """
        start = time.time()
        self.calculate_best_move(qs_dict = self.qs_dict, game_state = self.initial_game_state)
        end = time.time()
        self.seconds_to_solve = int(end - start)
        console.print(
            f"Size of evaluations cache in megabytes: {asizeof(self.evaluations_cache)//(2 ** 20):,}."
        ) # TODO: delete
        # self.print_cache_by_size()
        # console.print(f"{useless_queries:,} useless queries")
        # console.print(f"{useful_queries:,} useful queries")
        # console.print(f"Called calculate: {self.called_calculate:,}.\nCache hits: {self.cache_hits:,}.\nNumber of objects in cache: {len(self.evaluations_cache):,}")

    def get_move_mcost_gs_ncost_from_cache(self, game_state: Game_State, default=None):
        """
        Given a game state, return the best move, the cost of the best move, the resulting (gs_false, gs_true) tuple, and the cost of the game_state, or default if the game state is not in the cache. This function makes it so that solvers can easily change what they put in the evaluations cache for their own purposes, without necessitating changes to controller.py or display.py.
        """
        if not(game_state in self.evaluations_cache):
            return(default)

        (best_move, node_evaluation) = (
            self.evaluations_cache[game_state][0], self.evaluations_cache[game_state][-1]
        )
        best_mcost = ((Solver.does_move_cost_round(best_move, game_state)), 1)
        gs_tuple = self.apply_move_to_state(best_move, game_state)
        constructed_answer = (best_move, best_mcost, gs_tuple, node_evaluation)
        # assert(constructed_answer == self.evaluations_cache[game_state])
        # if not(constructed_answer == self.evaluations_cache[game_state]):
        #     print("O NOES!")
        #     exit()
        return(constructed_answer)

    def apply_move_to_state(self, move, gs: Game_State) -> tuple[Game_State, Game_State]:
        """ WARN: ONLY use this inside the get_move_mcost... fuction. Not for anything else """
        (proposal, v_index) = move
        (q_info_true, q_info_false) = self.qs_dict[proposal][v_index]
        (cwa_set_false, cwa_set_true) = (
            (gs.fset_cwa_indexes_remaining & q_info_false), (gs.fset_cwa_indexes_remaining & q_info_true)
        )
        num_queries_this_round = (1 if Solver.does_move_cost_round(move, gs) else (
                (gs.num_queries_this_round + 1) % 3
            )
        )
        proposal_used_this_round = (None if(num_queries_this_round == 0) else proposal)
        gs_false = Game_State(
            num_queries_this_round=num_queries_this_round,
            proposal_used_this_round=proposal_used_this_round,
            fset_cwa_indexes_remaining=cwa_set_false
        )
        gs_true = Game_State(
            num_queries_this_round=num_queries_this_round,
            proposal_used_this_round=proposal_used_this_round,
            fset_cwa_indexes_remaining=cwa_set_true
        )
        return((gs_false, gs_true))

    @staticmethod
    def does_move_cost_round(move, gs: Game_State):
        proposal = move[0]
        # if num_queries_this_round is 3, then gs.proposal_used.. should be None
        return(gs.proposal_used_this_round != proposal)

    def full_cwa_from_game_state(self, gs):
        return([self.rc_indexes_cwa_to_full_combos_dict[cwa] for cwa in gs.fset_cwa_indexes_remaining])

    # def print_cache_by_size(self):
    #     l = [0] * (len(self.full_cwa) + 1)
    #     for gs in self.evaluations_cache:
    #         l[len(gs.fset_cwa_indexes_remaining)] += 1
    #     for (size, num) in enumerate(l):
    #         console.print(f"{size:>{3},}: {num:>{15},}")