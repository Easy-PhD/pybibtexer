import json
import os
import re
from typing import Any

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
        """Read file content as string.

        Args:
            full_file (str): Path to the file to read

        Returns:
            str: Content of the file as string
        """
        # Read file content as string
        with open(full_file, "r", encoding="utf-8") as file:
            content = file.read()
        return content

    def parse_bibtex_file(self, full_biblatex: str, entry_type: str = "article"):
        """Parse BibTeX file and extract conference or journal data.

        Args:
            full_biblatex (str): Path to the BibLaTeX file
            entry_type (str): Type of entry to parse - 'article' or 'inproceedings'

        Returns:
            dict: Dictionary containing parsed conference or journal data

        Raises:
            ValueError: If entry_type is not 'article' or 'inproceedings'
        """
        if entry_type not in ["article", "inproceedings"]:
            raise ValueError("entry_type must be 'article' or 'inproceedings'")

        config = {
            "article": {
                "prefix": "J_",
                "pattern": r"@article\{(.*?),\s*([^@]*)\}",
                "full_field": "journaltitle",
                "abbr_field": "shortjournal"
            },
            "inproceedings": {
                "prefix": "C_",
                "pattern": r"@inproceedings\{(.*?),\s*([^@]*)\}",
                "full_field": "booktitle",
                "abbr_field": "eventtitle"
            }
        }

        cfg = config[entry_type]

        content = self._read_str(full_biblatex)

        # Regex pattern to match entries
        entries = re.findall(cfg["pattern"], content, re.DOTALL)

        result_dict = {}
        for cite_key, entry_content in entries:
            # Process only entries with the specified prefix
            if not cite_key.startswith(cfg["prefix"]):
                continue

            # Extract full and abbreviation fields
            full_match = re.search(
                rf"{cfg['full_field']}\s*=\s*{{([^}}]*)}}", entry_content
            )
            abbr_match = re.search(
                rf"{cfg['abbr_field']}\s*=\s*{{([^}}]*)}}", entry_content
            )

            # For inproceedings, booktitle is required but eventtitle is optional
            if not full_match:
                continue

            full = full_match.group(1).strip()
            if abbr_match:
                abbr = abbr_match.group(1).strip()
            else:
                # Use full name as abbreviation if abbreviation field is missing
                abbr = full

            parts = cite_key.split("_")
            if len(parts) >= 3:
                key = parts[1]

                # Check if key already exists
                if key in result_dict:
                    existing_entry = result_dict[key]

                    # Only add if full name is not already present
                    if full not in existing_entry["names_full"]:
                        existing_entry["names_abbr"].append(abbr)
                        existing_entry["names_full"].append(full)
                else:
                    # New key - add to dictionary
                    result_dict[key] = {"names_abbr": [abbr], "names_full": [full]}

        return result_dict

    def _compare_and_return(self, json_old: dict, json_new: dict) -> dict:
        """Compare old and new JSON data to find newly added items.

        Args:
            json_old: Old JSON data as dictionary
            json_new: New JSON data as dictionary

        Returns:
            dict: A dictionary containing keys that only exist in new data
        """
        # Find keys that only exist in new JSON
        keys_only_in_new = sorted(set(json_new.keys()) - set(json_old.keys()))
        new_only_data = {key: json_new[key] for key in keys_only_in_new}

        # Find common keys between old and new JSON
        common_keys = set(json_old.keys()) & set(json_new.keys())

        # Check each common key for new items using pattern matching
        for key in sorted(common_keys):

            for flag in ["names_full"]:
                old_items = [item.lower() for item in json_old[key][flag]]
                old_items = [item.replace("(", "").replace(")", "") for item in old_items]

                new_items = [item.lower() for item in json_new[key][flag]]
                new_items = [item.replace("(", "").replace(")", "") for item in new_items]

                # Convert to regex patterns
                patterns = [re.compile(f"^{item}$") for item in old_items]

                unmatched = []
                for new_item in new_items:
                    if (new_item not in old_items) and (not any(p.match(new_item) for p in patterns)):
                        unmatched.append(new_item)

                # Report unmatched items
                if unmatched:
                    print(f"New items found - Key: {key}, requires manual handling")
                    print(f"Existing data: {json_old[key][flag]}")
                    print(f"New data: {unmatched}")
                    print()

        # Return keys that only exist in new data
        return new_only_data

    def run(self, merge_json: bool = False) -> None:
        """Run the parsing pipeline.

        Args:
            merge_json: Whether to merge and save data to JSON files
        """
        # ==================== Conference Data Processing ====================
        json_old_c = self.load_json_file(self.default_full_json_c)
        json_new_c = self.parse_bibtex_file(self.full_biblatex, "inproceedings")

        print("*" * 9 + f" Checking existing conference data: `{self.default_full_json_c}` " + "*" * 9)
        json_old_c, _ = CheckAcronymAbbrAndFullDict().run(json_old_c)

        print("*" * 9 + f" Checking newly parsed conference data: `{self.full_biblatex}` " + "*" * 9)
        json_new_c, _ = CheckAcronymAbbrAndFullDict().run(json_new_c)

        print("*" * 9 + " Comparing existing conference data with newly parsed data " + "*" * 9)
        json_new_c = self._compare_and_return(json_old_c, json_new_c)

        print()

        # ==================== Journal Data Processing ====================
        json_old_j = self.load_json_file(self.default_full_json_j)
        json_new_j = self.parse_bibtex_file(self.full_biblatex, "article")

        print("*" * 9 + f" Checking existing journal data: `{self.default_full_json_j}` " + "*" * 9)
        json_old_j, _ = CheckAcronymAbbrAndFullDict().run(json_old_j)

        print("*" * 9 + f" Checking newly parsed journal data: `{self.full_biblatex}` " + "*" * 9)
        json_new_j, _ = CheckAcronymAbbrAndFullDict().run(json_new_j)

        print("*" * 9 + " Comparing existing journal data with newly parsed data " + "*" * 9)
        json_new_j = self._compare_and_return(json_old_j, json_new_j)

        print()

        # ==================== Check ====================
        # Process user-specific conference and journal JSON files
        user_c_json, user_j_json = process_user_conferences_journals_json(self.user_full_json_c, self.user_full_json_j)

        # Check for duplicates in conferences.json
        print("*" * 9 + " Checking duplicates in conferences " + "*" * 9)
        c = {**json_new_c, **json_old_c, **user_c_json}  # Priority: user > old > new
        c, c_flag = CheckAcronymAbbrAndFullDict().run(c)

        # Check for duplicates in journals.json
        print("*" * 9 + " Checking duplicates in journals " + "*" * 9)
        j = {**json_new_j, **json_old_j, **user_j_json}  # Priority: user > old > new
        j, f_flag = CheckAcronymAbbrAndFullDict().run(j)

        # ==================== Data Merging and Saving ====================
        if c_flag and f_flag and merge_json:
            self.save_to_json(c, self.default_full_json_c)
            self.save_to_json(j, self.default_full_json_j)
            print("Data merging completed and saved")

        return None

    @staticmethod
    def load_json_file(file_path: str) -> dict[str, Any]:
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
        try:
            if data:
                with open(full_json, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=4, sort_keys=True, ensure_ascii=True)

        except Exception as e:
            print(f"Error saving JSON file: {e}")

        return None


