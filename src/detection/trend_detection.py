"""
Multi-parameter trend/change-point detection — distinguishes a genuine
deterioration trajectory from a single noisy or transient reading.
"""
# TODO: rolling z-score / change-point detection (e.g. via the `ruptures` library)
# across correlated signals, not single-threshold breaches.


def is_deteriorating(vitals_history: list) -> bool:
    raise NotImplementedError
