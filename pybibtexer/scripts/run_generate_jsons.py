import os
import re

from ..main.utils import CheckAcronymAbbrAndFullDict, process_user_conferences_journals_json
from ..utils.utils import load_json_file, save_to_json


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
        with open(full_file, encoding="utf-8") as file:
            content = file.read()
        return content

    def parse_bibtex_file(self, full_biblatex: str, entry_type: str = "article"):
        """Parse BibTeX file and extract conference or journal data.

        Args:
            full_biblatex (str): Path to the BibLaTeX file
            entry_type (str): Type of entry to parse - 'article' or 'inproceedings'

        Returns:
            dict: dictionary containing parsed conference or journal data

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
        json_old_c = load_json_file(self.default_full_json_c)
        json_new_c = self.parse_bibtex_file(self.full_biblatex, "inproceedings")

        print("*" * 9 + f" Checking existing conference data: `{self.default_full_json_c}` " + "*" * 9)
        json_old_c, _ = CheckAcronymAbbrAndFullDict().run(json_old_c)

        print("*" * 9 + f" Checking newly parsed conference data: `{self.full_biblatex}` " + "*" * 9)
        json_new_c, _ = CheckAcronymAbbrAndFullDict().run(json_new_c)

        print("*" * 9 + " Comparing existing conference data with newly parsed data " + "*" * 9)
        json_new_c = self._compare_and_return(json_old_c, json_new_c)

        print()

        # ==================== Journal Data Processing ====================
        json_old_j = load_json_file(self.default_full_json_j)
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
            save_to_json(c, self.default_full_json_c)
            save_to_json(j, self.default_full_json_j)
            print("Data merging completed and saved")

        return None
