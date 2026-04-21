# django-referral-system

[![CI](https://github.com/soldatov-ss/django-referral-system/actions/workflows/ci.yml/badge.svg)](https://github.com/soldatov-ss/django-referral-system/actions/workflows/ci.yml)
[![PyPI version](https://badge.fury.io/py/django-referral-system.svg)](https://badge.fury.io/py/django-referral-system)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](https://github.com/soldatov-ss/django-referral-system/blob/main/LICENSE)
[![Python Versions](https://img.shields.io/badge/python-3.9%20|%203.10%20|%203.11%20|%203.12%20|%203.13%20|%203.14-blue.svg)](https://pypi.org/project/django-referral-system/)
[![Coverage Status](https://coveralls.io/repos/github/soldatov-ss/django-referral-system/badge.svg?branch=main)](https://coveralls.io/github/soldatov-ss/django-referral-system?branch=main)

**A plug-and-play Django referral engine.** Track promoters, reward commissions, manage payouts — all wired up in minutes.

Full documentation: [Read the Docs](https://django-referral-system.readthedocs.io/en/latest/index.html)

---

## What it does

| Area | Capability |
|------|------------|
| **Promoters** | Create and manage promoters with unique referral tokens and links |
| **Referral tracking** | Track sign-ups, activation status, and click counts per link |
| **Commissions** | Configurable commission rates tied to the active referral program |
| **Payouts** | Wise CSV export; auto-skip promoters below minimum withdrawal balance |
| **Refunds** | Commission is automatically reversed when a referred user refunds |
| **Email invitations** | Send branded HTML invite emails via a custom template |

Only one referral program can be active at a time, keeping the logic focused and predictable.

---

## Quick start

**1. Install**

```bash
pip install django-referral-system
```

Requires Python 3.9 – 3.14 and Django 4.2+.

**2. Add to `INSTALLED_APPS`**

```python
INSTALLED_APPS = [
    ...
    "referrals",
]
```

**3. Mount the URLs**

```python
from django.urls import path, include

urlpatterns = [
    ...
    path("referrals/", include("referrals.urls")),
]
```

**4. Migrate**

```bash
python manage.py migrate
```

**5. Create a referral program**

```bash
python manage.py create_referral_program \
    --name="My Referral Program" \
    --commission-rate=5.00 \
    --min-withdrawal-balance=10.00
```

Setting a program as active automatically deactivates any existing active program.

---

## Environment variables

| Variable | Purpose |
|----------|---------|
| `BASE_REFERRAL_LINK` | Base URL used when generating referral links |
| `BASE_EMAIL` | Sender address for invitation emails |

---

## License

MIT — see [LICENSE](LICENSE) for details.

## Contributing

Issues and pull requests are welcome. If this project saves you time, a star on GitHub goes a long way. ![github star](docs/github-star.png)
