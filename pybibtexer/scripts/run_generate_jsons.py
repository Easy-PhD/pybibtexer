import os

from ..main.utils import (
    CheckAcronymAbbrAndFullDict,
    parse_bibtex_file,
    process_user_conferences_journals_json,
)
from ..utils.utils import load_json_file, save_to_json


def run_generate_jsons(
    default_full_json_c: str,
    default_full_json_j: str,
    full_biblatex: str,
    user_full_json_c: str,
    user_full_json_j: str,
    merge_json: bool = False,
) -> None:
    """Execute the JSON generation process for conferences and journals.

    Args:
        default_full_json_c: Path to the default conferences JSON file.
        default_full_json_j: Path to the default journals JSON file.
        full_biblatex: Path to the BibLaTeX source file.
        user_full_json_c: Path to the user conferences JSON file.
        user_full_json_j: Path to the user journals JSON file.
        merge_json: Whether to merge and save JSON data. Defaults to False.

    Returns:
        None
    """
    default_full_json_c = os.path.expandvars(os.path.expanduser(default_full_json_c))
    default_full_json_j = os.path.expandvars(os.path.expanduser(default_full_json_j))
    full_biblatex = os.path.expandvars(os.path.expanduser(full_biblatex))
    user_full_json_c = os.path.expandvars(os.path.expanduser(user_full_json_c))
    user_full_json_j = os.path.expandvars(os.path.expanduser(user_full_json_j))

    check = CheckAcronymAbbrAndFullDict()

    # ==================== Conference Data Processing ====================
    json_old_c = load_json_file(default_full_json_c)
    json_new_c = parse_bibtex_file(full_biblatex, "inproceedings")

    print("\n" + "*" * 9 + f" Checking existing conference data: `{default_full_json_c}` " + "*" * 9)
    json_old_c, _ = check.length_dupicate_match(json_old_c)

    print("\n" + "*" * 9 + f" Checking newly parsed conference data: `{full_biblatex}` " + "*" * 9)
    json_new_c, _ = check.length_dupicate_match(json_new_c)

    print("\n" + "*" * 9 + " Comparing existing conference data with newly parsed conference data " + "*" * 9)
    json_new_c = check.compare_and_return_only_in_new(json_old_c, json_new_c)

    # ==================== Journal Data Processing ====================
    json_old_j = load_json_file(default_full_json_j)
    json_new_j = parse_bibtex_file(full_biblatex, "article")

    print("\n" + "*" * 9 + f" Checking existing journal data: `{default_full_json_j}` " + "*" * 9)
    json_old_j, _ = check.length_dupicate_match(json_old_j)

    print("\n" + "*" * 9 + f" Checking newly parsed journal data: `{full_biblatex}` " + "*" * 9)
    json_new_j, _ = check.length_dupicate_match(json_new_j)

    print("\n" + "*" * 9 + " Comparing existing journal data with newly parsed journal data " + "*" * 9)
    json_new_j = check.compare_and_return_only_in_new(json_old_j, json_new_j)

    # ==================== User Data Integration ====================
    # Process user-specific conference and journal JSON files
    json_user_c, json_user_j = process_user_conferences_journals_json(user_full_json_c, user_full_json_j)

    # Check for duplicates in conferences data
    print("\n" + "*" * 9 + " Checking duplicates in conferences " + "*" * 9)
    c = {**json_new_c, **json_old_c, **json_user_c}  # Priority: user > old > new
    c, c_matches = check.length_dupicate_match(c)
    json_new_c = {k: v for k, v in json_new_c.items() if k not in c_matches}
    c = {**json_new_c, **json_old_c, **json_user_c}  # Priority: user > old > new

    # Check for duplicates in journals data
    print("\n" + "*" * 9 + " Checking duplicates in journals " + "*" * 9)
    j = {**json_new_j, **json_old_j, **json_user_j}  # Priority: user > old > new
    j, f_matches = check.length_dupicate_match(j)
    json_new_j = {k: v for k, v in json_new_j.items() if k not in f_matches}
    j = {**json_new_j, **json_old_j, **json_user_j}  # Priority: user > old > new

    # ==================== Data Merging and Saving ====================
    if merge_json:
        save_to_json(c, default_full_json_c)
        save_to_json(j, default_full_json_j)
        print("Data merging completed and saved")

    return None
