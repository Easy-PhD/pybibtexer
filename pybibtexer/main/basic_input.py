import os
from typing import Any, Dict

from .utils import load_json_dict, process_user_conferences_journals_json


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
        full_json_c, full_json_j = options.get("full_json_c", ""), options.get("full_json_j", "")
        user_abbr_dict_c, user_abbr_dict_j = process_user_conferences_journals_json(full_json_c, full_json_j)

        # Merge dictionaries: user abbreviations override default ones for the same keys
        options["full_abbr_article_dict"] = {**default_abbr_dict_j, **user_abbr_dict_j}
        options["full_abbr_inproceedings_dict"] = {**default_abbr_dict_c, **user_abbr_dict_c}

        # Set JSON field names for full and abbreviated names
        options["full_names_in_json"] = "names_full"
        options["abbr_names_in_json"] = "names_abbr"

        self.options = options

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
        full_abbr_inproceedings_dict = load_json_dict(full_json_c)

        # Load journals abbreviations dictionary
        full_json_j = os.path.join(path_templates, "abbr_full", "journals.json")
        full_abbr_article_dict = load_json_dict(full_json_j)

        return full_abbr_inproceedings_dict, full_abbr_article_dict
