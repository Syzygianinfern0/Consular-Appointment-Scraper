import requests

CHECK_URL = "https://app.checkvisaslots.com/validate/v1"


def get_validate_header(api_key):
    return {
        "origin": "chrome-extension://beepaenfejnphdgnkmccjcfiieihhogl",
        "x-api-key": api_key,
    }


def main():
    api_keys = open("keys.txt").read().splitlines()
    for key in api_keys:
        response = requests.get(CHECK_URL, headers=get_validate_header(key))
        result = eval(response.text)
        print(result)


if __name__ == "__main__":
    main()
