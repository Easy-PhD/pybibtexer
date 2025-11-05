import os
import re
from typing import Any

from .utils import load_json_dict, process_user_conferences_journals_json


class BasicInput:
    """Basic input.

    Args:
        full_json_c (str): The conference json file
        full_json_j (str): The journal json file
        options (dict[str, Any]): Options.

    Attributes:
        full_abbr_article_dict (dict[str, str]): Full abbr article dict.
        full_abbr_inproceedings_dict (dict[str, str]): Full abbr inproceedings dict.
        full_names_in_json (str): Full names in json.
        abbr_names_in_json (str): Abbr names in json.
        abbr_article_pattern_dict (dict): Pre-compiled regex patterns for journal name matching
        abbr_inproceedings_pattern_dict (dict): Pre-compiled regex patterns for conference name matching

        options (dict[str, Any]): Options.

    """

    def __init__(self, options: dict[str, Any]) -> None:
        # Load default conferences and journals abbreviations from built-in templates
        default_abbr_dict_c, default_abbr_dict_j = self._process_default_conferences_journals_json()

        # Load user-defined conferences and journals abbreviations from provided JSON files
        full_json_c, full_json_j = options.get("full_json_c", ""), options.get("full_json_j", "")
        user_abbr_dict_c, user_abbr_dict_j = process_user_conferences_journals_json(full_json_c, full_json_j)

        # Merge dictionaries: user abbreviations override default ones for the same keys
        full_abbr_article_dict = {**default_abbr_dict_j, **user_abbr_dict_j}
        full_abbr_inproceedings_dict = {**default_abbr_dict_c, **user_abbr_dict_c}

        full_names_in_json = "names_full"
        abbr_names_in_json = "names_abbr"

        # Pre-compile regex patterns for efficient matching
        abbr_article_pattern_dict, abbr_inproceedings_pattern_dict = self.abbr_article_inproceedings_pattern(
            full_abbr_article_dict, full_abbr_inproceedings_dict, full_names_in_json, abbr_names_in_json)

        # Store all configurations in options for later use
        options["full_abbr_article_dict"] = full_abbr_article_dict
        options["full_abbr_inproceedings_dict"] = full_abbr_inproceedings_dict
        options["full_names_in_json"] = full_names_in_json
        options["abbr_names_in_json"] = abbr_names_in_json
        options["abbr_article_pattern_dict"] = abbr_article_pattern_dict
        options["abbr_inproceedings_pattern_dict"] = abbr_inproceedings_pattern_dict

        self.options = options

    @staticmethod
    def abbr_article_inproceedings_pattern(
        full_abbr_article_dict, full_abbr_inproceedings_dict, full_names_in_json, abbr_names_in_json
    ):
        """Pre-compile regex patterns for journal and conference name matching.

        Args:
            full_abbr_article_dict: dictionary containing journal abbreviations and their full names
            full_abbr_inproceedings_dict: dictionary containing conference abbreviations and their full names
            full_names_in_json: Key for full names in the dictionary
            abbr_names_in_json: Key for abbreviation names in the dictionary

        Returns:
            Tuple of two dictionaries containing pre-compiled regex patterns for journals and conferences
        """

        def _create_pattern_dict(abbr_dict):
            """Helper function to create pattern dictionary for a given abbreviation dictionary."""
            pattern_dict = {}
            for abbr, abbr_info in abbr_dict.items():
                # Get all name variations and combine with abbreviation
                full_names = abbr_info.get(full_names_in_json, [])
                long_abbrs = abbr_info.get(abbr_names_in_json, [])
                all_names = [*full_names, *long_abbrs, abbr]

                # Create pre-compiled regex pattern for exact matching
                pattern_dict[abbr] = re.compile(rf'^({"|".join(all_names)})$', flags=re.I)
            return pattern_dict

        abbr_article_pattern_dict = _create_pattern_dict(full_abbr_article_dict)
        abbr_inproceedings_pattern_dict = _create_pattern_dict(full_abbr_inproceedings_dict)

        return abbr_article_pattern_dict, abbr_inproceedings_pattern_dict

    def _process_default_conferences_journals_json(self):
        """Process default conferences and journals JSON files from built-in templates.

        Notes:
            The structure of full_json_c follows the format
                {"abbr": {"names_abbr": [], "names_full": []}},
            while full_json_j adheres to the format
                {"abbr": {"names_abbr": [], "names_full": []}}.

        Returns:
            Tuple containing default conference dictionary and journal dictionary
        """
        # Get current directory and construct path to templates
        current_dir = os.path.dirname(os.path.abspath(__file__))
        path_templates = os.path.join(os.path.dirname(current_dir), "data", "templates")

        # Load conferences abbreviations dictionary
        full_json_c = os.path.join(path_templates, "abbr_full", "conferences.json")
        full_abbr_inproceedings_dict = load_json_dict(full_json_c)

        # Load journals abbreviations dictionary
        full_json_j = os.path.join(path_templates, "abbr_full", "journals.json")
        full_abbr_article_dict = load_json_dict(full_json_j)

        return full_abbr_inproceedings_dict, full_abbr_article_dict
