"""Termux-first terminal graphics support for TERMAX."""
from .capabilities import probe, supported
from .renderer import display, demo

__all__ = ["probe", "supported", "display", "demo"]
