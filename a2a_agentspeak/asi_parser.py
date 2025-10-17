from dataclasses import dataclass
from enum import Enum


class SyntaxError(Exception):
    def __init__(self, message: str, filename: str, line: str):
        self.message = message
        self.filename = filename
        self.line = line


class Kind(Enum):
    BELIEF = "belief"
    INPUT = "input"
    ACTION = "action"


@dataclass
class Line:
    kind: Kind
    id: str
    doc: str


@dataclass
class Interface:
    name: str
    doc: str
    lines: list[Line]


def read_file(intf: str) -> Interface:
    with open(intf, "r") as f:
        l = f.readline()
        assert l.startswith("name = ")
        name = l.removeprefix("name = ")

        l = f.readline()
        assert l.startswith("doc = ")
        doc = l.removeprefix("doc = ")

        lines = []

        for l in f:

            if l == "\n":
                pass
            else:
                try:
                    [a, b, c] = l.split(" : ")
                    if a == "belief":
                        lines.append(Line(kind=Kind.BELIEF, doc=c, id=b))
                    elif a == "input":
                        lines.append(Line(kind=Kind.INPUT, doc=c, id=b))
                    elif a == "action":
                        lines.append(Line(kind=Kind.ACTION, doc=c, id=b))
                    else:
                        raise SyntaxError(intf, l, "Bad kind: " + a)
                except SyntaxError as e:
                    raise e
                except Exception as e:
                    raise SyntaxError(intf, l, "bad line structure")

        return Interface(name, doc, lines)
