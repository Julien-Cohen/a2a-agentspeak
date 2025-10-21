from dataclasses import dataclass

from a2a.types import (
    AgentCapabilities,
    AgentExtension,
    AgentCard,
)


from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore

from a2a_agentspeak import asi_parser
from a2a_agentspeak.asi_parser import Kind
from a2a_agentspeak.bdi import BDIAgentExecutor

import agentspeak

from a2a_agentspeak.check import check_achievement, check_input_belief, check_ask_belief
from a2a_agentspeak.skill import ASLSkill, a2a_skill_of_asl_skill

PROTOCOL_URI = "https://github.com/Julien-Cohen/a2a-agentspeak/blob/main/a2a_agentspeak/MOSAICO_A2A_AGENTSPEAK_PROTOCOL"
EXTENSION = AgentExtension(
    uri=PROTOCOL_URI, description="MOSAICO A2A AgentSpeak", required=True
)


def build_agent_card(
    name: str, doc: str, url: str, skills: list[ASLSkill]
) -> AgentCard:

    return AgentCard(
        name=name,
        description=doc,
        url=url,
        version="1.0.0",
        default_input_modes=["text"],
        default_output_modes=["text"],
        capabilities=AgentCapabilities(
            streaming=False,
            push_notifications=True,
            extensions=[EXTENSION],
        ),
        skills=[a2a_skill_of_asl_skill(s) for s in skills],
        supports_authenticated_extended_card=False,
    )


class AgentSpeakInterface:
    skills: list[ASLSkill]

    def __init__(self, name, doc, url, implementation: str, additional_tools):
        self.skills = []
        self.name = name
        self.doc = doc
        self.url = url
        self.implementation_file = implementation
        self.additional_tools = additional_tools

    def publish_ask(self, id, doc, literal, arity):
        self.skills.append(
            ASLSkill(id=id, doc=doc, literal=literal, arity=arity, illocution="ask")
        )

    def publish_listen(self, id, doc, literal, arity):
        self.skills.append(
            ASLSkill(id=id, doc=doc, literal=literal, arity=arity, illocution="tell")
        )

    def publish_obey(self, id, doc, literal, arity):
        self.skills.append(
            ASLSkill(id=id, doc=doc, literal=literal, arity=arity, illocution="achieve")
        )

    def public_literals(self):
        return [s.literal for s in self.skills]

    def build_card(self):
        return build_agent_card(self.name, self.doc, self.url, self.skills)

    def build_server(self):
        executor = BDIAgentExecutor(
            self.implementation_file,
            self.public_literals(),
            self.url,
            additional_tools=self.additional_tools,
        )

        request_handler = DefaultRequestHandler(
            agent_executor=executor,
            task_store=InMemoryTaskStore(),
        )
        return A2AStarletteApplication(
            agent_card=self.build_card(), http_handler=request_handler
        )

    @dataclass
    class Result:
        success: bool
        reason: str | None

    def check(self) -> Result:
        """Check that the public interface correspond to actual triggers in implementation.
        More precisely:
         * achievements declared in the interface must have a trigger (we do not consider plans that would be added dynamically with askHow or tellHow).
         * belief literals which can be asked must occur in the implementation (we do not consider beliefs that are perceived during execution and which are not handled by the start implementation)
         * beliefs that are told to that agent must occur too in the start implementation.
        """
        LOGGER = agentspeak.get_logger(__name__)
        with open(self.implementation_file) as source:
            log = agentspeak.Log(LOGGER, 3)
            tokens = agentspeak.lexer.TokenStream(source, log)
            ast_agent: agentspeak.parser.ASTAgent = agentspeak.parser.parse(
                source.name, tokens, log
            )
            log.throw()

        # exists
        for s in self.skills:
            if s.illocution == "achieve":
                if not check_achievement(s.literal, ast_agent):
                    return self.Result(False, s.literal)
            elif s.illocution == "tell":
                if not check_input_belief(s.literal, ast_agent):
                    return self.Result(False, s.literal)
            elif s.illocution == "ask":
                if not check_ask_belief(s.literal, ast_agent):
                    return self.Result(False, s.literal)
            else:
                print(
                    "WARNING: implementation not checked against skill in the interface: "
                    + str(s)
                    + " (FIXME)"
                )
        return self.Result(True, None)

    def add_new_actions_callback(self, callback):
        self.new_actions_callback = callback


class InterfaceError(Exception):
    def __init__(self, token):
        self.token = token


def from_file(intf: str, impl: str, url: str, tools=frozenset()) -> AgentSpeakInterface:
    i: asi_parser.Interface = asi_parser.read_file(intf)

    a: AgentSpeakInterface = AgentSpeakInterface(i.name, i.doc, url, impl, tools)

    for l in i.lines:
        if l.kind == Kind.BELIEF:
            a.publish_ask(id=l.id, doc=l.doc, literal=l.id, arity=l.arity)
        elif l.kind == Kind.INPUT:
            a.publish_listen(id=l.id, doc=l.doc, literal=l.id, arity=l.arity)
        elif l.kind == Kind.ACTION:
            a.publish_obey(id=l.id, doc=l.doc, literal=l.id, arity=l.arity)
        else:
            assert False

    r = a.check()
    if not r.success:
        raise InterfaceError(r.reason)
    else:
        return a
