import os

from a2a.types import AgentCard
from agentspeak import AslError
from mistralai import Mistral

from a2a_agentspeak.skill import asl_skill_of_a2a_skill

llm_api_key = os.environ["MISTRAL_API_KEY"]
llm_model = "mistral-small-latest"

llm_client = Mistral(api_key=llm_api_key)


def log(m):
    print("[LOG] " + m)


def build_agent_descr(a: AgentCard) -> tuple[str, str, str]:
    l = [asl_skill_of_a2a_skill(s) for s in a.skills]
    return (a.name, a.description, str(l))


def ask_llm_for_agent(query, lst: list[AgentCard]):
    str_lst = str([build_agent_descr(a) for a in lst])
    log(
        "I will prompt LLM with the following query: "
        + query
        + " "
        + "I also gave the following list of agents: "
        + str_lst
    )
    try:
        chat_response = llm_client.chat.complete(
            model=llm_model,
            messages=[
                {
                    "role": "system",
                    "content": "Given a specification of a task, and a list of agents with their skills, tell what agent is suited for that task."
                    + " Answer with the index (int) of the convenient agent in the list of agents.",
                },
                {
                    "role": "user",
                    "content": "Task: "
                    + query
                    + "(end of the specification of the task) List of agents: "
                    + str_lst
                    + "(end of list of agents)."
                    + "Just answer with an int if found, with None otherwise.",
                },
            ],
            max_tokens=1,
        )
        log(
            "Mistral gave me the following answer: "
            + chat_response.choices[0].message.content
        )
        return int(chat_response.choices[0].message.content)
    except Exception as e:
        raise Exception("LLM failure")