class CheckAcronymAbbrAndFullDict:
    def __init__(self, names_abbr="names_abbr", names_full="names_full"):
        self.names_abbr = names_abbr
        self.names_full = names_full

    def run(self, dict_data: dict[str, dict[str, list[str]]]) -> tuple[dict[str, dict[str, list[str]]], bool]:
        # Check if each acronym has equal number of abbreviations and full forms
        dict_data, length_check = self._validate_lengths(dict_data)

        # Check for duplicate abbreviations or full forms across all acronyms
        dict_data, duplicate_check = self._check_duplicates(dict_data)

        # Check for matching patterns in both abbreviations and full forms
        dict_data, abbr_match_check = self._check_matches(dict_data, self.names_abbr)
        dict_data, full_match_check = self._check_matches(dict_data, self.names_full)

        return dict_data, all([length_check, duplicate_check, abbr_match_check, full_match_check])

    def _validate_lengths(self, dict_data):
        """Validate that each acronym has equal number of abbreviations and full forms."""
        valid_data, all_valid = {}, True
        for acronym, value_dict in dict_data.items():
            names_abbr = value_dict.get(self.names_abbr, [])
            names_full = value_dict.get(self.names_full, [])

            if len(names_abbr) != len(names_full):
                all_valid = False
                print(
                    f"Length mismatch in '{acronym}': {len(names_abbr)} abbreviations vs {len(names_full)} full forms"
                )
            else:
                valid_data[acronym] = value_dict
        return valid_data, all_valid

    def _check_duplicates(self, data):
        """Check for duplicate abbreviations or full forms across all acronyms."""
        valid_data = {}
        all_unique = True
        seen_abbrs = set()
        seen_fulls = set()

        for acronym, values in data.items():
            has_duplicate = False

            # Check for duplicate abbreviations
            abbrs_lower = {abbr.lower() for abbr in values.get(self.names_abbr, [])}
            for abbr in abbrs_lower:
                if abbr in seen_abbrs:
                    print(f"Duplicate abbreviation '{abbr}' found in '{acronym}'")
                    has_duplicate = True
                else:
                    seen_abbrs.add(abbr)

            # Check for duplicate full forms
            fulls_lower = {full.lower() for full in values.get(self.names_full, [])}
            for full in fulls_lower:
                if full in seen_fulls:
                    print(f"Duplicate full form '{full}' found in '{acronym}'")
                    has_duplicate = True
                else:
                    seen_fulls.add(full)

            if not has_duplicate:
                valid_data[acronym] = values
            else:
                all_unique = False

        return valid_data, all_unique

    def _check_matches(self, data, key_type: str):
        """Check for exact matches in abbreviations or full forms between different acronyms."""
        valid_data = {}
        no_matches = True
        acronyms = sorted(data.keys())

        for i, main_acronym in enumerate(acronyms):
            # Normalize items: lowercase and remove parentheses
            main_items = [
                item.lower().replace("(", "").replace(")", "")
                for item in data[main_acronym].get(key_type, [])
            ]

            # Create exact match patterns
            patterns = [re.compile(f"^{item}$") for item in main_items]

            matches_found = []

            # Compare with other acronyms
            for other_acronym in acronyms[i + 1:]:
                other_items = [
                    item.lower().replace("(", "").replace(")", "")
                    for item in data[other_acronym].get(key_type, [])
                ]

                # Find matching items
                matching_items = [
                    item for item in other_items
                    if any(pattern.match(item) for pattern in patterns)
                ]

                if matching_items:
                    matches_found.append([main_acronym, other_acronym, matching_items])

            if matches_found:
                no_matches = False
                print(f"Found matches in {key_type}: {matches_found}")
            else:
                valid_data[main_acronym] = data[main_acronym]

        return valid_data, no_matches
