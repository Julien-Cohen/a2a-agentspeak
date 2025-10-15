import agentspeak


def check_achievement(literal: str, ast: agentspeak.parser.AstAgent) -> bool:
    """The literal occurs as trigger in a plan."""
    # exists
    for p in ast.plans:
        if (
            p.event.goal_type == agentspeak.GoalType.achievement
            and p.event.head.functor == literal
        ):
            return True
    return False


def check_input_belief(literal: str, ast: agentspeak.parser.AstAgent) -> bool:
    """The literal occurs as trigger in a plan."""
    # exists
    for p in ast.plans:
        if (
            p.event.goal_type == agentspeak.GoalType.belief
            and p.event.head.functor == literal
        ):
            return True
    return False


def check_ask_belief(literal: str, ast: agentspeak.parser.AstAgent) -> bool:
    """The literal occurs in a belief."""
    # exists
    for b in ast.beliefs:
        if b.functor == literal:
            return True
    return False
