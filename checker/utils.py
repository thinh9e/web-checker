from json import JSONDecodeError

import requests
from django.conf import settings
from requests.exceptions import RequestException

REQUEST_TIMEOUT = 30


def verify_captcha(response: str, user_ip: str) -> bool:
    """
    Verifies the reCAPTCHA response using the Google reCAPTCHA API.

    :param response: The reCAPTCHA response token provided by the user.
    :param user_ip: The IP address of the user submitting the reCAPTCHA.
    :return: True if the reCAPTCHA verification is successful, False otherwise.
    """
    if settings.DEBUG:
        print("Skipping reCAPTCHA verification in debug mode.")
        return True

    url = "https://www.google.com/recaptcha/api/siteverify"
    data = {
        "secret": settings.GOOGLE_RECAPTCHA_SECRET_KEY,
        "response": response,
        "remoteip": user_ip,
    }

    try:
        verify = requests.post(url=url, data=data)
        result: dict = verify.json()
        return result.get("success")
    except RequestException | JSONDecodeError as e:
        print(f"Failed to verify reCAPTCHA: {e}")
        return False
