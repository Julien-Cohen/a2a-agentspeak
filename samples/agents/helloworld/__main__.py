import threading
import uvicorn

from samples.agents.helloworld.bdi.asi import from_asi_file


if __name__ == "__main__":

    # define agent interface and implementation
    a = from_asi_file("state.asi", "http://localhost:9999/", "state.asl")

    # build and run the a2a server
    server = a.build_server()

    def start():
        uvicorn.run(server.build(), host="0.0.0.0", port=9999)

    threading.Thread(target=start).start()
    print("-running a2a-server for state agent-")
