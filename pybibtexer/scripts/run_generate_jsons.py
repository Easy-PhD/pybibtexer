import json
import os
import re
from typing import Any

from pyadvtools.tools import IterateSortDict

from ..main.utils import process_user_conferences_journals_json


def run_generate_jsons(
    default_full_json_c: str,
    default_full_json_j: str,
    full_biblatex: str,
    user_full_json_c: str,
    user_full_json_j: str,
    merge_json: bool = False
) -> None:
    """Execute the JSON generation process for conferences and journals.

    Args:
        default_full_json_c (str): Path to the default conferences JSON file
            Contains predefined conference abbreviations and full names
        default_full_json_j (str): Path to the default journals JSON file
            Contains predefined journal abbreviations and full names
        full_biblatex (str): Path to the BibLaTeX source file
            Used as input for generating/updating JSON data
        user_full_json_c (str): Path to the user conferences JSON file
            Stores user-specific conference abbreviations and full names
        user_full_json_j (str): Path to the user journals JSON file
            Stores user-specific journal abbreviations and full names
        merge_json (bool, optional): Flag indicating whether to merge JSON data
            If True, merges data from multiple sources; if False, do nothing
            Defaults to False

    Returns:
        None: This function does not return any value

    Notes:
        This function serves as a convenient wrapper to instantiate and execute
        the GenerateDefaultJSONs class with the provided parameters.
    """
    GenerateDefaultJSONs(
        default_full_json_c,
        default_full_json_j,
        full_biblatex,
        user_full_json_c,
        user_full_json_j,
    ).run(merge_json)
    return None


