from dataclasses import dataclass

from a2a.types import (
    AgentCapabilities,
    AgentExtension,
    AgentCard,
    AgentSkill,
)


from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore

from a2a_agentspeak import asi_parser
from a2a_agentspeak.asi_parser import Kind
from a2a_agentspeak.bdi import BDIAgentExecutor

import agentspeak

from a2a_agentspeak.check import check_achievement, check_input_belief, check_ask_belief


@dataclass
class ASLSkill:
    id: str
    illocution: str
    literal: str
    doc: str


def skill_of_ASLSkill(s: ASLSkill) -> AgentSkill:
    return AgentSkill(
        id=s.id,
        name=s.id + " (from ASL agent)",
        description=s.doc,
        tags=[s.illocution],
        examples=["(" + s.illocution + "," + s.literal + ")"],
    )


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
        skills=[skill_of_ASLSkill(s) for s in skills],
        supports_authenticated_extended_card=False,
    )


class AgentSpeakInterface:
    skills: list[ASLSkill]

    def __init__(self, name, doc, url, implementation: str):
        self.skills = []
        self.name = name
        self.doc = doc
        self.url = url
        self.implementation = implementation

    def publish_ask(self, id, doc, literal):
        self.skills.append(ASLSkill(id=id, doc=doc, literal=literal, illocution="ask"))

    def publish_listen(self, id, doc, literal):
        self.skills.append(ASLSkill(id=id, doc=doc, literal=literal, illocution="tell"))

    def publish_obey(self, id, doc, literal):
        self.skills.append(
            ASLSkill(id=id, doc=doc, literal=literal, illocution="achieve")
        )

    def build_card(self):
        return build_agent_card(self.name, self.doc, self.url, self.skills)

    def build_server(self, additional_callback=None):
        executor = BDIAgentExecutor(
            self.implementation, self.url, additional_callback=additional_callback
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
        reason: str

    def check(self) -> Result:
        """Check that the public interface correspond to actual triggers in implementation.
        More precisely:
         * achievements declared in the interface must have a trigger (we do not consider plans that would be added dynamically with askHow or tellHow).
         * belief literals which can be asked must occur in the implementation (we do not consider beliefs that are perceived during execution and which are not handled by the start implementation)
         * beliefs that are told to that agent must occur too in the start implementation.
        """
        LOGGER = agentspeak.get_logger(__name__)
        with open(self.implementation) as source:
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
        return self.Result(True, None)  # fixme

    def add_new_actions_callback(self, callback):
        self.new_actions_callback = callback


class InterfaceError(Exception):
    def __init__(self, token):
        self.token = token


def from_file(intf: str, impl: str, url: str) -> AgentSpeakInterface:
    i: asi_parser.Interface = asi_parser.read_file(intf)

    a: AgentSpeakInterface = AgentSpeakInterface(i.name, i.doc, url, impl)

    for l in i.lines:
        if l.kind == Kind.BELIEF:
            a.publish_ask(l.id, l.doc, l.id)
        elif l.kind == Kind.INPUT:
            a.publish_listen(l.id, l.doc, l.id)
        elif l.kind == Kind.ACTION:
            a.publish_obey(l.id, l.doc, l.id)
        else:
            assert False

    r = a.check()
    if not (r.success):
        raise InterfaceError(r.reason)
    else:
        return a
