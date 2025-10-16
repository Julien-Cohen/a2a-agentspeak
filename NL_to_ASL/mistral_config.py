import os
from mistralai import Mistral

llm_api_key = os.environ["MISTRAL_API_KEY"]
llm_model = "mistral-small-latest"

llm_client = Mistral(api_key=llm_api_key)


def log(m):
    print("[LOG] " + m)


def ask_llm_for_translation(system_prompt, user_prompt):

    messages = [system_prompt, user_prompt]

    log("Full prompt: " + str(messages))

    chat_response = llm_client.chat.complete(
        model=llm_model,
        messages=messages,
        max_tokens=5,
    )

    response = chat_response.choices[0].message.content

    log(
        "I had an interaction with mistral with the prompt above. "
        + "Mistral gave me the following answer: "
        + response
    )
    return response
