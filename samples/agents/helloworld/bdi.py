import asyncio
import ast

import agentspeak
import agentspeak.runtime
import agentspeak.stdlib

from dataclasses import dataclass


@dataclass
class CatalogEntry:
    achievement: str
    arity: int
    meaning: str


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


class BDIAgent:
    def __init__(self, asl_file):

        self.published_commands = []

        self.env = agentspeak.runtime.Environment()

        # add custom actions (must occur before loading the asl file)
        self.bdi_actions = agentspeak.Actions(agentspeak.stdlib.actions)
        self.add_custom_actions(self.bdi_actions)

        with open(asl_file) as source:
            self.asp_agent=self.env.build_agent(source, self.bdi_actions)

        self.env.run()

    # this method is called by __init__
    def add_custom_actions(self, actions: agentspeak.Actions):

            @actions.add("jump",0)
            def _jump(a: agentspeak.runtime.Agent, t, i):
                print("["+ a.name +"] I jump")
                yield


            @actions.add_procedure(
                ".set_public",
                (
                        agentspeak.Literal,
                        int,
                        str
                ),
            )
            def _set_public(command:agentspeak.Literal,arity:int, doc:str):
                self.register_command(command.functor, arity, doc)

            @actions.add_procedure(".print_float", (float,))
            def _print_float(a):
                print(str(a))

    def on_receive(self, msg: AgentSpeakMessage):
        self.asp_agent.call(
            msg.trigger(),
            msg.goal_type(),
            msg.literal(),
            agentspeak.runtime.Intention(),
        )
        self.env.run()


    def register_command(self, command, arity, doc):
        """This procedure inserts an achievement with its documentation in the catalog of this agent,
        which will be able to publish it to tell others how to use it."""
        self.published_commands.append(CatalogEntry(command, arity, doc))
