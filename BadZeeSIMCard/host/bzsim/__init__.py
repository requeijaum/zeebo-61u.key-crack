"""Host side of BadZeeSIMCard: framing, stimuli, run records.

The host never talks to the card. It arms the instrument, records what the
instrument saw, and decides whether a run is valid. Everything here runs without
hardware, which is what makes it testable.
"""

__version__ = "0.1.0"
