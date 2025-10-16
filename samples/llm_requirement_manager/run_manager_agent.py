from agentspeak import LinkedList

import context

import threading
import uvicorn

from a2a_agentspeak.asp_build import from_file, AgentSpeakInterface

import agentspeak

import mistral_config


def build_url(host: str, port: int) -> str:
    return "http://" + host + ":" + str(port) + "/"


if __name__ == "__main__":

    host = "0.0.0.0"
    port = 9999

    name = "manager"

    def add_custom_actions(actions: agentspeak.Actions) -> int:

        @actions.add_function(
            ".prompt_completeness", (agentspeak.Literal, agentspeak.Literal)
        )
        def prompt_completeness(
            s: agentspeak.Literal, r: agentspeak.Literal
        ) -> agentspeak.Literal:
            assert s.functor == "spec"
            assert r.functor == "req"
            res = mistral_config.ask_llm_for_coverage(str(s.args[0]), str(r.args[0]))
            return agentspeak.Literal("complete" if res else "incomplete")

        @actions.add_function(
            ".prompt_generate", (agentspeak.Literal, agentspeak.Literal)
        )
        def prompt_generation(s, r) -> agentspeak.Literal:
            assert s.functor == "spec"
            assert r.functor == "req"
            return agentspeak.Literal(
                mistral_config.ask_llm_for_completion(str(s.args[0]), str(r))
            )

    # define agent interface and implementation
    a: AgentSpeakInterface = from_file(
        name + ".asi", name + ".asl", build_url(host, port)
    )

    # build and run the a2a server
    server = a.build_server(additional_callback=add_custom_actions)

    def start():
        uvicorn.run(server.build(), host=host, port=port)

    threading.Thread(target=start).start()
    print("-running a2a-server for " + name + " agent-")
