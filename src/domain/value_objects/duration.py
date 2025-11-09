"""Duration value object for time durations."""

from typing import Any

from domain.exceptions.validation_exceptions import InvalidDurationError


class Duration:
    """Represents a time duration as a value object.

    According to FR-2.1, duration is stored in seconds and must be:
    - Non-negative integer
    - Immutable after creation

    Attributes:
        seconds: Duration in seconds
        hours: Duration in hours (as float)
        minutes: Duration in minutes (as float)
    """

    # Maximum reasonable duration: 24 hours
    MAX_SECONDS = 86400

    def __init__(self, seconds: int) -> None:
        """Initialize Duration instance.

        Args:
            seconds: Duration in seconds

        Raises:
            InvalidDurationError: If duration is negative or exceeds maximum
        """
        if seconds < 0:
            raise InvalidDurationError(
                seconds, reason="Duration cannot be negative"
            )

        if seconds > self.MAX_SECONDS:
            raise InvalidDurationError(
                seconds,
                reason=f"Duration exceeds maximum allowed ({self.MAX_SECONDS} seconds = 24 hours)",
            )

        self._seconds = seconds

    @property
    def seconds(self) -> int:
        """Get duration in seconds.

        Returns:
            Duration in seconds
        """
        return self._seconds

    @property
    def minutes(self) -> float:
        """Get duration in minutes.

        Returns:
            Duration in minutes as float
        """
        return self._seconds / 60.0

    @property
    def hours(self) -> float:
        """Get duration in hours.

        Returns:
            Duration in hours as float
        """
        return self._seconds / 3600.0

    def __add__(self, other: "Duration") -> "Duration":
        """Add two durations together.

        Args:
            other: Another Duration instance

        Returns:
            New Duration instance with sum of durations
        """
        if not isinstance(other, Duration):
            raise TypeError("Can only add Duration to Duration")
        return Duration(self._seconds + other._seconds)

    def __repr__(self) -> str:
        """Return detailed string representation."""
        return f"Duration(seconds={self._seconds})"

    def __str__(self) -> str:
        """Return human-readable string representation."""
        if self._seconds < 60:
            return f"{self._seconds}s"
        elif self._seconds < 3600:
            return f"{self.minutes:.1f}m"
        else:
            return f"{self.hours:.2f}h"

    def __eq__(self, other: Any) -> bool:
        """Check equality with another Duration instance.

        Args:
            other: Object to compare with

        Returns:
            True if durations are equal
        """
        if not isinstance(other, Duration):
            return False
        return self._seconds == other._seconds

    def __hash__(self) -> int:
        """Return hash of duration value for use in sets/dicts.

        Returns:
            Hash of the duration value
        """
        return hash(self._seconds)