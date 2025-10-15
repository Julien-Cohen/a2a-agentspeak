import threading
import uvicorn

from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import (
    AgentCapabilities,
    AgentCard,
    AgentSkill,
)
from bdi import BDIAgentExecutor


if __name__ == '__main__':

    number_provider_skill = AgentSkill(
        id='number-provider',
        name='provide a number',
        description='Returns a number which depends on an internal state. Ask secret to get the number',
        tags=['secret'],
        examples=['(ask,secret)'],
    )

    ready_skill = AgentSkill(
        id='ready-skill',
        name='get ready',
        description='Change internal state on ready',
        tags=['ready'],
        examples=['(tell, ready)'],
    )

    ping_skill = AgentSkill(
        id='ping-skill',
        name='handle ping',
        description='handle a ping request',
        tags=['ping'],
        examples=['(achieve, ping)'],
    )

    # This will be the public-facing agent card
    public_agent_card = AgentCard(
        name='State Agent',
        description='An agent with a state that returns a number on request. (Understands AgentSpeak messages)',
        url='http://localhost:9999/',
        version='1.0.0',
        default_input_modes=['text'],
        default_output_modes=['text'],
        capabilities=AgentCapabilities(streaming=False, push_notifications=True),
        skills=[number_provider_skill, ready_skill, ping_skill],
        supports_authenticated_extended_card=False,
    )


    request_handler = DefaultRequestHandler(
        agent_executor=BDIAgentExecutor("state.asl"),
        task_store=InMemoryTaskStore(),
    )

    server = A2AStarletteApplication(
        agent_card=public_agent_card,
        http_handler=request_handler,
    )

    def start():
        uvicorn.run(server.build(), host='0.0.0.0', port=9999)

    threading.Thread(target=start).start()
    print("-running a2a-server for state agent-")
