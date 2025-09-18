import re
from typing import List, Tuple


class StandardizePreambleBlock(object):
    """Stanndardize preamble block."""

    def __init__(self) -> None:
        pass

    def standardize(self, block: List[str]) -> Tuple[List[str], List[List[str]]]:
        # @preamble{ "\providecommand{\noopsort}[1]{} " }
        implicit_comments = []
        regex_preamble = re.compile(
            r"@preamble{" + r'\s*(")' + r"([\w\-\\\[\]\{\}\s]+)" + r'(")\s*' + r"(.*)(\n*)", re.DOTALL
        )
        mch = regex_preamble.match("".join(block))
        if mch:
            a, b, c, d, e = mch.groups()
            if (a == '"') and (c == '"'):
                block = ["@preamble{ " + a + b.replace("\n", " ").strip() + c + " }\n"]

                if d and d.lstrip()[0] == "}":
                    d = d.lstrip()[1:].lstrip()

                if d.strip():
                    implicit_comments = [[d + e, __class__.__name__]]

            else:
                block = []
                implicit_comments = [["".join(block), __class__.__name__]]
        else:
            block = []
            implicit_comments = [["".join(block), __class__.__name__]]
        return block, implicit_comments
