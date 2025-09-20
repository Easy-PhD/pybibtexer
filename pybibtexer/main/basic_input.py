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

    Notes:
        The structure of full_json_c follows the format {"publisher": {"conferences": {"abbr": {}}}},
            while full_json_j adheres to the format {"publisher": {"journals": {"abbr": {}}}}.
    """

    def __init__(self, options: Dict[str, Any]) -> None:
        # full_json_c and full_json_j
        current_dir = os.path.dirname(os.path.abspath(__file__))
        self._path_templates = os.path.join(os.path.dirname(current_dir), "data", "Templates")

        full_json_c = os.path.join(self._path_templates, "AbbrFull", "conferences.json")
        full_json_j = os.path.join(self._path_templates, "AbbrFull", "journals.json")

        _full_json_c = options.get("full_json_c")
        if isinstance(_full_json_c, str) and os.path.isfile(_full_json_c) and os.path.exists(_full_json_c):
            full_json_c = _full_json_c

        _full_json_j = options.get("full_json_j")
        if isinstance(_full_json_j, str) and os.path.isfile(_full_json_j) and os.path.exists(_full_json_j):
            full_json_j = _full_json_j

        self.full_json_c = full_json_c
        self.full_json_j = full_json_j

        self._initialize_middlewares(options)

        self.options = options

    # bib/core
    def _initialize_middlewares(self, options: Dict[str, Any]) -> None:
        if os.path.isfile(self.full_json_c):
            with open(self.full_json_c, "r") as f:
                try:
                    json_dict = json.loads(f.read())
                except Exception as e:
                    print(e)
                    json_dict = {}

                full_abbr_inproceedings_dict = {}
                for flag in ["conferences", "Conferences", "CONFERENCES", "conference", "Conference", "CONFERENCE"]:
                    full_abbr_inproceedings_dict = {p: json_dict[p].get(flag, {}) for p in json_dict}
                    if full_abbr_inproceedings_dict:
                        break
        else:
            full_abbr_inproceedings_dict = {}

        if os.path.isfile(self.full_json_j):
            with open(self.full_json_j, "r") as f:
                try:
                    json_dict = json.loads(f.read())
                except Exception as e:
                    print(e)
                    json_dict = {}

                full_abbr_article_dict = {}
                for flag in ["journals", "Journals", "JOURNALS", "journal", "Journal", "JOURNAL"]:
                    full_abbr_article_dict = {p: json_dict[p].get("journals", {}) for p in json_dict}
                    if full_abbr_article_dict:
                        break
        else:
            full_abbr_article_dict = {}

        self.full_abbr_inproceedings_dict = full_abbr_inproceedings_dict
        self.full_abbr_article_dict = full_abbr_article_dict

        full_names_in_json = options.get("full_names_in_json", "names_full")
        if not full_names_in_json:
            full_names_in_json = "names_full"
        self.full_names_in_json = full_names_in_json

        abbr_names_in_json = options.get("abbr_names_in_json", "names_abbr")
        if not abbr_names_in_json:
            abbr_names_in_json = "names_abbr"
        self.abbr_names_in_json = abbr_names_in_json

        options["full_abbr_article_dict"] = self.full_abbr_article_dict
        options["full_abbr_inproceedings_dict"] = self.full_abbr_inproceedings_dict

        options["full_names_in_json"] = self.full_names_in_json
        options["abbr_names_in_json"] = self.abbr_names_in_json
