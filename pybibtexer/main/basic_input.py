import json
import os
from typing import Any, Dict


class BasicInput(object):
    """Basic input.

    Args:
        full_json_c (str): The conference json file
        full_json_j (str): The journal json file
        options (Dict[str, Any]): Options.

    Attributes:
        full_abbr_article_dict (Dict[str, str]): Full abbr article dict.
        full_abbr_inproceedings_dict (Dict[str, str]): Full abbr inproceedings dict.
        full_names_in_json (str): Full names in json.
        abbr_names_in_json (str): Abbr names in json.

        options (Dict[str, Any]): Options.

    """

    def __init__(self, options: Dict[str, Any]) -> None:
        # Load default conferences and journals abbreviations from built-in templates
        default_abbr_dict_c, default_abbr_dict_j = self._process_default_conferences_journals_json()

        # Load user-defined conferences and journals abbreviations from provided JSON files
        user_abbr_dict_c, user_abbr_dict_j = self._process_user_conferences_journals_json(options)

        # Merge dictionaries: user abbreviations override default ones for the same keys
        options["full_abbr_article_dict"] = {**default_abbr_dict_j, **user_abbr_dict_j}
        options["full_abbr_inproceedings_dict"] = {**default_abbr_dict_c, **user_abbr_dict_c}

        # Set JSON field names for full and abbreviated names
        options["full_names_in_json"] = "names_full"
        options["abbr_names_in_json"] = "names_abbr"

        self.options = options

    @staticmethod
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

    def _process_default_conferences_journals_json(self):
        """Process default conferences and journals JSON files from built-in templates.

        Notes:
            The structure of full_json_c follows the format
                {"abbr": {"names_abbr": [], "names_full": []}},
            while full_json_j adheres to the format
                {"abbr": {"names_abbr": [], "names_full": []}}.
        """
        # Get current directory and construct path to templates
        current_dir = os.path.dirname(os.path.abspath(__file__))
        path_templates = os.path.join(os.path.dirname(current_dir), "data", "templates")

        # Load conferences abbreviations dictionary
        full_json_c = os.path.join(path_templates, "abbr_full", "conferences.json")
        full_abbr_inproceedings_dict = self.load_json_dict(full_json_c)

        # Load journals abbreviations dictionary
        full_json_j = os.path.join(path_templates, "abbr_full", "journals.json")
        full_abbr_article_dict = self.load_json_dict(full_json_j)

        return full_abbr_inproceedings_dict, full_abbr_article_dict

    def _process_user_conferences_journals_json(self, options: dict):
        """Process user-defined conferences and journals JSON files.

        Notes:
            The structure of full_json_c follows the format
                {"publisher": {"conferences": {"abbr": {"names_abbr": [], "names_full": []}}}},
            while full_json_j adheres to the format
                {"publisher": {"journals": {"abbr": {"names_abbr": [], "names_full": []}}}}.
        """
        # Process user conferences JSON file
        json_dict = self.load_json_dict(options.get("full_json_c", ""))
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
        json_dict = self.load_json_dict(options.get("full_json_j", ""))
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
