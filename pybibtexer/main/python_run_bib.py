from typing import Any, Dict, List, Tuple, Union

from pyadvtools import transform_to_data_list

from ..bib.bibtexparser import Entry, Library
from ..bib.core import ConvertLibrayToLibrary, ConvertStrToLibrary
from .basic_input import BasicInput


class PythonRunBib(BasicInput):
    """Python bib.

    Args:
        options (Dict[str, Any]): Options.

    Attributes:
        choose_abbr_zotero_save (str): Selected bibliography purpose ("abbr", "zotero", or "save")
    """

    def __init__(self, options: Dict[str, Any]) -> None:
        options["choose_abbr_zotero_save"] = options.get("choose_abbr_zotero_save", "save")
        super().__init__(options)

    def parse_to_single_standard_library(
        self, original_data: Union[List[str], str, Library], given_cite_keys: List[str] = [], **kwargs
    ) -> Library:
        # update
        self.options["keep_entries_by_cite_keys"] = given_cite_keys

        if not isinstance(original_data, Library):
            original_data = transform_to_data_list(original_data, extension=".bib", **kwargs)
            original_data = ConvertStrToLibrary(self.options).generate_library(original_data)

        library = ConvertLibrayToLibrary(self.options).generate_single_library(original_data)
        return library

    def parse_to_multi_standard_library(
        self, original_data: Union[List[str], str, Library], given_cite_keys: List[str] = [], **kwargs
    ) -> Tuple[Library, Library, Library]:
        # update
        self.options["keep_entries_by_cite_keys"] = given_cite_keys

        if not isinstance(original_data, Library):
            original_data = transform_to_data_list(original_data, extension=".bib", **kwargs)
            original_data = ConvertStrToLibrary(self.options).generate_library(original_data)

        libraries = ConvertLibrayToLibrary(self.options).generate_multi_libraries(original_data)
        abbr_library, zotero_library, save_library = libraries
        return abbr_library, zotero_library, save_library

    def parse_to_nested_entries_dict(
        self, original_data: Union[List[str], str, Library], given_cite_keys: List[str] = [], **kwargs
    ) -> Dict[str, Dict[str, Dict[str, Dict[str, Dict[str, List[Entry]]]]]]:
        library = self.parse_to_single_standard_library(original_data, given_cite_keys, **kwargs)

        entry_type_year_volume_number_month_entry_dict = {}
        for entry in library.entries:
            entry_type = entry.entry_type
            year = entry["year"] if "year" in entry else "year"
            volume = entry["volume"] if "volume" in entry else "volume"
            number = entry["number"] if "number" in entry else "number"
            month = entry["month"] if "month" in entry else "month"
            entry_type_year_volume_number_month_entry_dict.setdefault(entry_type, {}).setdefault(year, {}).setdefault(
                volume, {}
            ).setdefault(number, {}).setdefault(month, []).append(entry)
        return entry_type_year_volume_number_month_entry_dict
