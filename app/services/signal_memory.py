"""
OAMI Enterprise
Signal Memory Service
"""

from datetime import datetime

# -------------------------------------------------
# Signal Lifecycle Timing (seconds)
# -------------------------------------------------

NEW_TIME = 10
BUILDING_TIME = 30
CONFIRMED_TIME = 90


class SignalRecord:

    def __init__(self):

        self.signal = "WAIT"

        self.state = "NEW"

        self.started = None

        self.last_update = None

        self.age_seconds = 0


class SignalMemory:

    def __init__(self):

        self.records = {}

    # -------------------------------------------------

    def update(
        self,
        symbol,
        signal,
        confidence=None,
        score=None,
        rvol=None
    ):

        now = datetime.now()

        # ---------------------------------------------
        # First Signal
        # ---------------------------------------------

        if symbol not in self.records:

            record = SignalRecord()

            record.signal = signal
            record.started = now
            record.last_update = now
            record.state = "NEW"
            record.age_seconds = 0

            self.records[symbol] = record

            return record

        record = self.records[symbol]

        # ---------------------------------------------
        # Signal Changed
        # ---------------------------------------------

        if record.signal != signal:

            record.signal = signal
            record.started = now
            record.last_update = now
            record.state = "NEW"
            record.age_seconds = 0

            return record

        # ---------------------------------------------
        # Signal Continues
        # ---------------------------------------------

        record.last_update = now

        record.age_seconds = int(
            (now - record.started).total_seconds()
        )

        # ---------------------------------------------
        # Lifecycle
        # ---------------------------------------------

        if record.age_seconds < NEW_TIME:

            record.state = "NEW"

        elif record.age_seconds < BUILDING_TIME:

            record.state = "BUILDING"

        elif record.age_seconds < CONFIRMED_TIME:

            record.state = "CONFIRMED"

        else:

            record.state = "ACTIVE"

        return record


# -------------------------------------------------

signal_memory = SignalMemory()