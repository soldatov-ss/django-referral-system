Installation Guide
==================

Follow these steps to install and set up `django-referral-system`:

1. Install the package via pip:

   .. code-block:: bash

      pip install django-referral-system

2. Add referrals to your `INSTALLED_APPS` in `settings.py`:

   .. code-block:: python

      INSTALLED_APPS = [
          # other apps
          'referrals',
      ]

3. Add to `urls.py`:

   .. code-block:: python

      from django.urls import path, include

      urlpatterns = [
          # Other URL patterns...
          path('referrals/', include("referrals.urls")),
      ]

4. Apply Migrations:

   .. code-block:: bash

      python manage.py migrate

5. Create a Referral Program:

   After installation, you can create a new referral program using the provided management command.
   If this program is set to active, any previous active referral programs will be deactivated automatically.

   .. code-block:: bash

      python manage.py create_referral_program --name="My Referral Program" --commission-rate=5.00 --min-withdrawal-balance=10.00
