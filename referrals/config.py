import os

from dotenv import load_dotenv

load_dotenv()


class Config:
    BASE_REFERRAL_LINK = os.getenv('BASE_REFERRAL_LINK')
    BASE_EMAIL = os.getenv('BASE_EMAIL')


config = Config()
