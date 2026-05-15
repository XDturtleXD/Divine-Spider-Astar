"""Visual theme: exploration subset colors and scene chrome."""

from __future__ import annotations

# Max 8 remaining-subset states (2^3 snacks). First-seen assignment in drawer.
# Ground / earth palette: sand, olive, sage, clay, terracotta, slate — no reds (spider).
EXPLORATION_SUBSET_PALETTE: tuple[tuple[int, int, int], ...] = (
    (232, 208, 145),  # sand / cream
    (215, 178, 55),   # mustard gold
    (190, 118, 65),   # tan clay
    (130, 100, 50),   # olive brown
    (115, 170, 95),   # sage
    (75, 135, 65),    # moss green
    (205, 90, 50),    # terracotta
    (70, 125, 155),   # slate dust
)

EXPLORED_STRIPE_ALPHA = 185

BACKGROUND_RGB = (20, 20, 20)

# Final solution path — matches red spider accent (subset palette has no reds).
PATH_LINE_RGB = (210, 52, 48)
