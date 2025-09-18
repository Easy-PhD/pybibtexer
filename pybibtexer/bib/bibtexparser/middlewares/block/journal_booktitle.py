import re

from ...library import Library
from ...model import Block, Entry
from ..middleware import BlockMiddleware


class AbbreviateJournalBooktitle(BlockMiddleware):
    """Abbreviate the field `journal` or `booktitle` value of an entry."""

    def __init__(
        self,
        full_abbr_article_dict: dict,
        full_abbr_inproceedings_dict: dict,
        abbr_index_article_for_abbr: int,
        abbr_index_inproceedings_for_abbr: int,
        full_names_in_json: str,
        abbr_names_in_json: str,
        allow_inplace_modification: bool = True
    ):
        super().__init__(allow_inplace_modification=allow_inplace_modification)

        self.full_abbr_article_dict = full_abbr_article_dict
        self.full_abbr_inproceedings_dict = full_abbr_inproceedings_dict
        self.abbr_index_article_for_abbr = abbr_index_article_for_abbr
        self.abbr_index_inproceedings_for_abbr = abbr_index_inproceedings_for_abbr
        self.full_names_in_json = full_names_in_json
        self.abbr_names_in_json = abbr_names_in_json

    # docstr-coverage: inherited
    def transform_entry(self, entry: Entry, library: Library) -> Block:
        return self.abbreviate_journal_booktitle(entry)

    def abbreviate_journal_booktitle(self, entry: Entry) -> Entry:
        """Abbreviate."""
        if entry.entry_type.lower() == "article":
            full_abbr_dict = self.full_abbr_article_dict
            field_key = "journal"
            abbr_index = self.abbr_index_article_for_abbr
        elif entry.entry_type.lower() == "inproceedings":
            full_abbr_dict = self.full_abbr_inproceedings_dict
            field_key = "booktitle"
            abbr_index = self.abbr_index_inproceedings_for_abbr
        else:
            return entry

        if abbr_index not in [1, 2]:
            return entry

        # Case 1
        if abbr_index == 2:
            regex = re.compile(r"([a-zA-Z])_([\w\-]+)_(.*)")
            if mch := regex.search(entry.key):
                if mch.group(1).lower() in ["j", "c"]:
                    entry[field_key] = mch.group(2)
                    return entry

        # Case 2
        # obtain new_dict
        abbr_dict_dict = {}
        for publisher in full_abbr_dict:
            abbr_dict_dict.update({abbr: full_abbr_dict[publisher][abbr] for abbr in full_abbr_dict[publisher]})

        field_content = entry[field_key] if field_key in entry else ""
        field_content = re.sub(r"\(.*\)", "", field_content).strip()

        if not field_content:
            return entry

        # match
        content_list = []
        for abbr in abbr_dict_dict:
            full_name_list = abbr_dict_dict[abbr].get(self.full_names_in_json, [])
            long_abbr_name_list = abbr_dict_dict[abbr].get(self.abbr_names_in_json, [])

            # long abbreviation
            if abbr_index == 1:
                for full, long_abbr in zip(full_name_list, long_abbr_name_list):
                    if re.match('{' + full + '}', '{' + field_content + '}', re.I):
                        content_list.append(long_abbr)

            # short abbreviation
            elif abbr_index == 2:
                full_abbr = []
                full_abbr.extend(full_name_list)
                full_abbr.extend(long_abbr_name_list)

                if re.match("{" + rf'({"|".join(full_abbr)})' + "}", "{" + field_content + "}", flags=re.I):
                    content_list.append(abbr)

        # check
        content_list = list(set(content_list))
        if len(content_list) > 1:
            print(f"Multiple match: {content_list} for {field_content}.")
        elif len(content_list) == 1:
            entry[field_key] = content_list[0]
        return entry


class DeleteRedundantInJournalBooktitle(BlockMiddleware):
    """Delete redundant part such as `(CEC)` in field `journal` or `booktitle` value of an entry."""

    def __init__(self, allow_inplace_modification: bool = True):
        super().__init__(allow_inplace_modification=allow_inplace_modification, allow_parallel_execution=True)

    # docstr-coverage: inherited
    def transform_entry(self, entry: Entry, library: Library) -> Block:
        if entry.entry_type.lower() in ["article", "inproceedings"]:
            for i in ["journal", "booktitle"]:
                value = entry[i] if i in entry else ""
                if value:
                    entry[i] = re.sub(r"\(.*\)", "", value).strip()
        return entry
