import asyncio

import message_tools

import httpx

import agentspeak
import agentspeak.runtime
import agentspeak.stdlib

from dataclasses import dataclass

from a2a.client import A2ACardResolver, A2AClient, A2AClientJSONError, A2AClientHTTPError

import asl_message

@dataclass
class CatalogEntry:
    achievement: str
    arity: int
    meaning: str


async def do_send(url:str):
    async with httpx.AsyncClient() as httpx_client:

        resolver = A2ACardResolver(
            httpx_client=httpx_client,
            base_url=url,
        )

        try:
            _public_card = (
                await resolver.get_agent_card()
            )

            client = A2AClient(
                #httpx_client=httpx_client, agent_card=_public_card
                httpx_client = httpx_client, url = url
            )

            request = message_tools.build_basic_request('PING', None)
            response = await client.send_message(request)
            print("Answer received from PING: " + message_tools.extract_text(response))

        except A2AClientJSONError as e:
            print('---FAIL---: ASL agent failed to send (JSON). ' + str(e))
        except A2AClientHTTPError as e:
            print('---FAIL---: ASL agent failed to send (HTTP). ' + str(e))

        except Exception as e:
            print('---FAIL---: ASL agent failed to send (other). ' + str(e))


class BDIAgent:
    def __init__(self, asl_file):

        self.published_commands = []

        self.env = agentspeak.runtime.Environment()

        # add custom actions (must occur before loading the asl file)
        self.bdi_actions = agentspeak.Actions(agentspeak.stdlib.actions)
        self.add_custom_actions(self.bdi_actions)

        with open(asl_file) as source:
            self.asp_agent=self.env.build_agent(source, self.bdi_actions)

        self.env.run()

    # this method is called by __init__
    def add_custom_actions(self, actions: agentspeak.Actions):

            @actions.add("jump",0)
            def _jump(a: agentspeak.runtime.Agent, t, i):
                print("["+ a.name +"] I jump")
                yield


            @actions.add_procedure(
                ".set_public",
                (
                        agentspeak.Literal,
                        int,
                        str
                ),
            )
            def _set_public(command:agentspeak.Literal,arity:int, doc:str):
                self.register_command(command.functor, arity, doc)

            @actions.add_procedure(".print_float", (float,))
            def _print_float(a):
                print(str(a))

            @actions.add_procedure(".send_url", (agentspeak.Literal,))
            def _send_url(u:agentspeak.Literal):
                asyncio.create_task(do_send(str(u)))


    def on_receive(self, msg: asl_message.AgentSpeakMessage):
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
