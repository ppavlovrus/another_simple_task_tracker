"""Value objects module.

This module contains value objects used throughout the domain.
Value objects are immutable objects defined by their attributes.
"""

from domain.value_objects.duration import Duration
from domain.value_objects.email import Email
from domain.value_objects.task_title import TaskTitle

__all__ = [
    "Duration",
    "Email",
    "TaskTitle",
]
