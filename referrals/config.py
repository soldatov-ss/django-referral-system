import os

from django.core.exceptions import ImproperlyConfigured
from dotenv import load_dotenv

load_dotenv()


class Config:
    BASE_REFERRAL_LINK = os.getenv("BASE_REFERRAL_LINK")
    BASE_EMAIL = os.getenv("BASE_EMAIL")

    def __getattribute__(self, name):
        value = super().__getattribute__(name)
        if name == "BASE_REFERRAL_LINK" and value is None:
            raise ImproperlyConfigured(
                "django-referral-system: BASE_REFERRAL_LINK is not configured. "
                "Set the BASE_REFERRAL_LINK environment variable."
            )
        return value


config = Config()
