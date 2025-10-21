from dataclasses import dataclass
from typing import Callable


@dataclass
class Tool:
    kind: str
    action_name: str
    arity: tuple
    implementation: Callable
