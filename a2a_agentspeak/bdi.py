import asyncio

import a2a_agentspeak.message_tools as message_tools

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

from a2a_agentspeak.conversion import asl_of_a2a


@dataclass
class CatalogEntry:
    achievement: str
    arity: int
    meaning: str


async def do_send(url: str, content: str):
    async with httpx.AsyncClient() as httpx_client:

        resolver = A2ACardResolver(
            httpx_client=httpx_client,
            base_url=url,
        )

        try:
            _public_card = await resolver.get_agent_card()

            client = A2AClient(
                # httpx_client=httpx_client, agent_card=_public_card
                httpx_client=httpx_client,
                url=url,
            )

            request = message_tools.build_basic_request(content, None)
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
    def __init__(self, asl_file):

        self.published_commands = []

        self.env = agentspeak.runtime.Environment()

        # add custom actions (must occur before loading the asl file)
        self.bdi_actions = agentspeak.Actions(agentspeak.stdlib.actions)
        self.add_custom_actions(self.bdi_actions)

        with open(asl_file) as source:
            self.asp_agent = self.env.build_agent(source, self.bdi_actions)

        self.env.run()

    # this method is called by __init__
    def add_custom_actions(self, actions: agentspeak.Actions):

        @actions.add("jump", 0)
        def _jump(a: agentspeak.runtime.Agent, t, i):
            print("[" + a.name + "] I jump")
            yield

        @actions.add_procedure(
            ".set_public",
            (agentspeak.Literal, int, str),
        )
        def _set_public(command: agentspeak.Literal, arity: int, doc: str):
            self.register_command(command.functor, arity, doc)

        @actions.add_procedure(".print_float", (float,))
        def _print_float(a):
            print(str(a))

        @actions.add_procedure(".send", (agentspeak.Literal, agentspeak.Literal, str))
        def _send_to_url(u: agentspeak.Literal, illoc, t: str):
            # fixme : illoc ignored
            asyncio.create_task(do_send(str(u), t))

    def process_message(self, msg: AgentSpeakMessage):
        """Process tell, and achieve requests following the AgentSpeak defined behavior."""
        self.asp_agent.call(
            msg.trigger(),
            msg.goal_type(),
            msg.literal(),
            agentspeak.runtime.Intention(),
        )
        self.env.run()

    def register_command(self, command, arity, doc):
        """This procedure inserts an achievement with its documentation in the catalog of this agent,
        which will be able to publish it to tell others how to use it."""
        self.published_commands.append(CatalogEntry(command, arity, doc))

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

    def __init__(self, asl_file: str):
        self.bdi_agent = BDIAgent(asl_file)

    async def execute(
        self,
        context: RequestContext,
        output_event_queue: EventQueue,
    ) -> None:
        m: AgentSpeakMessage = asl_of_a2a(context)
        await self.bdi_agent.preprocess_message(m, output_event_queue)

    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        raise Exception("cancel not supported")
