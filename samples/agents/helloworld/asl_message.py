import agentspeak
import ast
from dataclasses import dataclass

def lit_of_str(s: str) -> agentspeak.Literal:
    l = s.split(sep="(", maxsplit=1)
    symb = l[0]
    if len(l) == 1:
        return agentspeak.Literal(symb)
    else:
        rest = l[1]
        assert rest.endswith(")")
        args = rest.removesuffix(")")
        if args.startswith("_X_"):
            return agentspeak.Literal(symb, agentspeak.Var)
        else:
            t = ast.literal_eval(args)
            if isinstance(t, tuple):
                return agentspeak.Literal(symb, t)
            else:
                return agentspeak.Literal(symb, (t,))


def strplan(p: str):
    return agentspeak.Literal("plain_text", (p,))


def add_source(lit: agentspeak.Literal, s: str) -> agentspeak.Literal:
    return lit.with_annotation(agentspeak.Literal("source", (agentspeak.Literal(s),)))


@dataclass
class AgentSpeakMessage:
    illocution: str
    content: str
    sender: str

    def goal_type(self) -> agentspeak.GoalType:
        _i = self.illocution
        if _i == "tell" or _i == "untell":
            return agentspeak.GoalType.belief
        elif _i == "achieve" or _i == "unachieve":
            return agentspeak.GoalType.achievement
        elif _i == "tellHow" or _i == "untellHow":
            return agentspeak.GoalType.tellHow
        else:
            raise RuntimeError("Illocution not supported: " + _i)

    def trigger(self) -> agentspeak.Trigger:
        _i = self.illocution
        if _i == "tell" or _i == "achieve" or _i == "tellHow":
            return agentspeak.Trigger.addition
        elif _i == "untell" or _i == "unachieve" or _i == "untellHow":
            return agentspeak.Trigger.removal
        else:
            raise RuntimeError("Illocution not supported: " + _i)

    def literal(self) -> agentspeak.Literal:
        _i = self.illocution
        _c = self.content
        _s = self.sender
        if _i in ["tell", "untell", "achieve", "unachieve"]:
            return add_source(lit_of_str(_c).freeze({}, {}), _s)
        elif _i in ["tellHow", "untellHow"]:
            return add_source(strplan(_c).freeze({}, {}), _s)
        else:
            raise RuntimeError("Illocution not supported: " + _i)

