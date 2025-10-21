import asyncio

import httpx

import agentspeak
import agentspeak.runtime
import agentspeak.stdlib

from dataclasses import dataclass

from a2a.client import (
    A2ACardResolver,
    A2AClient,
    A2AClientJSONError,
    A2AClientHTTPError,
)
from a2a.server.events import EventQueue
from a2a.utils import new_agent_text_message

from a2a_agentspeak.asl_message import AgentSpeakMessage

from a2a.server.agent_execution import AgentExecutor, RequestContext

import a2a_agentspeak.message_codec as message_tools
from a2a_agentspeak.message_codec import asl_of_a2a

from a2a_agentspeak.check import check_illoc
from a2a_agentspeak.tool import Tool


@dataclass
class CatalogEntry:
    achievement: str
    arity: int
    meaning: str


async def do_send(to_url: str, illoc: str, content: str, my_url: str):
    async with httpx.AsyncClient() as httpx_client:

        resolver = A2ACardResolver(
            httpx_client=httpx_client,
            base_url=to_url,
        )

        try:
            _public_card = await resolver.get_agent_card()

            client = A2AClient(
                # httpx_client=httpx_client, agent_card=_public_card
                httpx_client=httpx_client,
                url=to_url,
            )

            request = message_tools.build_basic_request(illoc, content, my_url)
            response = await client.send_message(request)
            print(
                "Message sent and synchronous answer received: "
                + message_tools.extract_text(response)
            )

        except A2AClientJSONError as e:
            print("---FAIL---: ASL agent failed to send (JSON). " + str(e))
        except A2AClientHTTPError as e:
            print("---FAIL---: ASL agent failed to send (HTTP). " + str(e))

        except Exception as e:
            print("---FAIL---: ASL agent failed to send (other). " + str(e))


async def reply(output_event_queue: EventQueue, r: str):
    await output_event_queue.enqueue_event(new_agent_text_message(r))


class BDIAgent:
    def __init__(self, asl_file: str, url: str, additional_tools: set[Tool]):
        self.my_url = url

        self.env = agentspeak.runtime.Environment()

        # add custom actions (must occur before loading the asl file)
        self.bdi_actions = agentspeak.Actions(agentspeak.stdlib.actions)
        self.add_custom_actions()
        for t in additional_tools:
            self.add_tool(t)

        with open(asl_file) as source:
            self.asp_agent = self.env.build_agent(source, self.bdi_actions)

        self.env.run()

    # this method is called by __init__
    def add_custom_actions(self):
        actions = self.bdi_actions

        @actions.add("jump", 0)
        def _jump(a: agentspeak.runtime.Agent, t, i):
            print("[" + a.name + "] I jump")
            yield

        @actions.add_procedure(".print_float", (float,))
        def _print_float(a):
            print(str(a))

        @actions.add_procedure(
            ".send", (agentspeak.Literal, agentspeak.Literal, agentspeak.Literal)
        )
        def _send_to_url(
            u: agentspeak.Literal, illoc: agentspeak.Literal, t: agentspeak.Literal
        ):
            assert check_illoc(illoc)
            asyncio.create_task(do_send(str(u), str(illoc), str(t), self.my_url))

        @actions.add_procedure(
            ".send_str", (str, agentspeak.Literal, agentspeak.Literal)
        )
        def _send_to_url_str(u: str, illoc: agentspeak.Literal, t: agentspeak.Literal):
            assert check_illoc(illoc)
            asyncio.create_task(do_send(u, str(illoc), str(t), self.my_url))

    def add_tool(self, tool: Tool):
        if tool.kind == "function":
            self.bdi_actions.add_function(
                tool.action_name, tool.arity, tool.implementation
            )
        else:
            print("This kind of tool is not supported yet: " + tool.kind)

    def process_message(self, msg: AgentSpeakMessage):
        """Process tell, and achieve requests following the AgentSpeak defined behavior."""
        self.asp_agent.call(
            msg.trigger(),
            msg.goal_type(),
            msg.literal(),
            agentspeak.runtime.Intention(),
        )
        self.env.run()

    def extract_from_beliefs(self, a: str):
        r = self.asp_agent.beliefs[(a, 1)]  # fixme : arity
        assert isinstance(r, set)
        if r == set():
            return None
        else:
            tmp = next(iter(r))
            assert isinstance(tmp, agentspeak.Literal)
            assert tmp.functor == a
            assert isinstance(tmp.args, tuple)
            return tmp.args[0]

    def get_belief(self, s: str) -> str | None:
        r = self.extract_from_beliefs(s)
        if r is not None:
            return str(r)
        else:
            return None

    async def preprocess_message(
        self, m: AgentSpeakMessage, output_event_queue: EventQueue
    ):
        """Answer to a message depending on the nature of a message:
        - reply with the required information for ask illocutions
        - reply with an ackowledgement and process the request otherwise.
        """
        if m.illocution == "achieve":
            self.process_message(m)
            await reply(output_event_queue, "Achieve received")
        elif m.illocution == "tell":
            self.process_message(m)
            await reply(output_event_queue, "Tell received.")
        elif (
            m.illocution == "ask"
        ):  # fixme : also check that the requested belief is public.
            """in A2A, each received message has an event queue to post responses.
            This is not the case in AgentSpeak.
            Here we add an illocution for requests that need an answer : ask"""
            result = self.get_belief(m.content)
            if result is not None:
                await reply(output_event_queue, result)
            else:
                pass  # do not reply
        else:
            print("Cannot manage illocution " + m.illocution)


class BDIAgentExecutor(AgentExecutor):

    def __init__(
        self,
        asl_file: str,
        public_literals: list[str],
        url: str,
        additional_tools,
    ):
        self.bdi_agent = BDIAgent(asl_file, url, additional_tools=additional_tools)
        self.public_literals = public_literals

    def is_public(self, lit: str) -> bool:
        return lit in self.public_literals

    async def execute(
        self,
        context: RequestContext,
        output_event_queue: EventQueue,
    ) -> None:
        m: AgentSpeakMessage = asl_of_a2a(context)
        l = str(m.literal().functor)
        if not (self.is_public(l)):
            await reply(
                output_event_queue,
                "The literal " + l + " is not public it this agent.",
            )
        else:
            await self.bdi_agent.preprocess_message(m, output_event_queue)

    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        raise Exception("cancel not supported")
