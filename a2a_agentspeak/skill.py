from dataclasses import dataclass

from a2a.types import AgentSkill


@dataclass
class ASLSkill:
    id: str
    illocution: str
    literal: str
    arity: int
    doc: str

    def has_interface(self, illoc: str, lit: str, ar: int) -> bool:
        return self.illocution == illoc and self.literal == lit and self.arity == ar


def pretty_print_example(s: ASLSkill):
    return "(" + s.illocution + "," + s.literal + ")"


def parse_example(s: str) -> tuple[str, str]:
    s2 = s.removeprefix("(").removesuffix(")")
    (a, b) = s2.split(",")
    return a, b


def encode_arity(a: int) -> str:
    return "(needs " + str(a) + " parameter" + ("s" if a > 1 else "") + ")"


def decode_arity(s: str) -> int:
    l = s.split(" ")
    s1 = l[-2]
    return int(s1)


def a2a_skill_of_asl_skill(s: ASLSkill) -> AgentSkill:
    return AgentSkill(
        id=s.id,
        name=s.id + " (from ASL agent)",
        description=s.doc + " " + encode_arity(s.arity),
        tags=[s.literal],
        examples=[pretty_print_example(s)],
    )


def asl_skill_of_a2a_skill(s: AgentSkill) -> ASLSkill:
    (a, b) = parse_example(s.examples[0])
    return ASLSkill(
        id=s.id,
        illocution=a,
        literal=b,
        arity=decode_arity(s.description),
        doc=s.description,
    )
