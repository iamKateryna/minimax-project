from enum import Enum

class ExplorationDecay(Enum):
    EPISODE = "episode"
    STEP = "step"

class AgentType(Enum):
    MINMAX = "minmax"
    QLEARNING = "qlearning"
    RANDOM = "random"