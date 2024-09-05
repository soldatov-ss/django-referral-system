# django-referral-system

A Django app for managing referral programs, promoters, referrals, and tracking referral performance with features like
commission setting, invitation management, and Wise payouts.

## Features
* **Promoter Management**: Easily create and manage promoters who can invite referrals to join your platform.
* **Referral Tracking**: Promoters can track their list of referrals, including invitation details, sign-up status, and more.
* **Earnings Monitoring**: Promoters can view their recent earnings, including commissions from successful referrals.
* **Commission-Based Rewards**: Promoters earn money by receiving commissions from referrals they invite, with configurable commission rates.
* **Customizable Payout Methods**: Promoters can set and update their preferred payout methods and minimum withdrawal balances.
* **Referral Link Creation**: Generate unique referral links that promoters can share to invite others to the platform.
* **Referral Program Flexibility**: Only one referral program can be active at a time, allowing for focused and streamlined referral management.
* **Detailed Payout History**: Promoters can view their full payout history, allowing for transparency and easy tracking of payment status.
* **Click Tracking**: Keep track of how many times a referral link has been clicked.

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
4: Apply Migrations
```bash
python manage.py migrate
```


### License
This package is licensed under the MIT License. See the LICENSE file for more details.

### Contributing
If you find any issues or have suggestions, feel free to open an issue or submit a pull request.