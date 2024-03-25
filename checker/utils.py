from json import JSONDecodeError
from typing import Optional

import requests
from django.conf import settings
from requests import Session
from requests.exceptions import HTTPError

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
    except HTTPError | JSONDecodeError as e:
        print(f"Failed to verify reCAPTCHA: {e}")
        return False


def get_robots_link(client: Session, base_url: str) -> Optional[str]:
    """
    Retrieves the URL of the robots.txt file for a given base URL using the provided HTTP client.

    :param client: The HTTP client session to use for making the request.
    :param base_url: The base URL for which to retrieve the robots.txt file.
    :return: The URL of the robots.txt file if it exists and can be accessed, None otherwise.
    """
    robots_url = base_url + "/robots.txt"
    try:
        r = client.head(robots_url)
        r.raise_for_status()
        return robots_url
    except HTTPError as e:
        print(f"Failed to get robots.txt: {e}")
        return None
