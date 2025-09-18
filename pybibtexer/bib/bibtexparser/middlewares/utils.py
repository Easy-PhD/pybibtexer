import re
from typing import Any, Dict

from ...bibtexbase.standardize_bib import MARKS_FLAGS
from ..model import Entry


def generate_cite_key_prefix(
    entry: Entry,
    full_abbr_article_dict: Dict[str, Any],
    full_abbr_inproceedings_dict: Dict[str, Any],
    full_names_in_json: str,
    abbr_names_in_json: str,
) -> str:
    prefix = generate_entry_abbr(entry.entry_type)

    if prefix.upper() in ["C", "J"]:
        prefix = generate_cite_key_prefix_c_j(
            entry, full_abbr_article_dict, full_abbr_inproceedings_dict, full_names_in_json, abbr_names_in_json
        )

    elif prefix == "D":
        if "url" in entry:
            if re.search(r"arxiv\.org", entry["url"]):
                prefix = "arXiv"
            elif re.search(r"biorxiv\.org", entry["url"]):
                prefix = "bioRxiv"
            elif re.search(r"ssrn\.", entry["url"]):
                prefix = "SSRN"
    return prefix


def generate_cite_key_prefix_c_j(
    entry: Entry,
    full_abbr_article_dict: Dict[str, Any],
    full_abbr_inproceedings_dict: Dict[str, Any],
    full_names_in_json: str,
    abbr_names_in_json: str,
) -> str:
    if entry.entry_type.lower() == "article":
        full_abbr_dict = full_abbr_article_dict
        field_key = "journal"
        prefix = "J"
    elif entry.entry_type.lower() == "inproceedings":
        full_abbr_dict = full_abbr_inproceedings_dict
        field_key = "booktitle"
        prefix = "C"
    else:
        return ""

    abbr_dict_dict = {}
    for publisher in full_abbr_dict:
        abbr_dict_dict.update({abbr: full_abbr_dict[publisher][abbr] for abbr in full_abbr_dict[publisher]})

    field_content = entry[field_key] if field_key in entry else ""

    # 2024 IEEE congress on evolutionary computation (CEC)
    # 2024 IEEE congress on evolutionary computation
    field_content = re.sub(r"\(.*\)", "", field_content).strip()

    if not field_content:
        return prefix

    # match
    abbr_list = []
    for abbr in abbr_dict_dict:
        full_name_list = abbr_dict_dict[abbr].get(full_names_in_json, [])
        long_abbr_name_list = abbr_dict_dict[abbr].get(abbr_names_in_json, [])

        # [full, long_abbr, abbr]
        full_abbr = []
        full_abbr.extend(full_name_list)
        full_abbr.extend(long_abbr_name_list)
        full_abbr.append(abbr)

        # completely match
        if re.match("^{" + rf'({"|".join(full_abbr)})' + "}$", "{" + field_content + "}", flags=re.I):
            abbr_list.append(abbr)

    # check
    abbr_list = list(set(abbr_list))
    if len(abbr_list) > 1:
        print(f"Multiple match: {abbr_list} for {field_content}.")
    elif len(abbr_list) == 1:
        prefix = prefix + "_" + abbr_list[0]
    return prefix


def generate_entry_abbr(entry_type: str) -> str:
    """Generate abbr according to entry type.

    zotero item type:
        ['Journal Article', 'Conference Paper', 'Book', 'Book Section', 'Document', 'Manuscript', 'Report', 'Thesis',
         'Thesis']
    zotero export:
        ['article', 'inproceedings','book', 'incollection', 'misc', 'unpublished', 'techreport', 'phdthesis',
         'masterthesis']
    """
    entries = {k[0]: k[2] for k in MARKS_FLAGS if k[1] == "entry"}
    return entries.get(entry_type.lower(), "")


SKIP_WORD_IN_CITATION_KEY = [
    "a",
    "ab",
    "aboard",
    "about",
    "above",
    "across",
    "after",
    "against",
    "al",
    "along",
    "amid",
    "among",
    "an",
    "and",
    "anti",
    "around",
    "as",
    "at",
    "before",
    "behind",
    "below",
    "beneath",
    "beside",
    "besides",
    "between",
    "beyond",
    "but",
    "by",
    "d",
    "da",
    "das",
    "de",
    "del",
    "dell",
    "dello",
    "dei",
    "degli",
    "della",
    "dell",
    "delle",
    "dem",
    "den",
    "der",
    "des",
    "despite",
    "die",
    "do",
    "down",
    "du",
    "during",
    "ein",
    "eine",
    "einem",
    "einen",
    "einer",
    "eines",
    "el",
    "en",
    "et",
    "except",
    "for",
    "from",
    "gli",
    "i",
    "il",
    "in",
    "inside",
    "into",
    "is",
    "l",
    "la",
    "las",
    "le",
    "les",
    "like",
    "lo",
    "los",
    "near",
    "nor",
    "of",
    "off",
    "on",
    "onto",
    "or",
    "over",
    "past",
    "per",
    "plus",
    "round",
    "save",
    "since",
    "so",
    "some",
    "sur",
    "than",
    "the",
    "through",
    "to",
    "toward",
    "towards",
    "un",
    "una",
    "unas",
    "under",
    "underneath",
    "une",
    "unlike",
    "uno",
    "unos",
    "until",
    "up",
    "upon",
    "versus",
    "via",
    "von",
    "while",
    "with",
    "within",
    "without",
    "yet",
    "zu",
    "zum",
]
