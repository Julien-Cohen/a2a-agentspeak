import context

import threading
import uvicorn

from a2a_agentspeak.asp_build import from_file
from a2a_agentspeak.tool import Tool


def build_url(host: str, port: int) -> str:
    return "http://" + host + ":" + str(port) + "/"


if __name__ == "__main__":

    host = "0.0.0.0"
    port = 9999

    name = "receiver"

    def square(x):
        return x * x

    # define agent interface and implementation
    a = from_file(
        name + ".asi",
        name + ".asl",
        build_url(host, port),
        [Tool("function", ".square", (int,), square)],
    )

    # build and run the a2a server
    server = a.build_server()

    def start():
        uvicorn.run(server.build(), host=host, port=port)

    threading.Thread(target=start).start()
    print("-running a2a-server for " + name + " agent-")
