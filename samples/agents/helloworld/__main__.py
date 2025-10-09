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
    # --8<-- [start:AgentSkill]
    number_provider_skill = AgentSkill(
        id='number-provider',
        name='provide a number',
        description='Returns a different number depending on an internal state that can be changed. Achieve ping to check connection. Tell ready to change state. Ask get to get the number',
        tags=['get', 'state'],
        examples=['(achieve, ping)', '(tell, ready)', '(ask,get)'],
    )
    # --8<-- [end:AgentSkill]

    extended_skill = AgentSkill(
        id='super_hello_world',
        name='Returns a SUPER Hello World',
        description='A more enthusiastic greeting, only for authenticated users.',
        tags=['hello world', 'super', 'extended'],
        examples=['super hi', 'give me a super hello'],
    )

    # --8<-- [start:AgentCard]
    # This will be the public-facing agent card
    public_agent_card = AgentCard(
        name='State Agent',
        description='An agent with a state that returns a number on request. (Understands AgentSpeak messages)',
        url='http://localhost:9999/',
        version='1.0.0',
        default_input_modes=['text'],
        default_output_modes=['text'],
        capabilities=AgentCapabilities(streaming=True),
        skills=[number_provider_skill],  # Only the basic skill for the public card
        supports_authenticated_extended_card=True,
    )
    # --8<-- [end:AgentCard]

    # This will be the authenticated extended agent card
    # It includes the additional 'extended_skill'
    specific_extended_agent_card = public_agent_card.model_copy(
        update={
            'name': 'State Ping Agent - Extended Edition',  # Different name for clarity
            'description': 'The full-featured state ping agent for authenticated users.',
            'version': '1.0.1',  # Could even be a different version
            # Capabilities and other fields like url, default_input_modes, default_output_modes,
            # supports_authenticated_extended_card are inherited from public_agent_card unless specified here.
            'skills': [
                number_provider_skill,
                extended_skill,
            ],  # Both skills for the extended card
        }
    )

    request_handler = DefaultRequestHandler(
        agent_executor=StateAgentExecutor(),
        task_store=InMemoryTaskStore(),
    )

    server = A2AStarletteApplication(
        agent_card=public_agent_card,
        http_handler=request_handler,
        extended_agent_card=specific_extended_agent_card,
    )

    uvicorn.run(server.build(), host='0.0.0.0', port=9999)
