from enum import Enum
from core.logging import logger
from core.message_log.message_log import MessageLog
from core.gametime.gametime import InGameTime


class StatusSeverity(Enum):
    CRITICAL = (255, 0, 0)  # Red
    SEVERE = (255, 165, 0)  # Orange
    MODERATE = (255, 255, 0)  # Yellow
    MINOR = (0, 255, 0)  # Green
    NONE = (220, 220, 220)  # White-ish
    PERMANENT = (160, 32, 240)  # Purple

    @property
    def color(self):
        return self.value


class StatSeverityDescriptions(Enum):
    DEV = {
        StatusSeverity.PERMANENT: "The Creator"
    }
    FOOD = {
        StatusSeverity.CRITICAL: "Starving",
        StatusSeverity.SEVERE: "Very Hungry",
        StatusSeverity.MODERATE: "Hungry",
        StatusSeverity.MINOR: "Peckish",
        StatusSeverity.NONE: "Full",
    }
    THIRST = {
        StatusSeverity.CRITICAL: "Dehydrated",
        StatusSeverity.SEVERE: "Very Thirsty",
        StatusSeverity.MODERATE: "Thirsty",
        StatusSeverity.MINOR: "Parched",
        StatusSeverity.NONE: "Hydrated",
    }
    STAMINA = {
        StatusSeverity.CRITICAL: "Exhausted",
        StatusSeverity.SEVERE: "Very Tired",
        StatusSeverity.MODERATE: "Tired",
        StatusSeverity.MINOR: "Fatigued",
        StatusSeverity.NONE: "Energized",
    }
    SLEEP = {
        StatusSeverity.CRITICAL: "Sleep Deprived",
        StatusSeverity.SEVERE: "Very Sleepy",
        StatusSeverity.MODERATE: "Sleepy",
        StatusSeverity.MINOR: "Drowsy",
        StatusSeverity.NONE: "Well-Rested",
    }
    WET = {
        StatusSeverity.CRITICAL: "Soaked",
        StatusSeverity.SEVERE: "Dripping Wet",
        StatusSeverity.MODERATE: "Soggy",
        StatusSeverity.MINOR: "Damp",
        StatusSeverity.NONE: "Dry",
    }

    def get_feeling(self, severity: StatusSeverity) -> str:
        """
        Retrieve the appropriate feeling for the given severity level.
        """
        return self.value.get(severity, "Unknown")


class StatusEffects:
    def __init__(self, message_log: MessageLog, game_time: InGameTime):
        """
        Initialize the StatusEffects system.
        """
        self.effects: dict[str, dict] = {}
        self.message_log = message_log
        self.game_time = game_time

    def add_or_update_effect(
        self,
        name: str,
        severity: StatusSeverity,
        stat_feeling: StatSeverityDescriptions,
        duration: int = None,
    ) -> None:
        """
        Add or update a status effect based on its severity, value, and duration in minutes.
        """
        # Calculate end time
        end_time = None
        if duration:
            end_time = self.game_time.get_time_in_minutes() + duration

        # Determine effect description
        description = f"You are {stat_feeling.get_feeling(severity).lower()}."

        # Update or add the effect
        self.effects[name] = {
            "severity": severity,
            "color": severity.color,
            "end_time": end_time,
            "description": description,
            "duration": duration
        }

    def remove_expired_effects(self) -> None:
        """
        Remove expired effects based on the current in-game time.
        """
        expired_effects = [name for name in self.effects if not self.is_effect_active(name)]

        for name in expired_effects:
            del self.effects[name]

    def is_effect_active(self, name: str) -> bool:
        """
        Check if a specific effect is active.
        """
        effect = self.effects.get(name)
        if not effect:
            return False
        if name == "Wet" and effect["end_time"] is None:
            return False
        return effect["duration"] is None or self.game_time.get_time_in_minutes() < effect["end_time"]

    def get_time_remaining(self, name: str) -> str:
        """
        Get the formatted time remaining for a specific effect.
        """
        effect = self.effects.get(name)
        if not effect:
            return

        if effect["end_time"] is None:
            return None

        remaining_minutes = effect["end_time"] - self.game_time.get_time_in_minutes()

        return remaining_minutes

