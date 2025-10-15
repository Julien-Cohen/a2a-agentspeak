from dataclasses import dataclass

from a2a.types import (
    AgentCapabilities,
    AgentCard,
    AgentSkill,
)


from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore

from samples.agents.helloworld.bdi.bdi import BDIAgentExecutor


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
        capabilities=AgentCapabilities(streaming=False, push_notifications=True),
        skills=[skill_of_ASLSkill(s) for s in skills],
        supports_authenticated_extended_card=False,
    )


class AgentSpeakInterface:

    def __init__(self, name, doc, url, implementation: str):
        self.skills = []
        self.name = name
        self.doc = doc
        self.url = url
        self.implementation = implementation

    def publish_ask(self, id, doc, literal):
        self.skills.append(ASLSkill(id, doc, literal, "ask"))

    def publish_listen(self, id, doc, literal):
        self.skills.append(ASLSkill(id, doc, literal, "tell"))

    def publish_obey(self, id, doc, literal):
        self.skills.append(ASLSkill(id, doc, literal, "achieve"))

    def build_card(self):
        return build_agent_card(self.name, self.doc, self.url, self.skills)

    def build_server(self):
        request_handler = DefaultRequestHandler(
            agent_executor=BDIAgentExecutor(self.implementation),
            task_store=InMemoryTaskStore(),
        )
        return A2AStarletteApplication(
            agent_card=self.build_card(), http_handler=request_handler
        )


def from_asi_file(intf: str, url: str, impl: str):
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

        return a
