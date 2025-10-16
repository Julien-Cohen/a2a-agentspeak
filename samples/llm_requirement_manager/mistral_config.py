import os
from mistralai import Mistral

llm_api_key = os.environ["MISTRAL_API_KEY"]
llm_model = "mistral-small-latest"

llm_client = Mistral(api_key=llm_api_key)


def log(m):
    print("[LOG] " + m)


def ask_llm_for_coverage(spec, req_list):
    chat_response = llm_client.chat.complete(
        model=llm_model,
        messages=[
            {
                "role": "system",
                "content": "Given a specification of a system, and a list of atomic requirements, tell if that list of atomic requirements covers well that specification."
                + " Answer COMPLETE is the specification is well covered."
                + " Answer PARTIAL otherwise.",
            },
            {
                "role": "user",
                "content": "Specification: "
                + spec
                + "(end of the specification) List of requirements: "
                + req_list
                + "(end of list of requirements).",
            },
        ],
        max_tokens=3,
    )
    log(
        "I had an interaction with mistral to check coverage. "
        + "I gave the following spec: "
        + spec
        + " "
        + "I also gave the following requirements: "
        + req_list
        + " "
        + "Mistral gave me the following answer: "
        + chat_response.choices[0].message.content
    )
    return chat_response.choices[0].message.content.startswith("COMPLETE")


def ask_llm_for_completion(spec: str, req_list: str):
    chat_response = llm_client.chat.complete(
        model=llm_model,
        messages=[
            {
                "role": "system",
                "content": "Given a specification of a system, and a list of atomic requirements, give an atomic requirements that covers the specification and which is not included in the given list of requirements."
                + " Answer with the new requirement, don't explain.",
            },
            {
                "role": "user",
                "content": "Specification: "
                + spec
                + "(end of the specification) List of requirements: "
                + req_list
                + "(end of list of requirements).",
            },
        ],
        max_tokens=50,
    )
    log(
        "I had an interaction with mistral to generate a requirement. "
        + "I gave the following spec: "
        + spec
        + "I also gave the following requirements: "
        + req_list
        + " "
        + "Mistral gave me the following answer: "
        + chat_response.choices[0].message.content
    )
    return chat_response.choices[0].message.content
