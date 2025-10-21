from a2a.server.agent_execution import RequestContext
from a2a.types import (
    SendMessageRequest,
    MessageSendParams,
    SendMessageResponse,
    SendMessageSuccessResponse,
    Message,
    MessageSendConfiguration,
    PushNotificationConfig,
)

from typing import Any
from uuid import uuid4

from a2a_agentspeak.asl_message import AgentSpeakMessage


def extract_text(response: SendMessageResponse):
    """Extract text from synchronous replies"""
    if (
        isinstance(response, SendMessageResponse)
        and isinstance(response.root, SendMessageSuccessResponse)
        and isinstance(response.root.result, Message)
    ):
        return response.root.result.parts[0].root.text
    else:
        return response.model_dump(mode="json", exclude_none=True)


def build_basic_message(
    illoc: str, t: str, c: MessageSendConfiguration
) -> dict[str, Any]:
    return {
        "message": {
            "role": "user",
            "parts": [{"kind": "text", "metadata": {"illocution": illoc}, "text": t}],
            "messageId": uuid4().hex,
        },
        "configuration": c,
    }


def build_basic_request(illoc: str, t: str, my_url: str) -> SendMessageRequest:
    c = MessageSendConfiguration(
        push_notification_config=PushNotificationConfig(url=my_url)
    )
    params = MessageSendParams(**build_basic_message(illoc, t, c))
    return SendMessageRequest(id=str(uuid4()), params=params)


def asl_of_a2a(context: RequestContext) -> AgentSpeakMessage:
    if context.configuration is None:
        sender = "no config"
    elif context.configuration.push_notification_config is None:
        sender = "no push config"
    else:
        sender = context.configuration.push_notification_config.url
    i = context.message.parts[0].root.metadata["illocution"]
    return AgentSpeakMessage(i, context.get_user_input(), sender)
