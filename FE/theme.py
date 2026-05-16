"""Visual theme: exploration subset colors and scene chrome."""

from __future__ import annotations

# Max 8 remaining-subset states (2^3 snacks). High-contrast hues, no pure reds
# (reserved for spider + path line). Spread roughly evenly around the hue wheel.
EXPLORATION_SUBSET_PALETTE: tuple[tuple[int, int, int], ...] = (
    (78, 44, 115),
    (156, 52, 76),
    (170, 162, 57),
    (87, 149, 50),
    (170, 91, 57),
    (170, 122, 57),
    (39, 116, 85),
    (42, 79, 110),
)

EXPLORED_STRIPE_ALPHA = 185

BACKGROUND_RGB = (20, 20, 20)

# Final solution path — matches red spider accent (subset palette has no reds).
PATH_LINE_RGB = (210, 52, 48)
