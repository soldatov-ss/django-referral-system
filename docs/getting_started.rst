Getting Started
==================

1. Create a Referral Program
--------------------

After installation, you can create a new referral program using the provided management command. If this program is set to active, any previous active referral programs will be deactivated automatically.

.. code-block:: bash

   python manage.py create_referral_program --name="My Referral Program" --commission-rate=5.00 --min-withdrawal-balance=10.00

2. Set Up Environment Variables
--------------------

In order to generate referral links, you need to set up the following environment variables in your `.env` file:

.. code-block:: bash

   BASE_REFERRAL_LINK=http://localhost:8000/

This variable will be used to construct the referral links. Ensure that the base URL reflects your application's domain or local environment.
