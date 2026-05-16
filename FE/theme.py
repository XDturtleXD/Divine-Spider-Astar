"""Visual theme: exploration subset colors and scene chrome."""

from __future__ import annotations

# Max 8 remaining-subset states (2^3 snacks). High-contrast hues, no pure reds
# (reserved for spider + path line). Spread roughly evenly around the hue wheel.
EXPLORATION_SUBSET_PALETTE: tuple[tuple[int, int, int], ...] = (
    (240, 145, 40),   # orange
    (240, 215, 60),   # yellow
    (135, 205, 60),   # lime
    (60, 185, 95),    # green
    (55, 200, 205),   # cyan
    (70, 130, 220),   # blue
    (165, 90, 210),   # purple
    (220, 80, 170),   # magenta
)

EXPLORED_STRIPE_ALPHA = 185

BACKGROUND_RGB = (20, 20, 20)

# Final solution path — matches red spider accent (subset palette has no reds).
PATH_LINE_RGB = (210, 52, 48)
