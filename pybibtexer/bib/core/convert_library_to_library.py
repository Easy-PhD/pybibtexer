from typing import Any, Dict, Tuple

from ..bibtexparser import Library, MiddlewaresLibraryToLibrary


class ConvertLibrayToLibrary(object):
    """Convert library to library.

    Args:
        options (Dict[str, Any]): Options. Default is {}.

    Attributes:
        choose_abbr_zotero_save (str): Choose "abbr", "zotero", or "save". Default is "save".
    """

    def __init__(self, options: Dict[str, Any] = {}) -> None:

        self.choose_abbr_zotero_save = options.get("choose_abbr_zotero_save", "save")

        self._middleware_library_library = MiddlewaresLibraryToLibrary(options)

    def generate_single_library(self, library: Library) -> Library:
        func = eval(f"_x.function_{self.choose_abbr_zotero_save}", {}, {"_x": self._middleware_library_library})
        library = func(library)

        return library

    def generate_multi_libraries(self, library: Library) -> Tuple[Library, Library, Library]:
        abbr_library, zotero_library, save_library = self._middleware_library_library.functions(library)

        return abbr_library, zotero_library, save_library
