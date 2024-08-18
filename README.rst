============
django-referrals
============



Detailed documentation is in the "docs" directory.

Quick start
-----------

1. Add "referrals" to your INSTALLED_APPS setting like this::

    INSTALLED_APPS = [
        ...,
        "referrals",
    ]

2. Include the polls URLconf in your project urls.py like this::

    path("referrals/", include("django-referrals.urls")),

3. Run ``python manage.py migrate`` to create the models.

4. Start the development server and visit the admin to create a poll.

5. Visit the ``/referrals/`` URL to participate in the poll.