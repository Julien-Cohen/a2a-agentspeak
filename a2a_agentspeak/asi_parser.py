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
    arity: int
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
        agent_doc = l.removeprefix("doc = ")

        lines = []

        for l in f:

            if l == "\n":
                pass
            else:
                try:
                    [k, lit, a, doc] = l.split(" : ")
                    if k == "belief":
                        lines.append(
                            Line(kind=Kind.BELIEF, doc=doc, id=lit, arity=int(a))
                        )
                    elif k == "input":
                        lines.append(
                            Line(kind=Kind.INPUT, doc=doc, id=lit, arity=int(a))
                        )
                    elif k == "action":
                        lines.append(
                            Line(kind=Kind.ACTION, doc=doc, id=lit, arity=int(a))
                        )
                    else:
                        raise SyntaxError(intf, l, "Bad kind: " + k)
                except SyntaxError as e:
                    raise e
                except Exception as e:
                    raise SyntaxError(intf, l, "bad line structure")

        return Interface(name, agent_doc, lines)
