from typing import List, Tuple

from .standardize.do_on_bib import ObtainMarkBlocksDict, SplitBibAccordingToMark
from .standardize.do_on_comment_block import StandardizeCommentBlock
from .standardize.do_on_entry_block import StandardizeEntryBlock
from .standardize.do_on_preamble_block import StandardizePreambleBlock
from .standardize.do_on_string_block import StandardizeStringBlock

MARKS_FLAGS = [
    ["comment", "comment", "CMT"],      # comment
    ["string", "string", "S"],          # string
    ["preamble", "preamble", "P"],      # preamble
    ["article", "entry", "J"],          # entry
    ["inproceedings", "entry", "C"],    # entry
    ["proceedings", "entry", "B"],      # entry
    ["book", "entry", "B"],             # entry
    ["incollection", "entry", "BS"],    # entry
    ["misc", "entry", "D"],             # entry
    ["unpublished", "entry", "M"],      # entry
    ["techreport", "entry", "R"],       # entry
    ["phdthesis", "entry", "T_D"],      # entry
    ["mastersthesis", "entry", "T_M"],  # entry
]


class StandardizeBib(object):
    """Stanndardize bib.

    Args:
        default_additional_field_list (List[str] = []): Additional default fields.
    """

    def __init__(self, default_additional_field_list: List[str] = []) -> None:
        self._standardize_comment_block = StandardizeCommentBlock()
        self._standardize_entry_block = StandardizeEntryBlock(default_additional_field_list)
        self._standardize_preamble_block = StandardizePreambleBlock()
        self._standardize_string_block = StandardizeStringBlock()

    def standardize(self, data_list: List[str]) -> Tuple[List[str], List[List[str]]]:
        """Generate standard bib.

        Args:
            data_list (List[str]): Bib data.

        Returns:
            List[str]: Standard bib.
        """
        # Initialize
        data_list = "".join(data_list).splitlines(keepends=True)
        data_list = [line for line in data_list if line.strip()]

        # Split data according to mark pattern
        data_list = SplitBibAccordingToMark().split_marks(data_list)

        new_data_list: List[str] = []
        implicit_comment_list: List[List[str]] = []

        # Generate dict
        mark_blocks_dict, temp_implicit_comment_list = ObtainMarkBlocksDict().obtain_dict(data_list, True)
        implicit_comment_list.extend(temp_implicit_comment_list)

        marks, flags = [i[0] for i in MARKS_FLAGS], [i[1] for i in MARKS_FLAGS]
        if not_in := {k: v for k, v in mark_blocks_dict.items() if k not in marks}:
            print(f"Warning: Not standard parts - {not_in}")

        for mark in mark_blocks_dict:
            if mark in marks:
                flag = flags[marks.index(mark)]

                for block in mark_blocks_dict[mark]:
                    block, temp = eval(f"self._standardize_{flag}_block.standardize")(block)
                    new_data_list.extend(block)
                    implicit_comment_list.extend(temp)

        return new_data_list, implicit_comment_list
