from enum import Enum


class RiskLevel(Enum):
    SAFE = "Safe"
    WARNING = "Warning"
    DANGEROUS = "Dangerous"

    UNKNOWN = "Unknown"
