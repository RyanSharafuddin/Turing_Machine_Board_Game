"""
Gets problems from turingmachine.info.

get_web_problem_from_id: gets a problem from the web with given ID.

get_web_problem_from_mode_difficulty_num_vs : get a web problem with given params.
"""
# See https://www.scrapingbee.com/curl-converter/python/
import requests, json, random
from rich.text import Text
# My imports
from src.core.definitions import Problem, console, EXTREME
import src.core.display as display
from src.core.problems import pre_process_p_id
import src.core.config as config

def _get_response_by_problem_id(p_id: str):
    """ Given a problem ID, get the raw response for the problem with that ID from turingmachine.info """
    cookies = {
        'user': 'bd3b4132-f193-4748-8c2c-942dbd802ceb',
        'histData': '%5B%22A52%20F7E%201%20%22%2C%22F43%205FE%20%22%2C%22B52%20CY9%205%20%22%2C%22F43%20_5F%20E%20%22%2C%22F43%20%22%2C%22C4A%202GW%20%22%2C%22C65%20CN4%20V%20%22%2C%22I4B%20YJK%20%22%2C%22F43%205FE%20.%20%22%2C%22I44%204M2%20%22%2C%22I44%20NDW%20%22%2C%22I45%20ZJR%20%22%2C%22I42%20M3I%20%22%2C%22A43%20Y6L%20%22%2C%22B52%20NYS%20M%20%22%2C%22F52%20LUJ%20G%20%22%2C%22F5X%20TDF%20%22%2C%22F63%20EZQ%20M%20%22%2C%22E63%20YF4%20H%20%22%2C%22B52%20JXQ%20J%20%22%2C%22C5H%20CBJ%20%22%2C%22C46%2043N%20%22%2C%22B63%20YRW%204%20%22%2C%22A43%20031%20%22%2C%22C63%200YV%20B%20%22%2C%22C65%20EEW%20I%20%22%2C%22B52%20MWX%205%20%22%5D',
    }

    headers = {
        'Accept': '*/*',
        'Accept-Language': 'en-US,en;q=0.9',
        'Connection': 'keep-alive',
        'Referer': 'https://turingmachine.info/',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-origin',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36',
        'sec-ch-ua': '"Not)A;Brand";v="8", "Chromium";v="138", "Google Chrome";v="138"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"macOS"',
        # Requests sorts cookies= alphabetically
        # 'Cookie': 'user=bd3b4132-f193-4748-8c2c-942dbd802ceb; histData=%5B%22A52%20F7E%201%20%22%2C%22F43%205FE%20%22%2C%22B52%20CY9%205%20%22%2C%22F43%20_5F%20E%20%22%2C%22F43%20%22%2C%22C4A%202GW%20%22%2C%22C65%20CN4%20V%20%22%2C%22I4B%20YJK%20%22%2C%22F43%205FE%20.%20%22%2C%22I44%204M2%20%22%2C%22I44%20NDW%20%22%2C%22I45%20ZJR%20%22%2C%22I42%20M3I%20%22%2C%22A43%20Y6L%20%22%2C%22B52%20NYS%20M%20%22%2C%22F52%20LUJ%20G%20%22%2C%22F5X%20TDF%20%22%2C%22F63%20EZQ%20M%20%22%2C%22E63%20YF4%20H%20%22%2C%22B52%20JXQ%20J%20%22%2C%22C5H%20CBJ%20%22%2C%22C46%2043N%20%22%2C%22B63%20YRW%204%20%22%2C%22A43%20031%20%22%2C%22C63%200YV%20B%20%22%2C%22C65%20EEW%20I%20%22%2C%22B52%20MWX%205%20%22%5D',
    }

    params = {
        'uuid': 'bd3b4132-f193-4748-8c2c-942dbd802ceb',
        'h': p_id,
    }

    try:
        response = requests.get('https://turingmachine.info/api/api.php', params=params, cookies=cookies, headers=headers)
        response_data = json.loads(response.text)
    except Exception:
        console.print(f"There was an error getting or decoding a response for problem ID: {p_id}.")
        console.print("Printing response.")
        console.print(response)
        response_data = json.loads("{}")
    return(response_data)
