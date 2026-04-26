"""Sigil generator.

A sigil is a Presence's anonymous in-séance handle. They are deliberately
short, evocative, and ambiguous so two of them sound like they could be
the same person, or three different people, or none at all. We never want
the sigil to leak the underlying Seeker.

Three patterns are produced with roughly equal frequency:

    "The {Adjective} {Noun}"   -> "The Pale Lantern"
    "{Noun}-and-{Noun}"        -> "Ash-and-Iron"
    "{Number} {Noun}s"         -> "Thirteen Veils"

Use ``generate_sigil()`` for a one-shot draw. The ``presence_service`` is
responsible for retrying on uniqueness collisions within a single Seance.
"""

from __future__ import annotations

import secrets

_ADJECTIVES: tuple[str, ...] = (
    "Pale", "Veiled", "Hollow", "Wandering", "Shrouded", "Withered",
    "Spectral", "Cinder", "Bone", "Salt-Bitten", "Moth-Eaten", "Twilit",
    "Cold-Iron", "Mourning", "Velvet", "Midnight", "Ashen", "Black-Eyed",
    "Sleepless", "Forgotten", "Whispering", "Lantern-Bearing", "Drowned",
    "Threadbare", "Vesper", "Quiet", "Unbidden", "Long-Dead", "Crow-Marked",
    "Hourless",
)

_NOUNS: tuple[str, ...] = (
    "Veil", "Ember", "Lantern", "Pendulum", "Sigil", "Crown", "Murmur",
    "Hand", "Hollow", "Mirror", "Thread", "Loom", "Hour", "Door", "Mask",
    "Echo", "Wick", "Reliquary", "Knell", "Idol", "Shroud", "Cipher",
    "Marrow", "Cinder", "Pyre", "Augur", "Salt", "Iron", "Moth", "Reverie",
    "Vespers", "Witness",
)

_NUMBERS: tuple[str, ...] = (
    "Three", "Five", "Seven", "Nine", "Eleven", "Thirteen",
)


def _the_pattern() -> str:
    return f"The {secrets.choice(_ADJECTIVES)} {secrets.choice(_NOUNS)}"


def _and_pattern() -> str:
    a = secrets.choice(_NOUNS)
    b = secrets.choice(_NOUNS)
    # Allow same-noun pairings ("Ash-and-Ash") only rarely - re-roll once.
    if b == a:
        b = secrets.choice(_NOUNS)
    return f"{a}-and-{b}"


def _number_pattern() -> str:
    return f"{secrets.choice(_NUMBERS)} {secrets.choice(_NOUNS)}s"


_PATTERNS = (_the_pattern, _and_pattern, _number_pattern)


def generate_sigil() -> str:
    """Return one randomly-styled sigil."""
    return secrets.choice(_PATTERNS)()
