import logging

import httpx
from a2a.client import A2ACardResolver
from a2a.types import AgentCard
from a2a.utils.constants import AGENT_CARD_WELL_KNOWN_PATH


async def get_card(url: str) -> AgentCard:
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)  # Get a logger instance

    async with httpx.AsyncClient(timeout=httpx.Timeout(timeout=30)) as httpx_client:
        # Initialize A2ACardResolver
        resolver = A2ACardResolver(
            httpx_client=httpx_client,
            base_url=url,
        )

        logger.info(
            f"Attempting to fetch public agent card from: {url}{AGENT_CARD_WELL_KNOWN_PATH}"
        )
        _public_card: AgentCard = (
            await resolver.get_agent_card()
        )  # Fetches from default public path
        return _public_card


class CardHolder:

    cards: list[AgentCard]

    def __init__(self):
        self.cards = []

    async def retrieve_card_from(self, url) -> bool:
        logging.basicConfig(level=logging.INFO)
        logger = logging.getLogger(__name__)  # Get a logger instance

        try:
            _public_card: AgentCard = await get_card(url)

            logger.info("Successfully fetched public agent card:")
            self.cards.append(_public_card)
            logger.info(
                "\nUsing PUBLIC agent card for client initialization (default)."
            )
            return True

        except Exception:
            logger.info("Client failed to fetch the public agent card.")
            return False

    def cards_with(self, predicate):
        return [c for c in self.cards if predicate(c)]
