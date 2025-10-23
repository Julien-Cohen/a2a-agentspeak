import os

import openai
from agentspeak import AslError
from openai import OpenAI

openai.log = "debug"

llm_api_key = os.environ["OPENAI_API_KEY"]
llm_model = "gpt-4o-mini"

llm_client = OpenAI(api_key=llm_api_key)

llm_timeout = 60  # seconds


def log(m):
    print("[LOG] " + m)


def ask_llm_for_coverage(spec: str, req_list: str):
    log("Asking LLM for coverage (timeout " + str(llm_timeout) + " seconds)")
    try:
        chat_response = llm_client.responses.create(
            model=llm_model,
            instructions=(
                "Given a specification of a system, and a list of atomic requirements, tell if that list of atomic requirements covers well that specification."
                + " Answer COMPLETE is the specification is well covered."
                + " Answer PARTIAL otherwise."
            ),
            input=(
                "Specification: "
                + spec
                + "(end of the specification) List of requirements: "
                + req_list
                + "(end of list of requirements)."
            ),
            timeout=llm_timeout,
            background=False,
            max_output_tokens=16,  # 16 is the minimum for gpt-4o-mini
        )
        log("Resonse from LLM received")
        r = chat_response.output_text
        log(
            "I had an interaction with gpt to check coverage. "
            + "I gave the following spec: "
            + spec
            + " "
            + "I also gave the following requirements: "
            + req_list
            + " "
            + "Gpt gave me the following answer: "
            + r
        )
        if r.startswith("COMPLETE"):
            return True
        elif r.startswith("PARTIAL"):
            return False
        else:
            raise Exception("Cannot understand LLM answer.")
    except Exception as e:
        print(str(e))
        raise AslError("LLM failure: " + str(type(e))) from e


def ask_llm_for_completion(spec: str, req_list: str):
    log("Asking LLM for completion  (timeout " + str(llm_timeout) + " seconds)")
    try:
        chat_response = llm_client.responses.create(
            model=llm_model,
            instructions="Given a specification of a system, and a list of atomic requirements, give an atomic requirements that covers the specification and which is not included in the given list of requirements."
            + " Answer with the new requirement, don't explain.",
            input="Specification: "
            + spec
            + "(end of the specification) List of requirements: "
            + req_list
            + "(end of list of requirements).",
            timeout=llm_timeout,
            background=False,
            # max_output_tokens=50,
        )
        log("Resonse from LLM received")
        log(
            "I had an interaction with gpt to generate a requirement. "
            + "I gave the following spec: "
            + spec
            + "I also gave the following requirements: "
            + req_list
            + " "
            + "Gpt gave me the following answer: "
            + chat_response.output_text
        )
        return chat_response.output_text
    except Exception as e:
        print(str(e))
        raise AslError("LLM failure: " + str(type(e)))
