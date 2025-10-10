import uvicorn

from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import (
    AgentCapabilities,
    AgentCard,
    AgentSkill,
)
from agent_executor import (
    StateAgentExecutor,  # type: ignore[import-untyped]
)


if __name__ == '__main__':

    number_provider_skill = AgentSkill(
        id='number-provider',
        name='provide a number',
        description='Returns a different number depending on an internal state that can be changed. Achieve ping to check connection. Tell ready to change state. Ask get to get the number',
        tags=['get', 'state'],
        examples=['(achieve, ping)', '(tell, ready)', '(ask,secret)'],
    )



    # This will be the public-facing agent card
    public_agent_card = AgentCard(
        name='State Agent',
        description='An agent with a state that returns a number on request. (Understands AgentSpeak messages)',
        url='http://localhost:9999/',
        version='1.0.0',
        default_input_modes=['text'],
        default_output_modes=['text'],
        capabilities=AgentCapabilities(streaming=True, push_notifications=True),
        skills=[number_provider_skill],
        supports_authenticated_extended_card=True,
    )


    request_handler = DefaultRequestHandler(
        agent_executor=StateAgentExecutor(),
        task_store=InMemoryTaskStore(),
    )

    server = A2AStarletteApplication(
        agent_card=public_agent_card,
        http_handler=request_handler,
    )

    uvicorn.run(server.build(), host='0.0.0.0', port=9999)
