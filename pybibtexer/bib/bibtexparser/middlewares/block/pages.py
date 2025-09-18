from ...library import Library
from ...model import Block, Entry
from ..middleware import BlockMiddleware


class NormalizePagesInEntry(BlockMiddleware):
    """Normalize field `pages` of an entry by deleting redundant part or generating when not existed."""

    def __init__(self, allow_inplace_modification: bool = True):
        super().__init__(allow_inplace_modification=allow_inplace_modification, allow_parallel_execution=True)

    # docstr-coverage: inherited
    def transform_entry(self, entry: Entry, library: Library) -> Block:
        if "pages" in entry:
            # 5-10-5-10 -> 5-10
            page_list = []
            for page in entry["pages"].split("-"):  # English hyphen
                for p in page.strip().split("—"):  # Chinese hyphen
                    if p.strip():
                        page_list.append(p.strip())

            page_list = sorted(set(page_list), key=page_list.index)
            entry["pages"] = "-".join(page_list)
        else:
            # pages = {12:1-37}
            if "articleno" in entry and "numpages" in entry:
                entry["pages"] = f'{entry["articleno"]}:1-{entry["numpages"]}'
        return entry
