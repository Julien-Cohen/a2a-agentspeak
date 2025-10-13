
from a2a.types import (SendMessageRequest, MessageSendParams, SendMessageResponse, SendMessageSuccessResponse, Message, MessageSendConfiguration)

from typing import Any
from uuid import uuid4

def extract_text (response:SendMessageResponse):
    if isinstance(response, SendMessageResponse):
        if isinstance(response.root, SendMessageSuccessResponse):
            if isinstance(response.root.result, Message):
                return response.root.result.parts[0].root.text
    # otherwise
    return response.model_dump(mode='json', exclude_none=True)


def build_basic_message(t: str, c: MessageSendConfiguration) -> dict[str, Any]:
    return {
        'message': {
            'role': 'user',
            'parts': [
                {'kind': 'text', 'text': t}
            ],
            'messageId': uuid4().hex,
        },
        'configuration': c
    }


def build_basic_request(t: str, c: MessageSendConfiguration) -> SendMessageRequest:
    return SendMessageRequest(id=str(uuid4()), params=MessageSendParams(**build_basic_message(t, c)))