def _get_response_by_mode_difficulty_num_vs(mode: int, difficulty: int, num_verifiers: int):
    """
    Get the raw response for an arbitrary problem from turingmachine.info with the given mode, difficulty, and number of verifiers.

    mode = 0, 1, or 2 for standard, extreme, nightmare.

    difficulty is 0, 1, or 2.

    num_verifiers is 4, 5, or 6.
    """
    cookies = {
        'user': 'bd3b4132-f193-4748-8c2c-942dbd802ceb',
        'histData': '%5B%22A52%20IL6%20C%20%22%2C%22A48%20CVO%20%22%2C%22E52%20N24%207%20%22%2C%22H65%20H5D%20B%20%22%2C%22H43%20YG5%20%22%2C%22I52%20GAY%20Z%20%22%2C%22C63%20O6S%202%20%22%2C%22I63%20FKS%20E%20%22%2C%22C63%200YV%20B%20%22%2C%22F52%20LUJ%20G%20%22%2C%22B52%20E83%20H%20%22%2C%22B51%20E3M%20M%20%22%2C%22B52%20D2C%20N%20%22%2C%22F43%205FE%20%22%2C%22A52%20F7E%201%20%22%2C%22B52%20CY9%205%20%22%2C%22F43%20_5F%20E%20%22%2C%22F43%20%22%2C%22C4A%202GW%20%22%2C%22C65%20CN4%20V%20%22%2C%22I4B%20YJK%20%22%2C%22F43%205FE%20.%20%22%2C%22I44%204M2%20%22%2C%22I44%20NDW%20%22%2C%22I45%20ZJR%20%22%2C%22I42%20M3I%20%22%2C%22A43%20Y6L%20%22%2C%22B52%20NYS%20M%20%22%2C%22F5X%20TDF%20%22%2C%22F63%20EZQ%20M%20%22%2C%22E63%20YF4%20H%20%22%2C%22B52%20JXQ%20J%20%22%2C%22C5H%20CBJ%20%22%2C%22C46%2043N%20%22%2C%22B63%20YRW%204%20%22%2C%22A43%20031%20%22%2C%22C65%20EEW%20I%20%22%2C%22B52%20MWX%205%20%22%5D',
    }

    headers = {
        'Accept': '*/*',
        'Accept-Language': 'en-US,en;q=0.9',
        'Connection': 'keep-alive',
        'Referer': 'https://turingmachine.info/',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-origin',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36',
        'sec-ch-ua': '"Not)A;Brand";v="8", "Chromium";v="138", "Google Chrome";v="138"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"macOS"',
        # Requests sorts cookies= alphabetically
        # 'Cookie': 'user=bd3b4132-f193-4748-8c2c-942dbd802ceb; histData=%5B%22A52%20IL6%20C%20%22%2C%22A48%20CVO%20%22%2C%22E52%20N24%207%20%22%2C%22H65%20H5D%20B%20%22%2C%22H43%20YG5%20%22%2C%22I52%20GAY%20Z%20%22%2C%22C63%20O6S%202%20%22%2C%22I63%20FKS%20E%20%22%2C%22C63%200YV%20B%20%22%2C%22F52%20LUJ%20G%20%22%2C%22B52%20E83%20H%20%22%2C%22B51%20E3M%20M%20%22%2C%22B52%20D2C%20N%20%22%2C%22F43%205FE%20%22%2C%22A52%20F7E%201%20%22%2C%22B52%20CY9%205%20%22%2C%22F43%20_5F%20E%20%22%2C%22F43%20%22%2C%22C4A%202GW%20%22%2C%22C65%20CN4%20V%20%22%2C%22I4B%20YJK%20%22%2C%22F43%205FE%20.%20%22%2C%22I44%204M2%20%22%2C%22I44%20NDW%20%22%2C%22I45%20ZJR%20%22%2C%22I42%20M3I%20%22%2C%22A43%20Y6L%20%22%2C%22B52%20NYS%20M%20%22%2C%22F5X%20TDF%20%22%2C%22F63%20EZQ%20M%20%22%2C%22E63%20YF4%20H%20%22%2C%22B52%20JXQ%20J%20%22%2C%22C5H%20CBJ%20%22%2C%22C46%2043N%20%22%2C%22B63%20YRW%204%20%22%2C%22A43%20031%20%22%2C%22C65%20EEW%20I%20%22%2C%22B52%20MWX%205%20%22%5D',
    }

    params = {
        'uuid': 'bd3b4132-f193-4748-8c2c-942dbd802ceb',
        'm': str(mode),
        'd': str(difficulty),
        'n': str(num_verifiers),
    }
    try:
        response = requests.get('https://turingmachine.info/api/api.php', params=params, cookies=cookies, headers=headers)
        response_data = json.loads(response.text)
    except Exception:
        problem_args_str = f"mode: {mode}, difficulty: {difficulty}, num_verifiers: {num_verifiers}"
        console.print(
            f"There was an error getting or decoding a response for problem with arguments\n:{problem_args_str}."
        )
        console.print("Printing response.")
        console.print(response)
        response_data = json.loads("{}")
    return response_data
def _get_required_field_from_response(response, field):
    """
    A convenience function for getting a *required* field from a response object.
    If the field isn't present, prints the name of the missing field, prints the response object, and returns None.
    """
    try:
        required_field = response[field]
    except KeyError:
        console.print(
            f"[b red]Error[/b red]: received a response that does not contain the required field:", end=""
        )
        console.print(f" [b hot_pink]{field}[/b hot_pink].")
        console.print("Printing response: ")
        console.print(response)
        required_field = None
    return required_field
