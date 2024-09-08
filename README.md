# django-referral-system

![Documentation Status](https://readthedocs.org/projects/django-referral-system/badge/?version=latest)
[![PyPI version](https://badge.fury.io/py/django-referral-system.svg)](https://badge.fury.io/py/django-referral-system)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](https://github.com/soldatov-ss/django-referral-system/blob/main/LICENSE)
[![Python Versions](https://img.shields.io/pypi/pyversions/django-referral-system.svg)](https://pypi.org/project/django-referral-system/)
[![Coverage Status](https://coveralls.io/repos/github/soldatov-ss/django-referral-system/badge.svg?branch=main)](https://coveralls.io/github/soldatov-ss/django-referral-system?branch=main)

A Django app for managing referral programs, promoters, referrals, and tracking referral performance with features like commission setting, invitation management, and Wise payouts.
## Documentation

Full documentation is available at [Read the Docs](https://django-referral-system.readthedocs.io/en/latest/index.html).

## Features
* **Promoter Management**: Easily create and manage promoters who can invite referrals to join your platform.
* **Referral Tracking**: Promoters can track their list of referrals, including invitation details, sign-up status, and more.
* **Earnings Monitoring**: Promoters can view their recent earnings, aggregated by day for the last 7 days, including commissions from successful referrals.
* **Commission-Based Rewards**: Promoters earn money by receiving commissions from referrals they invite, with configurable commission rates based on the active referral program.
* **Customizable Payout Methods**: Promoters can set and update their preferred payout methods (e.g., Wise) and minimum withdrawal balances.
* **Wise Payout Integration**: Automatically generate CSV files for Wise payouts and process payouts for promoters whose balance meets the minimum withdrawal amount.
* **Email Invitation**: Promoters can send invitation emails to potential referrals with a custom HTML template. Ensure that the `BASE_REFERRAL_LINK` and `BASE_EMAIL` environment variables are properly set.
* **Refund Handling**: Automatically adjust promoter commissions in case of user refunds, ensuring that promoters only earn commissions for completed transactions.
* **Referral Program Flexibility**: Only one referral program can be active at a time, allowing for focused and streamlined referral management.
* **Detailed Payout History**: Promoters can view their full payout history, providing transparency and easy tracking of payment status.
* **Click Tracking**: Keep track of how many times a referral link has been clicked, helping promoters measure the performance of their referral efforts.

## Installation

1. Install the package via pip:

```bash
pip install django-referral-system
```

2. Add referrals to your INSTALLED_APPS in settings.py:

```python
INSTALLED_APPS = [
    # other apps
    'referrals',
]
```

3. Add to urls.py
```python
from django.urls import path, include

urlpatterns = [
    # Other URL patterns...
    path('referrals/', include("referrals.urls")),
]
```
4. Apply Migrations
```bash
python manage.py migrate
```

5. Create a Referral Program    
After installation, you can create a new referral program using the provided management command:
If this program is set to active, any previous active referral programs will be deactivated automatically.
```bash
python manage.py create_referral_program --name="My Referral Program" --commission-rate=5.00 --min-withdrawal-balance=10.00
```


### License
This package is licensed under the MIT License. See the LICENSE file for more details.

### Contributing
If you find any issues or have suggestions, feel free to open an issue or submit a pull request.

To support this project, please give star it on Github. ![github star](docs/github-star.png)