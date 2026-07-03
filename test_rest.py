"""
OpenAlgo REST Test
"""

from app.openalgo.client import OpenAlgoClient

REST_URL = "https://ualgo.arvelstudios.com"
API_KEY = "YOUR_OPENALGO_API_KEY"


def main():

    client = OpenAlgoClient(
        rest_url=REST_URL,
        api_key=API_KEY,
    )

    print("=" * 60)
    print("OPENALGO CLIENT CREATED")
    print("=" * 60)

    print(client)


if __name__ == "__main__":
    main()