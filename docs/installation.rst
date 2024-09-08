Installation Guide
==================

Follow these steps to install and set up `django-referral-system`:

1. Install the package via pip:
--------------------

   .. code-block:: bash

      pip install django-referral-system

2. Add referrals to your `INSTALLED_APPS` in `settings.py`:
--------------------

   .. code-block:: python

      INSTALLED_APPS = [
          # other apps
          'referrals',
      ]

3. Add to `urls.py`:
--------------------

   .. code-block:: python

      from django.urls import path, include

      urlpatterns = [
          # Other URL patterns...
          path('referrals/', include("referrals.urls")),
      ]

4. Apply Migrations:
--------------------

   .. code-block:: bash

      python manage.py migrate
