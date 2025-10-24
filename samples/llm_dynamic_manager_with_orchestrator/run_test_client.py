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
from a2a_agentspeak.skill import asl_skill_of_a2a_skill
from a2a_utils.card_holder import CardHolder, get_card


from mistral_selector_prompt import ask_llm_for_agent
from context import build_url

spec1 = "A function to compare two words."


def neutralize_str(s):
    return "'" + s + "'"


solution_agent_urls = [
    "http://127.0.0.1:9990/",  # robot
    "http://127.0.0.1:9992/",  # opeanai requirement manager
    "http://127.0.0.1:9993/",  # bad requirement manager
    "http://127.0.0.1:9991/",  # mistral requirement manager
    "http://127.0.0.1:9995/",  # naive requirement manager
]

orchestrator_agent_url = "http://127.0.0.1:9980/"

host = "127.0.0.1"
my_port = 9999
my_url = build_url(host, my_port)


async def send_request(client, request):
    try:
        response = await client.send_message(request)
        print("Synchronous reply received: " + str(extract_text(response)))
    except A2AClientTimeoutError:
        print("No acknowledgement received before timeout.")


def is_requirement_manager(card: AgentCard) -> bool:
    skills = [asl_skill_of_a2a_skill(s) for s in card.skills]
    has_spec_skill = False
    for s in skills:
        if s.literal == "spec" and s.arity == 1 and s.illocution == "tell":
            has_spec_skill = True
    has_build_skill = False
    for s in skills:
        if s.literal == "build" and s.arity == 0 and s.illocution == "achieve":
            has_build_skill = True
    return has_spec_skill and has_build_skill


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
            await send_request(client, request)

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
            await send_request(client, request)

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

    def srv_start():
        uvicorn.run(server.build(), host=host, port=my_port)

    # spawn the server to continue the script.
    threading.Thread(target=srv_start).start()
    print("-running a2a-server for client agent-")

    # 2) query the other a2a agents
    card_holder = CardHolder()
    for url in solution_agent_urls:
        await card_holder.retrieve_card_from(url)

    # 3) select the convenient agent
    if card_holder.cards is []:
        raise Exception("No agent successfully contacted.")

    for card in card_holder.cards:
        if is_requirement_manager(card):
            async with httpx.AsyncClient(
                timeout=httpx.Timeout(timeout=30)
            ) as httpx_client:
                client = A2AClient(
                    httpx_client=httpx_client, agent_card=orchestrator_agent_card
                )
                request = build_basic_request(
                    "tell",
                    "has_requirement_manager_interface("
                    + neutralize_str(other_url)
                    + ")",
                    my_url,
                )
                await send_request(client, request)

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
        await send_request(client, request)

    async with httpx.AsyncClient(timeout=httpx.Timeout(timeout=30)) as httpx_client:
        client = A2AClient(
            httpx_client=httpx_client, agent_card=orchestrator_agent_card
        )

        request = build_basic_request(
            "tell", "spec(" + neutralize_str(spec1) + ")", my_url
        )
        await send_request(client, request)

    async with httpx.AsyncClient(timeout=httpx.Timeout(timeout=30)) as httpx_client:
        client = A2AClient(
            httpx_client=httpx_client, agent_card=orchestrator_agent_card
        )

        request = build_basic_request("achieve", "build", my_url)
        await send_request(client, request)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
