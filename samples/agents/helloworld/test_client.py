import logging

from typing import Any
from uuid import uuid4

import httpx

from a2a.client import A2ACardResolver, A2AClient
from a2a.types import (
    AgentCard,
    MessageSendParams,
    SendMessageRequest,
    SendMessageResponse,
    SendMessageSuccessResponse, Message, MessageSendConfiguration,
    PushNotificationConfig
)
from a2a.utils.constants import (
    AGENT_CARD_WELL_KNOWN_PATH,
    EXTENDED_AGENT_CARD_PATH,
)

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

async def main() -> None:
    # Configure logging to show INFO level messages
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)  # Get a logger instance


    other_agent_url = 'http://localhost:9999'
    my_url = 'http://localhost:9998'

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
            logger.info(
                _public_card.model_dump_json(indent=2, exclude_none=True)
            )
            final_agent_card_to_use = _public_card
            logger.info(
                '\nUsing PUBLIC agent card for client initialization (default).'
            )

            if _public_card.supports_authenticated_extended_card:
                logger.info(
                        f'\nPublic card supports authenticated extended card.'
                )

            elif (
                _public_card
            ):  # supports_authenticated_extended_card is False or None
                logger.info(
                    '\nPublic card does not indicate support for an extended card. Using public card.'
                )

        except Exception as e:
            logger.error(
                f'Critical error fetching public agent card: {e}', exc_info=True
            )
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