class GenerateDefaultJSONs:
    def __init__(
        self,
        default_full_json_c: str,
        default_full_json_j: str,
        full_biblatex: str,
        user_full_json_c: str,
        user_full_json_j: str,
    ) -> None:
        """Initialize the GenerateJSON class with file paths for JSON generation.

        Args:
            default_full_json_c (str): Path to the default conferences JSON file
                Contains predefined conference abbreviations and full names
            default_full_json_j (str): Path to the default journals JSON file
                Contains predefined journal abbreviations and full names
            full_biblatex (str): Path to the BibLaTeX source file
                Used as input for generating/updating JSON data
            user_full_json_c (str): Path to the user conferences JSON file
                Stores user-specific conference abbreviations and full names
            user_full_json_j (str): Path to the user journals JSON file
                Stores user-specific journal abbreviations and full names

        Notes:
            All file paths are expanded to handle environment variables and user home directory shortcuts.
            The structure follows a separation between default (system) data and user-customized data.
        """
        # Expand environment variables and user home directory in file paths
        # Process default conferences JSON file path
        self.default_full_json_c = os.path.expandvars(os.path.expanduser(default_full_json_c))
        # Process default journals JSON file path
        self.default_full_json_j = os.path.expandvars(os.path.expanduser(default_full_json_j))

        # Process BibLaTeX source file path
        self.full_biblatex = os.path.expandvars(os.path.expanduser(full_biblatex))

        # Process user conferences JSON file path
        self.user_full_json_c = os.path.expandvars(os.path.expanduser(user_full_json_c))
        # Process user journals JSON file path
        self.user_full_json_j = os.path.expandvars(os.path.expanduser(user_full_json_j))

    @staticmethod
    def _read_str(full_file: str) -> str:
        # Read file content as string
        with open(full_file, "r", encoding="utf-8") as file:
            content = file.read()
        return content

    def parse_bibtex_file(self, full_biblatex: str):
        # Read BibLaTeX file content
        content = self._read_str(full_biblatex)

        # Regex pattern to match @article entries
        article_pattern = r"@article\{(.*?),\s*([^@]*)\}"
        articles = re.findall(article_pattern, content, re.DOTALL)

        journal_dict = {}
        for cite_key, entry_content in articles:
            # Process only entries starting with 'J_' (journal entries)
            if not cite_key.startswith("J_"):
                continue

            # Extract journaltitle and shortjournal fields
            journal_title_match = re.search(
                r"journaltitle\s*=\s*\{([^}]*)\}", entry_content
            )
            short_journal_match = re.search(
                r"shortjournal\s*=\s*\{([^}]*)\}", entry_content
            )

            if not (journal_title_match and short_journal_match):
                continue

            journal_title = journal_title_match.group(1).strip()
            short_journal = short_journal_match.group(1).strip()

            parts = cite_key.split("_")
            if len(parts) >= 3:
                journal_key = parts[1]

                # Check if key already exists
                if journal_key in journal_dict:
                    existing_entry = journal_dict[journal_key]

                    # Only update if journaltitle and shortjournal are identical
                    if journal_title not in existing_entry["names_full"]:
                        existing_entry["names_abbr"] = existing_entry["names_abbr"].append(
                            short_journal
                        )
                        existing_entry["names_full"] = existing_entry["names_full"].append(
                            journal_title
                        )
                else:
                    # New key - add to dictionary
                    journal_dict[journal_key] = {
                        "names_abbr": [short_journal],
                        "names_full": [journal_title],
                    }

        return journal_dict

    @staticmethod
    def _check_multiple_items(json_data: dict) -> None:
        # Check for entries with multiple full names
        for key in json_data:
            if len(set(json_data[key].get("names_full", []))) > 1:
                print(f"{key}: {json_data[key]["names_full"]}")
                print(f"{key}: {json_data[key]["names_abbr"]}")

        print()
        for flag in ["names_full", "names_abbr"]:
            # Create reverse mapping from full/abbr names to keys
            new_json_data = {}
            for key in json_data:
                for j in json_data[key].get(flag, []):
                    new_json_data.setdefault(j, []).append(key)

            # Check for full/abbr names that map to multiple keys
            for key in new_json_data:
                if len(set(new_json_data[key])) > 1:
                    print(f"{key}: {new_json_data[key]}")

            print()

        return None

    def _check_duplicate(self, json_old: dict, json_new: dict) -> None:
        # Check for duplicate keys between old and new JSON data
        for key in json_old:
            if key in json_new:
                # Check if new data has any items not in old data
                if any(item not in json_old[key] for item in json_new[key]):
                    print(f"Old data:{json_old[key]}")
                    print(f"New data:{json_new[key]}")
                    print()
        return None

    def run(self, merge_json: bool = False) -> None:
        # Load existing JSON data
        print(f"Check in `JSON {self.default_full_json_j}`")
        json_old_j = self.load_json_file(self.default_full_json_j)
        self._check_multiple_items(json_old_j)
        print()

        # Parse new data from BibLaTeX file
        json_new_j = self.parse_bibtex_file(self.full_biblatex)
        # Check for multiple items in new data
        print(f"Check in `JSON generated from {self.full_biblatex}`")
        self._check_multiple_items(json_new_j)
        print()

        # Check for duplicates between old and new data
        print(f"Compare `{self.default_full_json_j}` with `JSON generated from {self.full_biblatex}`")
        self._check_duplicate(json_old_j, json_new_j)  # Identify overlapping entries
        print()

        # Merge old and new data (new data overwrites old data for same keys) and save
        if merge_json:
            # Process user-specific conference and journal JSON files
            _c_json, _j_json = process_user_conferences_journals_json(self.user_full_json_c, self.user_full_json_j)

            # Save conference data
            _c_json = IterateSortDict().dict_update(_c_json)
            self.save_to_json(_c_json, self.default_full_json_c)

            # Merge journal data with priority: new data > user data > old data
            self.save_to_json({**json_old_j, **json_new_j, **_j_json}, self.default_full_json_j)

        return None

    @staticmethod
    def load_json_file(file_path: str) -> dict[str, Any]:
        # Check if file exists
        if not os.path.isfile(file_path):
            print(f"File not found: {file_path}")
            return {}

        try:
            # Open and read the JSON file
            with open(file_path, 'r', encoding='utf-8') as file:
                return json.load(file)

        except Exception as e:
            print(f"Error reading file {file_path}: {e}")
            return {}

    @staticmethod
    def save_to_json(data: dict, full_json: str) -> None:
        # Save data to JSON file
        try:
            if data:
                with open(full_json, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=4, sort_keys=True, ensure_ascii=True)

        except Exception as e:
            print(f"Error saving JSON file: {e}")

        return None
