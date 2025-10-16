import os
from mistralai import Mistral

llm_api_key = os.environ["MISTRAL_API_KEY"]
llm_model = "mistral-small-latest"

llm_client = Mistral(api_key=llm_api_key)


def log(m):
    print("[LOG] " + m)


def ask_llm_for_translation(catalog: str, user_request: str):
    chat_response = llm_client.chat.complete(
        model=llm_model,
        messages=[
            {
                "role": "system",
                "content": "Your task is to translate a human request into an AgentSpeak goal for a robot."
                + " Answer COMPLETE is the specification is well covered."
                + " Answer PARTIAL otherwise.",
            },
            {
                "role": "user",
                "content": (
                    "Your task is to translate a human request into an AgentSpeak goal for a robot."
                    + " The possible AgentSpeak achievements are described in the following list. [BEGIN LIST OF ACHIEVEMENTS] "
                    + catalog
                    + "[END OF LIST OF ACHIEVEMENTS]"
                    + " Here is the sentence to translate. [BEGIN] "
                    + user_request
                    + "[END] "
                    + "Respond with only one achievement. For example you can answer 'do_dig' if that achievement has arity 0, or 'do_wait(300)' if arity is 1."
                ),
            },
        ],
        max_tokens=10,
    )

    response = chat_response.choices[0].message.content

    log(
        "I had an interaction with mistral. "
        + "I gave the following catalog: "
        + catalog
        + " "
        + "I also gave the following user request: "
        + user_request
        + " "
        + "Mistral gave me the following answer: "
        + response
    )
    return response
