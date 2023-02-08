import requests
import random
import string


def random_string_generator():
    str_size = 32
    allowed_chars = string.ascii_letters + string.punctuation
    str = ''.join(random.choice(allowed_chars) for x in range(str_size))
    print(str)
    return str


def call_amarpay(data):
    url = "https://secure.aamarpay.com/index.php"

    payload={'store_id': "onnow",
    'tran_id': random_string_generator(),
    'signature_key': "e4ff45ae2ebf159304663a36daa3f29e",
    'success_url': data["success_url"],
    'fail_url': data["fail_url"],
    'cancel_url': data["cancel_url"],
    'amount': int(data["amount"]),
    'currency': data["currency"],
    'desc': data["desc"],
    'cus_name': data["cus_name"],
    'cus_email': data["cus_email"],
    'cus_add1': data["cus_add1"],
    'cus_add2': data["cus_add2"],
    'cus_city': data["cus_city"],
    'cus_state': data["cus_state"],
    'cus_postcode': data["cus_postcode"],
    'cus_country': data["cus_country"],
    'cus_phone': data["cus_phone"],
    'type': 'json'}
    files=[

    ]
    headers = {}

    response = requests.request("POST", url, headers=headers, data=payload, files=files)

    return response