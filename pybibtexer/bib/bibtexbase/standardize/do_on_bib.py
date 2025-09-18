import re
from typing import Dict, List, Tuple

from ._base import split_data_list


class SplitBibAccordingToMark(object):
    def __init__(self) -> None:
        super().__init__()

    def split_marks(self, data_list: List[str]) -> List[str]:
        return split_data_list(r"(@[a-zA-Z]+{)", data_list, "next")


class ObtainMarkBlocksDict(object):
    def __init__(self) -> None:
        pass

    def obtain_dict(
        self, data_list: List[str], is_lower_mark: bool = True
    ) -> Tuple[Dict[str, List[List[str]]], List[List[str]]]:
        r"""Generate blocks.

        Args:
            data_list (List[str]): data list.

        Returns:
            Tuple[Dict[str, List[List[str]]], List[str]]: dict and implicit comments.
        """
        regex_mark = re.compile(r"@([a-zA-Z]+){")
        line_index, len_data, implicit_comment_list = 0, len(data_list), []
        mark_patch_bib_list_dict: Dict[str, List[List[str]]] = {}
        while line_index < len_data:
            line = data_list[line_index]
            line_index += 1
            if mch := regex_mark.match(line):
                mark = mch.group(1)
                temp = [line]
                while line_index < len_data:
                    line = data_list[line_index]
                    if regex_mark.match(line):
                        break
                    temp.append(line)
                    line_index += 1
                if is_lower_mark:
                    mark = mark.lower()
                mark_patch_bib_list_dict.setdefault(mark, []).append(temp)
            else:
                implicit_comment_list.append([line, __class__.__name__])
        return mark_patch_bib_list_dict, implicit_comment_list


if __name__ == "__main__":
    pass
