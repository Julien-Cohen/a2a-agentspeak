import logging
import threading

from typing import Any
from uuid import uuid4

import httpx

from a2a.client import A2ACardResolver, A2AClient
from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.types import (
    AgentCard,
    AgentCapabilities,
    MessageSendParams,
    SendMessageRequest,
    SendMessageResponse,
    SendMessageSuccessResponse, Message, MessageSendConfiguration,
    PushNotificationConfig
)
from a2a.utils.constants import (
    AGENT_CARD_WELL_KNOWN_PATH,
)

from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.server.events import EventQueue
import uvicorn

def extract_text (response:SendMessageResponse):
    if isinstance(response, SendMessageResponse):
        if isinstance(response.root, SendMessageSuccessResponse):
            if isinstance(response.root.result, Message):
                return response.root.result.parts[0].root.text
    # otherwise
    return response.model_dump(mode='json', exclude_none=True)


def build_basic_message(t: str, c: MessageSendConfiguration) -> dict[str, Any]:
    return {
        'message': {
            'role': 'user',
            'parts': [
                {'kind': 'text', 'text': t}
            ],
            'messageId': uuid4().hex,
        },
        'configuration': c
    }


def build_basic_request(t: str, c: MessageSendConfiguration) -> SendMessageRequest:
    return SendMessageRequest(id=str(uuid4()), params=MessageSendParams(**build_basic_message(t, c)))

class ClientAgentExecutor(AgentExecutor):
    async def execute(
        self,
        context: RequestContext,
        output_event_queue: EventQueue,
    ) -> None:
        print("EXECUTE")

    async def cancel(
        self, context: RequestContext, event_queue: EventQueue
    ) -> None:
        raise Exception('cancel not supported')

async def main() -> None:
    # Configure logging to show INFO level messages
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)  # Get a logger instance


    other_agent_url = 'http://localhost:9999'
    my_url = 'http://localhost:9998'

    # 1) start an a2a server

    public_agent_card = AgentCard(
        name='Client Agent',
        description='A client agent',
        url=my_url,
        version='1.0.0',
        default_input_modes=['text'],
        default_output_modes=['text'],
        capabilities=AgentCapabilities(streaming=False, push_notifications=False),
        skills=[],
        supports_authenticated_extended_card=False,
    )

    request_handler = DefaultRequestHandler(
        agent_executor=ClientAgentExecutor(),
        task_store=InMemoryTaskStore(),
    )

    server = A2AStarletteApplication(
        agent_card=public_agent_card,
        http_handler=request_handler,
    )

    def start():
        uvicorn.run(server.build(), host='0.0.0.0', port=9998)

    threading.Thread(target=start).start()
    print("-running a2a-server for client agent-")

    # 2) query the other a2a agent

    async with httpx.AsyncClient() as httpx_client:
        # Initialize A2ACardResolver
        resolver = A2ACardResolver(
            httpx_client=httpx_client,
            base_url=other_agent_url,
            # agent_card_path uses default, extended_agent_card_path also uses default
        )

        # Fetch Public Agent Card and Initialize Client
        final_agent_card_to_use: AgentCard | None = None
        try:
            logger.info(
                f'Attempting to fetch public agent card from: {other_agent_url}{AGENT_CARD_WELL_KNOWN_PATH}'
            )
            _public_card = (
                await resolver.get_agent_card()
            )  # Fetches from default public path
            logger.info('Successfully fetched public agent card:')
            final_agent_card_to_use = _public_card
            logger.info(
                '\nUsing PUBLIC agent card for client initialization (default).'
            )

        except Exception as e:
            raise RuntimeError(
                'Failed to fetch the public agent card. Cannot continue.'
            ) from e

        client = A2AClient(
            httpx_client=httpx_client, agent_card=final_agent_card_to_use
        )
        logger.info('A2AClient initialized.')

        config = MessageSendConfiguration(push_notification_config=PushNotificationConfig(url=my_url))

        # First message (achieve)
        request = build_basic_request('(achieve,ping)', config)
        response = await client.send_message(request)
        print ("Answer: " + extract_text(response))

        # Another message (ask)
        request = build_basic_request('(ask,secret)', config)
        response = await client.send_message(request)
        print("Answer: " + extract_text(response))

        # Another message (tell)
        request = build_basic_request('(tell,ready)', config)
        response = await client.send_message(request)
        print ("Answer: " + extract_text(response))

        # Another message (achieve)
        request = build_basic_request('(achieve,ping)', config)
        response = await client.send_message(request)
        print ("Answer: " + extract_text(response))

        # Another message (ask)
        request = build_basic_request('(ask,secret)', config)
        response = await client.send_message(request)
        print("Answer: " + extract_text(response))




if __name__ == '__main__':
    import asyncio

    asyncio.run(main())
