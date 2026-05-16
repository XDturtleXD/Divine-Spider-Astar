"""Visual theme: exploration subset colors and scene chrome."""

from __future__ import annotations

# Max 8 remaining-subset states (2^3 snacks). High-contrast hues, no pure reds
# (reserved for spider + path line). Spread roughly evenly around the hue wheel.
EXPLORATION_SUBSET_PALETTE: tuple[tuple[int, int, int], ...] = (
    (163, 56, 73),
    (130, 64, 23),
    (77, 147, 51),
    (38, 111, 95),
    (75, 146, 117),
    (75, 109, 138),
    (215, 141, 109),
    (215, 170, 109),
)

EXPLORED_STRIPE_ALPHA = 185

BACKGROUND_RGB = (20, 20, 20)

# Final solution path — matches red spider accent (subset palette has no reds).
PATH_LINE_RGB = (210, 52, 48)
