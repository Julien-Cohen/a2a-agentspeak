from dataclasses import dataclass

from a2a.types import (
    AgentCapabilities,
    AgentCard,
    AgentSkill,
)


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
