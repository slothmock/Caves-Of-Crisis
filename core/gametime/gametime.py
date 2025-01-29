import pygame
from datetime import timedelta

class InGameTime:
    """
    Handles the in-game time system, syncing with the Pygame clock.
    Scales time such that 1 real-world second = time_scale minutes in-game.
    """

    def __init__(self, time_scale: float = 5.0):
        """
        Initialize the in-game time system.
        :param time_scale: Scales the in-game time relative to real-world time (e.g., 5 real seconds = 1 in-game minute).
        """
        self.minute = 0  # In-game minute (0-59)
        self.hour = 0  # In-game hour (0-23)
        self.day = 1  # In-game day (1-30 for simplicity)
        self.week = 1  # In-game week (1-4 per month)
        self.month = 1  # In-game month (1-12)
        self.year = 1  # In-game year
        self.season = "Spring"  # Current in-game season
        self.time_scale = time_scale  # Time scaling factor
        self.last_time = 0  # Real-world time (in milliseconds)
        self.time_elapsed = 0  # Time that has passed in real-world ms

        # Define seasonal changes (can be expanded for different systems)
        self.seasons = ["Spring", "Summer", "Autumn", "Winter"]

        # Custom events tied to specific times
        self.events = {}

    def reset_clock(self):
        """Reset the in-game time system"""
        self.minute = 0  # In-game minute (0-59)
        self.hour = 0  # In-game hour (0-23)
        self.day = 1  # In-game day (1-30 for simplicity)
        self.week = 1  # In-game week (1-4 per month)
        self.month = 1  # In-game month (1-12)
        self.year = 1  # In-game year
        self.season = "Spring"  # Current in-game season
        self.last_time = 0  # Real-world time (in milliseconds)
        self.time_elapsed = 0  # Time that has passed in real-world ms

        self.events.clear()


    def update(self):
        """Update in-game time based on the Pygame clock."""
        current_time = pygame.time.get_ticks()  # Get real-world time in ms
        delta_time = current_time - self.last_time  # Time elapsed since last update

        self.time_elapsed += delta_time
        self.last_time = current_time  # Update the last_time to the current time
        
        # Only tick the in-game time once the required time has passed (based on time_scale)
        if self.time_elapsed >= 1000 * self.time_scale:  # 1000 ms = 1 second
            self.time_elapsed = 0  # Reset elapsed time
            self.tick()  # Advance in-game time by 1 minute

    def tick(self):
        """Simulate the passage of one minute in the game."""
        self.minute += 1
        if self.minute >= 60:  # After 60 minutes, a new hour begins
            self.minute = 0
            self.hour += 1
            if self.hour >= 24:  # After 24 hours, a new day begins
                self.hour = 0
                self.day += 1
                if self.day > 30:  # Simplified month with 30 days
                    self.day = 1
                    self.week += 1
                    if self.week > 4:  # After 4 weeks, a new month begins
                        self.week = 1
                        self.month += 1
                        if self.month > 12:  # After 12 months, a new year begins
                            self.month = 1
                            self.year += 1
                        self.update_season()

        # Check for any scheduled events
        self.check_events()

    def update_season(self):
        """Update the current season based on the current month."""
        if 3 <= self.month <= 5:
            self.season = "Spring"
        elif 6 <= self.month <= 8:
            self.season = "Summer"
        elif 9 <= self.month <= 11:
            self.season = "Autumn"
        else:
            self.season = "Winter"

    def schedule_event(self, event_name: str, target_time: timedelta, callback):
        """
        Schedule an event to trigger at a specific in-game time.
        :param event_name: Name of the event.
        :param target_time: The target in-game time as a timedelta object.
        :param callback: The function to call when the event triggers.
        """
        self.events[event_name] = {
            "time": target_time,
            "callback": callback,
        }

    def check_events(self):
        """Check and trigger scheduled events based on the current in-game time."""
        current_time = timedelta(
            days=self.day - 1,
            hours=self.hour,
            minutes=self.minute
        )
        for event_name, event_data in list(self.events.items()):
            if current_time >= event_data["time"]:
                event_data["callback"]()  # Trigger the event
                del self.events[event_name]  # Remove the event after triggering

    def get_time_string(self) -> str:
        """
        Return the current in-game time as a string (e.g. Day 1, 15:30').
        """
        return f" Day {self.day}, {self.hour:02}:{self.minute:02}"

    def time_to_dict(self) -> dict:
        """
        Return the current in-game time as a dictionary for advanced use cases.
        """
        return {
            "year": self.year,
            "season": self.season,
            "month": self.month,
            "week": self.week,
            "day": self.day,
            "hour": self.hour,
            "minute": self.minute,
        }
    
    def convert_to_minutes(self, value: int, unit: str) -> int:
        """
        Convert a time value to in-game minutes based on the given unit.
        :param value: Time value to convert.
        :param unit: Unit of the time ("milliseconds", "seconds", "minutes", "hours").
        :return: Equivalent time in in-game minutes.
        """
        conversion_factors = {
            "milliseconds": self.time_scale / 60 / 1000,
            "seconds": self.time_scale / 60,
            "minutes": 1,
            "hours": 60,
        }
        if unit not in conversion_factors:
            raise ValueError(f"Unsupported time unit: {unit}")
        return int(value * conversion_factors[unit])
    
    def get_time_in_minutes(self) -> int:
        """
        Get the current in-game time as the total number of minutes since Day 1.
        :return: Total in-game minutes.
        """
        return ((self.day - 1) * 1440) + (self.hour * 60) + self.minute
    
    def get_time_in_timedelta(self) -> timedelta:
        """
        Return the current in-game time as a timedelta object.
        """
        return timedelta(
            days=self.day - 1,
            hours=self.hour,
            minutes=self.minute,
        )
    
    def convert_to_timedelta(self, value: int, unit: str) -> timedelta:
        """
        Convert a time value to a timedelta object.
        """
        conversion = {
            "milliseconds": timedelta(milliseconds=value),
            "seconds": timedelta(seconds=value),
            "minutes": timedelta(minutes=value),
            "hours": timedelta(hours=value),
        }
        if unit not in conversion:
            raise ValueError(f"Unsupported time unit: {unit}")
        return conversion[unit]

    def game_time_to_timedelta(self) -> timedelta:
        """
        Convert in-game time to timedelta.
        """
        return timedelta(days=self.day, hours=self.hour, minutes=self.minute)

    def format_time_remaining(self, duration: timedelta) -> str:
        """
        Format remaining time in MINS:SECS.
        """
        total_seconds = int(duration.total_seconds())
        minutes, seconds = divmod(total_seconds, 60)
        return f"{minutes:02}:{seconds:02}"


