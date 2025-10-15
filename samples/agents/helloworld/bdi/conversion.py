from asl_message import AgentSpeakMessage
from a2a.server.agent_execution import RequestContext

def decode_str(s:str, sender:str) -> AgentSpeakMessage:
    s2 = s.removeprefix("(").removesuffix(")")
    s3 = s2.split(",")
    return AgentSpeakMessage(s3[0], s3[1], sender)

def asl_of_a2a(context:RequestContext) -> AgentSpeakMessage:
    if context.configuration is None:
        sender = "no config"
    elif context.configuration.push_notification_config is None:
        sender = "no push config"
    else:
        sender = context.configuration.push_notification_config.url
    return decode_str(context.get_user_input(), sender)
