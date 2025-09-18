import copy
import os
from typing import Any, Dict, List

from pyadvtools import sort_int_str

from ..bib.bibtexparser import Entry


def obtain_local_abbr_paths(path_storage: str, options: dict) -> List[str]:
    """Get all local abbreviation paths from the storage directory.

    Scans the specified storage directory and returns paths to all abbreviation
    subdirectories that match the inclusion/exclusion criteria in options.

    Parameters
    ----------
    path_storage : str
        Root directory containing publisher/abbreviation folders
    options : dict
        Configuration dictionary containing:
            - include_publisher_list: List of publishers to include
            - exclude_publisher_list: List of publishers to exclude
            - include_abbr_list: List of abbreviations to include
            - exclude_abbr_list: List of abbreviations to exclude

    Returns
    -------
    List[str]
        List of full paths to all matching abbreviation directories
    """
    abbr_list = []
    if not os.path.exists(path_storage):
        return []

    publisher_abbr_dict = generate_standard_publisher_abbr_options_dict(path_storage, options)
    for publisher in publisher_abbr_dict:
        for abbr in publisher_abbr_dict[publisher]:
            abbr_list.append(os.path.join(path_storage, publisher, abbr))
    return abbr_list


def generate_standard_publisher_abbr_options_dict(
    path_storage: str, options: Dict[str, Any]
) -> Dict[str, Dict[str, Dict[str, Any]]]:
    """Generate a nested dictionary of publisher/abbreviation options.

    Creates a hierarchical dictionary structure representing all publishers
    and their abbreviations that match the inclusion/exclusion criteria.

    Parameters
    ----------
    path_storage : str
        Root directory containing publisher/abbreviation folders
    options : Dict[str, Any]
        Configuration options including inclusion/exclusion lists

    Returns
    -------
    Dict[str, Dict[str, Dict[str, Any]]]
        Nested dictionary structure:
            - Top level: Publisher names
            - Middle level: Abbreviation names
            - Inner level: Copy of options dictionary
    """
    if not os.path.exists(path_storage):
        return {}

    # First scan directory structure to find all publishers and abbreviations
    publisher_abbr_dict: Dict[str, List[str]] = {}
    publishers = [f for f in os.listdir(path_storage) if os.path.isdir(os.path.join(path_storage, f))]
    for p in publishers:
        path_p = os.path.join(path_storage, p)
        publisher_abbr_dict.update({p: [f for f in os.listdir(path_p) if os.path.isdir(os.path.join(path_p, f))]})

    # Apply inclusion/exclusion filters to publishers
    publisher_list = in_not_in_list(
        list(publisher_abbr_dict.keys()),
        options.get("include_publisher_list", []),
        options.get("exclude_publisher_list", []),
    )

    # Build the nested options dictionary structure
    publisher_abbr_options_dict: Dict[str, Dict[str, Dict[str, Any]]] = {}
    for publisher in sort_int_str(publisher_list):

        # Apply inclusion/exclusion filters to abbreviations
        abbr_list = in_not_in_list(
            publisher_abbr_dict[publisher], options.get("include_abbr_list", []), options.get("exclude_abbr_list", [])
        )

        # Create nested structure with copied options
        for abbr_standard in sort_int_str(abbr_list):
            publisher_abbr_options_dict.setdefault(publisher, {}).setdefault(abbr_standard, copy.deepcopy(options))
    return publisher_abbr_options_dict


def in_not_in_list(original: List[str], in_list: List[str], out_list: List[str]):
    """Filter a list based on inclusion and exclusion criteria.

    Parameters
    ----------
    original : List[str]
        Original list to filter
    in_list : List[str]
        List of items to include (case-insensitive)
    out_list : List[str]
        List of items to exclude (case-insensitive)

    Returns
    -------
    List[str]
        Filtered list containing only items that:
            - Are in in_list (if in_list is not empty)
            - Are not in out_list
    """
    if in_list := [o.lower() for o in in_list]:
        original = [o for o in original if o.lower() in in_list]
    if out_list := [o.lower() for o in out_list]:
        original = [o for o in original if o.lower() not in out_list]
    return original


def generate_readme(
    j_conf_abbr: str,
    entry_type: str,
    year_volume_number_month_entry_dict: Dict[str, Dict[str, Dict[str, Dict[str, List[Entry]]]]],
) -> List[str]:
    """Generate a README markdown file summarizing bibliography entries.

    Creates a formatted markdown table showing publication statistics
    organized by year, volume, number, and month.

    Parameters
    ----------
    j_conf_abbr : str
        Journal/conference abbreviation for the title
    entry_type : str
        Type of bibliography entries (article, inproceedings, etc.)
    year_volume_number_month_entry_dict : Dict[str, Dict[str, Dict[str, Dict[str, List[Entry]]]]]
        Nested dictionary structure containing entries organized by:
            - Year
            - Volume
            - Number
            - Month

    Returns
    -------
    List[str]
        Lines of the generated markdown file, or empty list if no valid entries
    """
    # Configuration for different entry types
    entry_type_list = ["article", "inproceedings", "misc"]
    filed_key_list = ["journal", "booktitle", "publisher"]

    # Determine which field to display based on entry type
    field_key = ""
    if (entry_type := entry_type.lower()) in entry_type_list:
        field_key = filed_key_list[entry_type_list.index(entry_type)]

    def extract_journal_booktitle(entries: List[Entry], field_key: str) -> List[str]:
        """Extract unique journal/booktitle values from entries."""
        if field_key:
            contents = []
            for entry in entries:
                value = entry[field_key] if field_key in entry else ""
                contents.append(value)
            return sorted(set(contents), key=contents.index)
        return []

    # Initialize markdown content with header
    readme = [f"# {j_conf_abbr}-{entry_type.title()}\n\n", f"|Name|Year|Papers|{field_key.title()}|\n", "|-|-|-|-|\n"]

    # Process each hierarchical level to build the table
    for year in year_volume_number_month_entry_dict:
        for volume in year_volume_number_month_entry_dict[year]:
            for number in year_volume_number_month_entry_dict[year][volume]:
                for month in year_volume_number_month_entry_dict[year][volume][number]:

                    # Generate filename components
                    file_name = ""
                    for i, j in zip(["", "Vol.", "No.", "Month"], [j_conf_abbr, volume, number, month]):
                        if j.lower().strip() in ["volume", "number", "month"]:
                            j = ""
                        file_name += (i + j + "-") * (len(j.strip()) >= 1)

                    # Count papers and get journal/booktitle info
                    number_paper = len(temp := year_volume_number_month_entry_dict[year][volume][number][month])
                    j_b = extract_journal_booktitle(temp, field_key)

                    # Add table row
                    readme.append(f'|{file_name[:-1]}|{year}|{number_paper}|{"; ".join(j_b)}|' + "\n")

    # Only return content if we have more than just the header
    if len(readme) > 3:
        return readme
    return []
