Referrals Logic
===============

Referral Creation
--------------------

Referrals are created when a promoter shares their referral link, and a new user signs up through that link. This process can be managed through the API.

.. code-block:: bash

    POST http://localhost:8000/referrals/
    Content-Type: application/json
    Authorization: Bearer your_token

    {
      "email": "john_doe@example.com",
      "referral_token": "6B86B273FF",
      "referral_source": "email"
    }

# Optional field referral_source: 'email' or 'link' (by default: link)

Example response:

.. code-block:: json

    {
      "userId": 2,
      "email": "john_doe@example.com",
      "status": "signup",
      "invitationMethod": "email",
      "commissionRate": "15.00",
      "commissionAmount": 0,
      "commissionStatus": null
    }
