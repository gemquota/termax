"""Small ASCII reef simulation used by TERMAX Pulse's optional aquarium mode."""
from __future__ import annotations

import math
import shutil


class Aquarium:
    """A tiny event-reactive scene: failures stir predators; successes grow coral."""

    def __init__(self):
        self.tick = 0
        self.health = 0
        self.current = "run"

    def render(self, event: str) -> str:
        self.tick += 1
        self.current = event
        if event == "ok":
            self.health = min(12, self.health + 2)
        elif event == "bad":
            self.health = max(-12, self.health - 3)
        elif event == "warn":
            self.health = max(-12, self.health - 1)
        width = max(32, min(72, shutil.get_terminal_size((80, 24)).columns - 4))
        rows = [[" " for _ in range(width)] for _ in range(5)]
        # Slow water shimmer.
        for x in range(width):
            rows[0][x] = "~" if (x + self.tick) % 7 == 0 else " "
            rows[4][x] = "." if (x * 3 + self.tick) % 11 == 0 else " "
        # Fish school follows the output rhythm.
        fish_x = (self.tick * 3) % max(1, width - 5)
        rows[1][fish_x:fish_x + 3] = list("><>")
        small_x = (width - 1 - self.tick * 2) % max(1, width - 4)
        rows[2][small_x:small_x + 3] = list("<><")
        # Bubbles rise and drift.
        for i in range(4):
            x = (self.tick * (i + 2) + i * 13) % width
            y = (4 - (self.tick + i * 2) % 4)
            rows[y][x] = "o" if i % 2 else "°"
        # Reef grows after success and recedes after errors.
        reef = max(1, min(12, 6 + self.health))
        for i in range(reef):
            x = width // 2 - reef // 2 + i
            rows[4][x] = "♣" if self.health >= 0 else "·"
        if event == "bad":
            predator_x = (width - 4 - self.tick * 4) % max(1, width - 5)
            rows[1][predator_x:predator_x + 4] = list("><))")
        scene = "\n".join("".join(row) for row in rows)
        label = {"ok":"reef recovering", "warn":"current disturbed",
                 "bad":"predator alert", "info":"school gathering",
                 "run":"ecosystem cruising"}.get(event, "ecosystem cruising")
        return f"\x1b[36m{scene}\x1b[0m\n\x1b[2mNEXUS REEF · {label} · stability {self.health:+d}\x1b[0m"
