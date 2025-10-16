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
            self.implementation, additional_callback=additional_callback
        )

        request_handler = DefaultRequestHandler(
            agent_executor=executor,
            task_store=InMemoryTaskStore(),
        )
        return A2AStarletteApplication(
            agent_card=self.build_card(), http_handler=request_handler
        )

    def check(self) -> bool:
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
                    print(s.literal + " invalidated.")
                    return False
                else:
                    print("Check achievement " + s.literal + " ok.")
            elif s.illocution == "tell":
                if not check_input_belief(s.literal, ast_agent):
                    print(s.literal + " invalidated.")
                    return False
                else:
                    print("Check tell belief " + s.literal + " ok.")

            elif s.illocution == "ask":
                if not check_ask_belief(s.literal, ast_agent):
                    print(s.literal + " invalidated.")
                    return False
                else:
                    print("Check ask belief " + s.literal + " ok.")
            else:
                print(
                    "WARNING: implementation not checked against skill in the interface: "
                    + str(s)
                    + " (FIXME)"
                )
        return True  # fixme

    def add_new_actions_callback(self, callback):
        self.new_actions_callback = callback


def from_file(intf: str, impl: str, url: str) -> AgentSpeakInterface:
    with open(intf, "r") as f:
        l = f.readline()
        assert l.startswith("name = ")
        name = l.removeprefix("name = ")

        l = f.readline()
        assert l.startswith("doc = ")
        doc = l.removeprefix("doc = ")

        a: AgentSpeakInterface = AgentSpeakInterface(name, doc, url, impl)

        for l in f:

            if l == "\n":
                pass
            elif l.startswith("belief"):
                [_, b, c] = l.split(" : ")
                a.publish_ask(b, c, b)
            elif l.startswith("input"):
                [_, b, c] = l.split(" : ")
                a.publish_listen(b, c, b)
            elif l.startswith("action"):
                [_, b, c] = l.split(" : ")
                a.publish_obey(b, c, b)
            else:
                print("line ignored: " + l)

        if not (a.check()):
            raise Exception(
                "The specified interface does not match the specified implementation."
            )
        else:
            return a
