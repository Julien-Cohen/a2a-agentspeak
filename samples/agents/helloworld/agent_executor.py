from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.utils import new_agent_text_message

import agentspeak
import agentspeak.runtime
import agentspeak.stdlib

from asl_message import AgentSpeakMessage

import bdi

from conversion import asl_of_a2a

class StateAgent(bdi.BDIAgent):
    """State Agent."""

    # in A2A, each received message has an event queue to post responses.
    # This is not the case in AgentSpeak.
    # Here we add an illocution for requests that need an answer : ask

    def __init__(self):
        super().__init__("state.asl")


    def extract_reply_from_beliefs(self, a:str):
        r = self.asp_agent.beliefs[(a, 1)] # fixme : arity
        assert isinstance(r, set)
        if r == set():
            return None
        else:
            tmp = next(iter(r))
            assert isinstance(tmp, agentspeak.Literal)
            assert tmp.functor == a
            assert isinstance(tmp.args, tuple)
            return tmp.args[0]


    def ask(self, s:str) -> str | None:
        r = self.extract_reply_from_beliefs(s)
        if r is not None :
            return str(r)
        else:
            return None



class StateAgentExecutor(AgentExecutor):
    """Test AgentExecutor Implementation."""

    def __init__(self):
        self.agent = StateAgent()

    async def execute(
        self,
        context: RequestContext,
        output_event_queue: EventQueue,
    ) -> None:

        m : AgentSpeakMessage = asl_of_a2a(context)

        if m.illocution == 'achieve':
            self.agent.on_receive(m)
            await output_event_queue.enqueue_event(new_agent_text_message("Achieve received"))
        elif m.illocution == 'tell':
            self.agent.on_receive(m)
            await output_event_queue.enqueue_event(new_agent_text_message("Tell received."))
        elif m.illocution == 'ask':
            result = self.agent.ask(m.content)
            if result is not None:
                await output_event_queue.enqueue_event(new_agent_text_message(result))
            else:
                pass # do not reply
        else :
            print("Cannot manage illocution " + m.illocution)


    async def cancel(
        self, context: RequestContext, event_queue: EventQueue
    ) -> None:
        raise Exception('cancel not supported')
