import re

from ..utils.utils import load_json_file


class StrictOrderedDict:
    """A dictionary that strictly maintains insertion order.

    This implementation guarantees that keys, values, and items will always be
    returned in the exact order they were inserted, regardless of Python version
    or internal dictionary implementation changes.

    Attributes:
        _keys: List maintaining the order of key insertion.
        _data: Dictionary storing the actual key-value pairs.
    """

    def __init__(self, data=None):
        """Initializes the StrictOrderedDict with optional initial data.

        Args:
            data: Optional iterable of (key, value) pairs to initialize the dictionary.
                  If provided, must be an iterable containing exactly two-element
                  tuples or lists representing key-value pairs.

        Example:
            >>> sod = StrictOrderedDict()
            >>> sod = StrictOrderedDict([('a', 1), ('b', 2)])
        """
        self._keys = []    # Maintains insertion order of keys
        self._data = {}    # Stores the actual key-value mappings

        if data:
            for k, v in data:
                self[k] = v

    def __setitem__(self, key, value):
        """Sets a key-value pair, maintaining insertion order for new keys.

        Args:
            key: The key to set or update.
            value: The value to associate with the key.

        Note:
            If the key is new, it is added to the end of the insertion order.
            If the key exists, its value is updated but its position remains unchanged.
        """
        if key not in self._data:
            self._keys.append(key)  # Only add new keys to maintain order

        self._data[key] = value

    def __getitem__(self, key):
        """Retrieves the value associated with the given key.

        Args:
            key: The key to look up.

        Returns:
            The value associated with the key.

        Raises:
            KeyError: If the key is not found in the dictionary.
        """
        return self._data[key]

    def keys(self):
        """Returns all keys in insertion order.

        Returns:
            A copy of the list containing all keys in the order they were inserted.
        """
        return self._keys.copy()

    def values(self):
        """Returns all values in key insertion order.

        Returns:
            A list of values in the same order as their corresponding keys were inserted.
        """
        return [self._data[k] for k in self._keys]

    def items(self):
        """Returns all key-value pairs in insertion order.

        Returns:
            A list of (key, value) tuples in the order they were inserted.
        """
        return [(k, self._data[k]) for k in self._keys]

    def __repr__(self):
        """Returns a string representation of the dictionary.

        Returns:
            A string representation showing all key-value pairs in insertion order,
            formatted like a standard Python dictionary.

        Example:
            >>> sod = StrictOrderedDict([('x', 10), ('y', 20)])
            >>> print(sod)
            {'x': 10, 'y': 20}
        """
        items = [f"'{k}': {v}" for k, v in self.items()]
        return "{" + ", ".join(items) + "}"


def process_user_conferences_journals_json(full_json_c: str, full_json_j: str) -> tuple[dict, dict]:
    """Process user-defined conferences and journals JSON files.

    Notes:
        The structure of full_json_c follows the format
            {"publisher": {"conferences": {"abbr": {"names_abbr": [], "names_full": []}}}},
        while full_json_j adheres to the format
            {"publisher": {"journals": {"abbr": {"names_abbr": [], "names_full": []}}}}.
    """
    # Process user conferences JSON file
    json_dict = load_json_file(full_json_c)
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
    json_dict = load_json_file(full_json_j)
    full_abbr_article_dict = {}

    # Try different possible keys for journals section in JSON structure
    for flag in ["journals", "Journals", "JOURNALS", "journal", "Journal", "JOURNAL"]:
        full_abbr_article_dict = {p: json_dict[p].get(flag, {}) for p in json_dict}
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
        acronyms_bak = sorted(data.keys())

        for acronyms in [acronyms_bak, acronyms_bak[::-1]]:
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