def _get_rc_nums_from_raw_response(raw_response) -> list[int]:
    """
    Given a response from a _get_response* function, return the rule card numbers list associated with that response, or None if the response failed.
    """
    extreme_cards = raw_response.get("fake") # only extreme problems seem to have this field.
    regular_cards = _get_required_field_from_response(raw_response, "ind")
    if(regular_cards is None):
        return None
    regular_cards = [int(rc_num) for rc_num in regular_cards]
    if(extreme_cards is None):
        return(regular_cards)
    extreme_cards = [int(rc_num) for rc_num in extreme_cards]
    rc_nums = []
    for (primary, secondary) in zip(regular_cards, extreme_cards):
        rc_nums.append(primary)
        rc_nums.append(secondary)
    return(rc_nums)
def _error_if_no_match(actual, expected, attribute_name):
    """
    Given an actual object, an expected object, and the name of the object, if the expected object is not None and the objects don't match up, prints an error message.
    """
    if((expected is not None) and (actual != expected)):
        console.print(f"[b red]Warn[/b red]: for {attribute_name}, expected {expected}, but got {actual}.")
def _get_problem_from_raw_response(
        raw_response,
        expected_id = None,
        expected_mode = None,
        expected_difficulty = None,
        expected_num_vs = None,
    ) -> Problem :
    """
    Given a response from a _get_response* function, return the Problem associated with that response, or None if the response failed. If any expected_* kwargs are included, compare that attribute of the received probem to the expected attribute and print an error message if they don't match up.
    """
    problem_id = _get_required_field_from_response(raw_response, "hash")
    problem_id = pre_process_p_id(problem_id)
    rc_nums = _get_rc_nums_from_raw_response(raw_response)
    mode = _get_required_field_from_response(raw_response, "m")
    if(None in [problem_id, rc_nums, mode]):
        return None
    mode = int(mode)
    num_verifiers = (len(rc_nums) / 2) if(mode == EXTREME) else len(rc_nums) # 2 rcs/verifier in extreme mode
    difficulty = _get_required_field_from_response(raw_response, "d")
    difficulty = None if (difficulty is None) else int(difficulty)
    _error_if_no_match(problem_id, expected_id, "problem ID")
    _error_if_no_match(mode, expected_mode, "mode")
    _error_if_no_match(difficulty, expected_difficulty, "difficulty")
    _error_if_no_match(num_verifiers, expected_num_vs, "number of verifiers")
    return(Problem(identity=problem_id, rc_nums_list=rc_nums, mode=mode))
def _randomize_if_none(value, num_values, start=0):
    """
    If value is not None, return it, otherwise get a random value in the range [start, start+num_values).
    """
    if(value is not None):
        return value
    return random.randrange(start, start + num_values)

def get_web_problem_from_id(p_id: str, print_action=False):
    """
    Given a problem ID, return the problem from the web with that ID.
    Return None if there was a problem getting the problem.
    If print_action is True, print out a message showing that it is retrieving a problem with given ID from the web.
    Note: The problem ids are in fact just hashes, so they're not unique. i.e. different hashes could lead to the same associated problem.
    """
    p_id = pre_process_p_id(p_id)
    if(print_action):
        text = Text.assemble(
            ("Getting problem "),
            (f"{p_id} ", config.PROBLEM_TITLE_COLOR),
            "from ",
            ("turingmachine.info", "link https://turingmachine.info/"),
            ".",
        )
        console.print(text, justify="center")
    response = _get_response_by_problem_id(p_id)
    return(_get_problem_from_raw_response(response, expected_id=p_id))
def get_web_problem_from_mode_difficulty_num_vs(mode, difficulty, num_verifiers, print_action=False):
    """
    Get a problem from the web with given mode, difficulty, and num_verifiers. If print_action is True, display a message showing that it is getting a problem with those parameters from the web. Return None if there was a problem getting the problem.

    Note: if any of the parameters are None, choose a value for that parameter 'randomly'.
    mode is an integer from 0 to 2 inclusive.
    difficulty is an integer from 0 to 2 inclusive.
    num_verifiers is an integer from 4 - 6 inclusive.
    """
    mode = _randomize_if_none(mode, 3)
    difficulty = _randomize_if_none(difficulty, 3)
    num_verifiers = _randomize_if_none(num_verifiers, 3, 4)
    if(print_action):
        text = Text.assemble(
            f"Getting a ",
            (f"{display.MODE_NAMES[mode].lower()}", "#FF5FD7"),
            " mode problem with ",
            (f"{num_verifiers}", "#00D7FF"),
            " verifiers and difficulty level ",
            (f"{difficulty}", "#0000FF"),
            " from ",
            ("turingmachine.info", "link https://turingmachine.info/"),
            "."
        )
        console.print(text, justify="center")
    return(
        _get_problem_from_raw_response(
            _get_response_by_mode_difficulty_num_vs(mode, difficulty, num_verifiers),
            expected_mode=mode,
            expected_difficulty=difficulty,
            expected_num_vs=num_verifiers,
        )
    )
