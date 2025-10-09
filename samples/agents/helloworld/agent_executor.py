from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.utils import new_agent_text_message

import agentspeak
import agentspeak.runtime
import agentspeak.stdlib


import bdi


class StatePingAgent(bdi.BDIAgent):
    """State Ping  Agent."""

    # in A2A, each received message has a event queue to post responses.
    # This is not the case in AgentSpeak.
    # Here we add a mechanism to build answers.
    # More precisely, the AgentSpeak program adds a 'reply(v)' belief in its state
    # and the value v is extracted and placed in an answer message.

    def __init__(self):
        super().__init__("state.asl")


    def extract_reply_from_beliefs(self):
        r = self.asp_agent.beliefs[('reply', 1)]
        tmp = 'nothing'
        for e in r:
            tmp = e

        if isinstance(tmp, agentspeak.Literal):
            tmp = tmp.args[0]

        return tmp

    async def achieve(self, s:str) -> str:
        self.on_receive(bdi.AgentSpeakMessage("achieve", s, "unknown"))
        return ('The number is ' + str(self.extract_reply_from_beliefs()))

    async def tell(self, s:str) -> None:
        self.on_receive(bdi.AgentSpeakMessage("tell", s, "unknown"))
        return



class StatePingAgentExecutor(AgentExecutor):
    """Test AgentExecutor Implementation."""

    def __init__(self):
        self.agent = StatePingAgent()

    async def execute(
        self,
        context: RequestContext,
        output_event_queue: EventQueue,
    ) -> None:

        i = context.get_user_input()
        if i == '(achieve,ping)':
            result = await self.agent.achieve('ping')
            await output_event_queue.enqueue_event(new_agent_text_message(result))
        elif i == '(tell,ready)':
            await self.agent.tell('ready')
            await output_event_queue.enqueue_event(new_agent_text_message("I changed my state (new belief added)."))
        else :
            print("Cannot answer to " + i)


    async def cancel(
        self, context: RequestContext, event_queue: EventQueue
    ) -> None:
        raise Exception('cancel not supported')
