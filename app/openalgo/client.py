"""
OAMI Enterprise
OpenAlgo Client
"""

from app.openalgo.rest import OpenAlgoRESTClient


class OpenAlgoClient:
    """
    Main OpenAlgo Client
    """

    def __init__(
        self,
        rest_url: str,
        api_key: str,
        timeout: int = 10,
    ):

        self.rest = OpenAlgoRESTClient(
            rest_url=rest_url,
            api_key=api_key,
            timeout=timeout,
        )