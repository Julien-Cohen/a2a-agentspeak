from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.utils import new_agent_text_message

import agentspeak
import agentspeak.runtime
import agentspeak.stdlib
import collections

import bdi

# --8<-- [start:HelloWorldAgent]
class HelloWorldAgent(bdi.BDIAgent):
    """Hello World Agent."""

    def __init__(self):
        super().__init__("hello.asl")


    def extract_reply(self):
        r = self.asp_agent.beliefs[('reply', 1)]
        # r is a set
        tmp = 'nothing'
        for e in r:
            tmp = e

        if isinstance(tmp, agentspeak.Literal):
            tmp = tmp.args[0]

        return tmp

    async def achieve(self, s:str) -> str:
        self.asp_agent.call(agentspeak.Trigger.addition, agentspeak.GoalType.achievement, agentspeak.Literal(s,()), agentspeak.runtime.Intention() )
        self.env.run()

        tmp = self.extract_reply()
        return ('My reply is ' + str(tmp))

    async def tell(self, s:str) -> None:
        self.asp_agent.call(agentspeak.Trigger.addition, agentspeak.GoalType.belief, agentspeak.Literal(s,()), agentspeak.runtime.Intention() )
        self.env.run()
        return


# --8<-- [end:HelloWorldAgent]


# --8<-- [start:HelloWorldAgentExecutor_init]
class HelloWorldAgentExecutor(AgentExecutor):
    """Test AgentProxy Implementation."""

    def __init__(self):
        self.agent = HelloWorldAgent()

    # --8<-- [end:HelloWorldAgentExecutor_init]
    # --8<-- [start:HelloWorldAgentExecutor_execute]
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
            await output_event_queue.enqueue_event(new_agent_text_message("Tell received."))
        else :
            print("Cannot answer to " + i)

    # --8<-- [end:HelloWorldAgentExecutor_execute]

    # --8<-- [start:HelloWorldAgentExecutor_cancel]
    async def cancel(
        self, context: RequestContext, event_queue: EventQueue
    ) -> None:
        raise Exception('cancel not supported')

    # --8<-- [end:HelloWorldAgentExecutor_cancel]
