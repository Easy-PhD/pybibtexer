
import json
import os


def load_json_dict(file_path):
    """Load and parse JSON file, return empty dict if fails."""
    if os.path.isfile(file_path):
        with open(file_path, "r") as f:
            try:
                return json.loads(f.read())
            except Exception as e:
                print(e)
                return {}
    return {}


def process_user_conferences_journals_json(full_json_c, full_json_j):
    """Process user-defined conferences and journals JSON files.

    Notes:
        The structure of full_json_c follows the format
            {"publisher": {"conferences": {"abbr": {"names_abbr": [], "names_full": []}}}},
        while full_json_j adheres to the format
            {"publisher": {"journals": {"abbr": {"names_abbr": [], "names_full": []}}}}.
    """
    # Process user conferences JSON file
    json_dict = load_json_dict(full_json_c)
    full_abbr_inproceedings_dict = {}

    # Try different possible keys for conferences section in JSON structure
    for flag in ["conferences", "Conferences", "CONFERENCES", "conference", "Conference", "CONFERENCE"]:
        full_abbr_inproceedings_dict = {p: json_dict[p].get(flag, {}) for p in json_dict}
        if full_abbr_inproceedings_dict:
            break

    # Flatten the nested dictionary structure to {abbr: value} format
    # Convert from {publisher: {abbr: data}} to {abbr: data}
    full_abbr_inproceedings_dict = {abbr: v[abbr] for v in full_abbr_inproceedings_dict.values() for abbr in v}
    # Standardize the structure to ensure consistent format
    # Extract only usefull information ("names_full" and "names_abbr")
    full_abbr_inproceedings_dict = {
        k: {"names_full": v.get("names_full", []), "names_abbr": v.get("names_abbr", [])}
        for k, v in full_abbr_inproceedings_dict.items()
    }

    # Process user journals JSON file
    json_dict = load_json_dict(full_json_j)
    full_abbr_article_dict = {}

    # Try different possible keys for journals section in JSON structure
    for flag in ["journals", "Journals", "JOURNALS", "journal", "Journal", "JOURNAL"]:
        full_abbr_article_dict = {p: json_dict[p].get("journals", {}) for p in json_dict}
        if full_abbr_article_dict:
            break

    # Flatten the nested dictionary structure to {abbr: value} format
    # Convert from {publisher: {abbr: data}} to {abbr: data}
    full_abbr_article_dict = {abbr: v[abbr] for v in full_abbr_article_dict.values() for abbr in v}
    # Standardize the structure to ensure consistent format
    # Extract only usefull information ("names_full" and "names_abbr")
    full_abbr_article_dict = {
        k: {"names_full": v.get("names_full", []), "names_abbr": v.get("names_abbr", [])}
        for k, v in full_abbr_article_dict.items()
    }

    # Return both processed dictionaries
    return full_abbr_inproceedings_dict, full_abbr_article_dict
