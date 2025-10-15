import threading
import uvicorn

from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore

from bdi import BDIAgentExecutor

from asi import ASLSkill, build_agent_card


if __name__ == "__main__":

    skill1 = ASLSkill(
        id="number-provider",
        doc="Returns a number which depends on an internal state.",
        literal="secret",
        illocution="ask",
    )
    skill2 = ASLSkill(
        id="ready-skill",
        doc="Change internal state on ready",
        literal="ready",
        illocution="tell",
    )

    skill3 = ASLSkill(
        id="ping-skill",
        doc="handle a ping request",
        literal="ping",
        illocution="achieve",
    )

    # This will be the public-facing agent card
    public_agent_card = build_agent_card(
        "State Agent",
        "An agent with a state that returns a number on request. (Understands AgentSpeak messages)",
        "http://localhost:9999/",
        [skill1, skill2, skill3],
    )

    request_handler = DefaultRequestHandler(
        agent_executor=BDIAgentExecutor("state.asl"),
        task_store=InMemoryTaskStore(),
    )

    server = A2AStarletteApplication(
        agent_card=public_agent_card,
        http_handler=request_handler,
    )

    def start():
        uvicorn.run(server.build(), host="0.0.0.0", port=9999)

    threading.Thread(target=start).start()
    print("-running a2a-server for state agent-")
