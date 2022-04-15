import requests

from bot import SLOTS_URL, get_slot_header
from check_all import CHECK_URL, get_validate_header


def main():
    api_key = open("keys.txt").read().splitlines()[0]

    while True:
        response = requests.get(SLOTS_URL, headers=get_slot_header(api_key))
        result = eval(response.text)
        print(result)

        response = requests.get(CHECK_URL, headers=get_validate_header(api_key))
        result = eval(response.text)
        print(result)

        print("=" * 10)


if __name__ == "__main__":
    main()
