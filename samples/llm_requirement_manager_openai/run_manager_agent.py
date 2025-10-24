import a2a_agentspeak.tool
import context

import threading
import uvicorn

from a2a_agentspeak.asp_build import from_file, AgentSpeakInterface

import agentspeak

import openai_requirement_prompt


from context import build_url

failure = agentspeak.Literal("failure")


def prompt_completeness(
    s: agentspeak.Literal, r: agentspeak.Literal
) -> agentspeak.Literal:
    assert s.functor == "spec"
    assert r.functor == "req"
    try:
        res = openai_requirement_prompt.ask_llm_for_coverage(
            str(s.args[0]), str(r.args[0])
        )
        return agentspeak.Literal("complete" if res else "incomplete")
    except Exception as e:
        print("Failure while talking with the llm")
        print(str(e))
        return failure


def prompt_generation(s, r) -> agentspeak.Literal:
    assert s.functor == "spec"
    assert r.functor == "req"
    try:
        return agentspeak.Literal(
            openai_requirement_prompt.ask_llm_for_completion(
                str(s.args[0]), str(r.args[0])
            )
        )
    except Exception as e:
        print("Failure while talking with the llm")
        print(str(e))
        return failure


if __name__ == "__main__":

    host = "0.0.0.0"
    port = 9999

    name = "manager"

    action1 = a2a_agentspeak.tool.Tool(
        "function",
        ".prompt_completeness",
        (agentspeak.Literal, agentspeak.Literal),
        prompt_completeness,
    )

    action2 = a2a_agentspeak.tool.Tool(
        "function",
        ".prompt_generate",
        (agentspeak.Literal, agentspeak.Literal),
        prompt_generation,
    )

    # define agent interface and implementation
    a: AgentSpeakInterface = from_file(
        name + ".asi",
        name + ".asl",
        build_url(host, port),
        tools=[action1, action2],
    )

    # build and run the a2a server
    server = a.build_server()

    def srv_start():
        uvicorn.run(server.build(), host=host, port=port)

    # threading.Thread(target=start).start()
    srv_start()
    print("-running a2a-server for " + name + " agent-")
