import context

import threading
import uvicorn

from a2a_agentspeak.asp_build import from_file

host = "0.0.0.0"
port = context.port_receiver

name = "receiver"


from context import build_url

if __name__ == "__main__":

    # define agent interface and implementation
    a = from_file(name + ".asi", name + ".asl", build_url(host, port))

    # build and run the a2a server
    server = a.build_server()

    def start():
        uvicorn.run(server.build(), host=host, port=port)

    threading.Thread(target=start).start()
    print("-running a2a-server for " + name + " agent-")
