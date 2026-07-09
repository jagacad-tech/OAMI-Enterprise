"""
OAMI Enterprise
Instrument Master
"""

INSTRUMENTS = {

    # ----------------------------
    # Index
    # ----------------------------

    "NIFTY": {
        "instrument_type": "INDEX",
        "strike_interval": 50,
        "lot_size": 75
    },

    "BANKNIFTY": {
        "instrument_type": "INDEX",
        "strike_interval": 100,
        "lot_size": 35
    },

    "FINNIFTY": {
        "instrument_type": "INDEX",
        "strike_interval": 50,
        "lot_size": 40
    },

    "SENSEX": {
        "instrument_type": "INDEX",
        "strike_interval": 100,
        "lot_size": 20
    },

    # ----------------------------
    # Stocks
    # ----------------------------

    "RELIANCE": {
        "instrument_type": "STOCK",
        "strike_interval": 10,
        "lot_size": 250
    },

    "HDFCBANK": {
        "instrument_type": "STOCK",
        "strike_interval": 20,
        "lot_size": 550
    },

    "INFY": {
        "instrument_type": "STOCK",
        "strike_interval": 10,
        "lot_size": 300
    },

    "SBIN": {
        "instrument_type": "STOCK",
        "strike_interval": 10,
        "lot_size": 750
    },

    "TCS": {
        "instrument_type": "STOCK",
        "strike_interval": 10,
        "lot_size": 175
    }

}


def get(symbol):

    return INSTRUMENTS.get(
        symbol,
        {
            "instrument_type": "STOCK",
            "strike_interval": 10,
            "lot_size": 1
        }
    )