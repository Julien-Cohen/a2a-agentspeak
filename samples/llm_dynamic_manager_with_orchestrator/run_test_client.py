import logging
import threading

import httpx

from a2a.client import A2AClient, A2AClientTimeoutError
from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.types import (
    AgentCard,
    AgentCapabilities,
)
from a2a.utils import new_agent_text_message

from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.server.events import EventQueue
import uvicorn

from a2a_agentspeak.message_codec import (
    build_basic_request,
    extract_text,
)
from a2a_utils.card_holder import CardHolder, get_card


from mistral_selector_prompt import ask_llm_for_agent

spec1 = "A function to compare two words."


def neutralize_str(s):
    return "'" + s + "'"


solution_agent_urls = [
    "http://127.0.0.1:9990/",  # robot
    # "http://127.0.0.1:9991/",  # mistral manager
    # "http://127.0.0.1:9992/",  # opeanai manager
    "http://127.0.0.1:9993/",  # bad manager
]

orchestrator_agent_url = "http://127.0.0.1:9994/"

host = "127.0.0.1"
my_port = 9999
my_url = "http://" + host + ":" + str(my_port) + "/"


class ClientAgentExecutor(AgentExecutor):

    def __init__(self, orchestrator_agent: AgentCard):
        self.orchestrator_agent: AgentCard = orchestrator_agent
        self.current_selected_agent = None

    async def report_failure_to_orchestrator(self):
        async with httpx.AsyncClient(timeout=httpx.Timeout(timeout=30)) as httpx_client:

            client = A2AClient(
                httpx_client=httpx_client, agent_card=self.orchestrator_agent
            )
            request = build_basic_request(
                "tell",
                "failed(" + neutralize_str(self.current_selected_agent.url) + ")",
                my_url,
            )
            try:
                response = await client.send_message(request)
                print("Synchronous reply received: " + extract_text(response))
            except A2AClientTimeoutError:
                print("No acknowledgement received before timeout.")

    async def execute(
        self,
        context: RequestContext,
        output_event_queue: EventQueue,
    ) -> None:
        await output_event_queue.enqueue_event(
            new_agent_text_message("MESSAGE RECEIVED")
        )
        if context.get_user_input().startswith("failure"):
            print("The agent reported a failure.")
            await self.report_failure_to_orchestrator()
        else:
            print("The agent answered this: " + context.get_user_input())

    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        raise Exception("cancel not supported")


async def main() -> None:
    # Configure logging to show INFO level messages
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)  # Get a logger instance

    # Feed an orchestrator agent.
    orchestrator_agent_card = await get_card(orchestrator_agent_url)
    async with httpx.AsyncClient(timeout=httpx.Timeout(timeout=30)) as httpx_client:

        client = A2AClient(
            httpx_client=httpx_client, agent_card=orchestrator_agent_card
        )

        for other_url in solution_agent_urls:
            request = build_basic_request(
                "achieve", "register(" + neutralize_str(other_url) + ")", my_url
            )
            try:
                response = await client.send_message(request)
                print("Synchronous reply received: " + extract_text(response))
            except A2AClientTimeoutError:
                print("No acknowledgement received before timeout.")

    # 1) start an a2a server

    public_agent_card = AgentCard(
        name="Client Agent",
        description="A client agent",
        url=my_url,
        version="1.0.0",
        default_input_modes=["text"],
        default_output_modes=["text"],
        capabilities=AgentCapabilities(streaming=False, push_notifications=False),
        skills=[],
        supports_authenticated_extended_card=False,
    )

    the_client_agent_executor = ClientAgentExecutor(orchestrator_agent_card)

    request_handler = DefaultRequestHandler(
        agent_executor=the_client_agent_executor,
        task_store=InMemoryTaskStore(),
    )

    server = A2AStarletteApplication(
        agent_card=public_agent_card,
        http_handler=request_handler,
    )

    def start():
        uvicorn.run(server.build(), host=host, port=my_port)

    threading.Thread(target=start).start()
    print("-running a2a-server for client agent-")

    # 2) query the other a2a agents
    card_holder = CardHolder()
    for url in solution_agent_urls:
        await card_holder.retrieve_card_from(url)

    # 3) select the convenient agent
    if card_holder.cards is []:
        raise Exception("No agent successfully contacted.")

    try:
        i = ask_llm_for_agent(
            "Build a list of requirement from a specification.", card_holder.cards
        )
        if i < 0 or i >= len(card_holder.cards):
            raise Exception("Irregular answer from LLM")
        selected_agent_card = card_holder.cards[i]
    except Exception:
        print("LLM selection failed, switching to algorithmic selection")
        filtered = card_holder.cards_with(lambda c: "req" in c.name)
        if filtered is []:
            raise Exception("No convenient agent found")
        else:
            selected_agent_card = filtered[0]

    print("Selected : " + selected_agent_card.name)
    the_client_agent_executor.current_selected_agent = selected_agent_card

    # inform the orchestrator of the selection
    async with httpx.AsyncClient(timeout=httpx.Timeout(timeout=30)) as httpx_client:

        client = A2AClient(
            httpx_client=httpx_client, agent_card=orchestrator_agent_card
        )

        request = build_basic_request(
            "tell", "selected(" + neutralize_str(selected_agent_card.url) + ")", my_url
        )
        try:
            response = await client.send_message(request)
            print("Synchronous reply received: " + extract_text(response))
        except A2AClientTimeoutError:
            print("No acknowledgement received before timeout.")

    # talk with the selected agent
    async with httpx.AsyncClient(timeout=httpx.Timeout(timeout=30)) as httpx_client:

        client = A2AClient(httpx_client=httpx_client, agent_card=selected_agent_card)
        logger.info("A2AClient initialized.")

        # First message (tell)
        request = build_basic_request(
            "tell", "spec(" + neutralize_str(spec1) + ")", my_url
        )
        try:
            response = await client.send_message(request)
            print("Synchronous reply received: " + extract_text(response))
        except A2AClientTimeoutError:
            print("No acknowledgement received before timeout.")

        # Second message (achieve)
        request = build_basic_request("achieve", "build", my_url)
        try:
            response = await client.send_message(request)
            print("Synchronous reply received: " + extract_text(response))
        except A2AClientTimeoutError:
            print("Warning: No acknowledgement received before timeout.")


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
