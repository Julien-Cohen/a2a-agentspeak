from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue


from asl_message import AgentSpeakMessage

import bdi

from conversion import asl_of_a2a


from bdi import reply

class StateAgent(bdi.BDIAgent):
    """State Agent."""

    def __init__(self):
        super().__init__("state.asl")



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

        await self.agent.act(m, output_event_queue)



    async def cancel(
        self, context: RequestContext, event_queue: EventQueue
    ) -> None:
        raise Exception('cancel not supported')
