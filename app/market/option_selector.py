"""Option selection based exclusively on validated chain contracts."""

from app.market.instrument_master import get_option_chain


class OptionSelector:
    def __init__(self, option_chain_provider=get_option_chain):
        self.option_chain_provider = option_chain_provider

    def analyze(self, snapshot):
        snapshot.strike = "-"
        snapshot.expiry = "-"
        snapshot.option_symbol = "-"
        snapshot.option_reason = "No active trade lifecycle"

        # Recommendations are entry-only.  Holds and exits retain the lifecycle
        # action, but do not produce a fresh contract recommendation.
        if snapshot.lifecycle_state not in {"NEW BUY", "CONFIRMED"}:
            return snapshot

        chain = self.option_chain_provider(snapshot.symbol) or []
        contracts = [
            contract for contract in chain
            if contract.get("option_type") == snapshot.option_type
            and contract.get("strike") is not None
            and contract.get("symbol")
            and contract.get("expiry")
        ]

        if not contracts:
            snapshot.option_reason = "No validated option chain available"
            return snapshot

        contract = min(
            contracts,
            key=lambda item: abs(float(item["strike"]) - snapshot.ltp),
        )
        snapshot.strike = f'{contract["strike"]} {snapshot.option_type}'
        snapshot.expiry = str(contract["expiry"])
        snapshot.option_symbol = contract["symbol"]
        snapshot.option_reason = "Validated option-chain contract"
        return snapshot
