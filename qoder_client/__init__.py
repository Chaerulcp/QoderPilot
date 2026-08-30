"""Qoder IDE and Qoder Agentic automation package."""

from .agentic import QoderAgenticAutomation
from .automation import QoderClientAutomation, init_platform

__all__ = ["QoderAgenticAutomation", "QoderClientAutomation", "init_platform"]
