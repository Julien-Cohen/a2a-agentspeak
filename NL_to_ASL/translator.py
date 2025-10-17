from a2a.types import AgentCard

from NL_to_ASL.mistral_config import ask_llm_for_translation


class LLMError(Exception):
    pass


system_prompt_message = {
    "role": "system",
    "content": "Your task is to translate a human request into an AgentSpeak goal",
}


def build_user_prompt_message(agent_type: str, catalog: str, user_request: str):
    return {
        "role": "user",
        "content": (
            "Your task is to translate a human request into an AgentSpeak goal for the following agent: "
            + agent_type
            + " The possible AgentSpeak achievements are described in the following list. [BEGIN LIST OF ACHIEVEMENTS] "
            + catalog
            + "[END OF LIST OF ACHIEVEMENTS]"
            + " Here is the sentence to translate. [BEGIN] "
            + user_request
            + "[END] "
            + "Respond with only one achievement. For example you can answer 'do_dig' if that achievement has arity 0, or 'do_wait(300)' if arity is 1."
        ),
    }


def translate(card: AgentCard, request: str) -> str:
    try:
        user_prompt = build_user_prompt_message(
            str(card.description), str(card.skills), request
        )
        return ask_llm_for_translation(
            system_prompt=system_prompt_message, user_prompt=user_prompt
        )
    except Exception as e:
        raise LLMError()
