import a2a_agentspeak.tool
import context

import threading
import uvicorn

from a2a_agentspeak.asp_build import from_file, AgentSpeakInterface

import agentspeak

import openai_requirement_prompt


from context import build_url

failure = agentspeak.Literal("failure")


if __name__ == "__main__":

    host = "127.0.0.1"
    port = 9994

    name = "agent_selector"

    # define agent interface and implementation
    a: AgentSpeakInterface = from_file(
        name + ".asi", name + ".asl", build_url(host, port), tools=[]
    )

    # build and run the a2a server
    server = a.build_server()

    def srv_start():
        uvicorn.run(server.build(), host=host, port=port)

    # threading.Thread(target=srv_start).start()
    srv_start()
    print("-running a2a-server for " + name + " agent-")
