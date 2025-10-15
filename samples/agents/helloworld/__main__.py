import threading
import uvicorn

from asi import AgentSpeakInterface


if __name__ == "__main__":

    # define agent interface and implementation

    a = AgentSpeakInterface(
        "State Agent",
        "An agent with a state that returns a number on request. (Understands AgentSpeak messages)",
        "http://localhost:9999/",
        "state.asl",
    )

    a.publish_ask(
        id="number-provider",
        doc="Returns a number which depends on an internal state.",
        literal="secret",
    )

    a.publish_listen(
        id="ready-skill",
        doc="Change internal state on ready",
        literal="ready",
    )

    a.publish_obey(
        id="ping-skill",
        doc="handle a ping request",
        literal="ping",
    )

    # build and run the a2a server
    server = a.build_server()

    def start():
        uvicorn.run(server.build(), host="0.0.0.0", port=9999)

    threading.Thread(target=start).start()
    print("-running a2a-server for state agent-")
