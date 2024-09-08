Promoter Logic
==============


1. Promoter Creation
--------------------

A promoter is created by associating a `User` with a referral token and referral link. Promoters are responsible for sending out referral links, tracking referrals, and earning commissions.

You can retrieve or create a promoter for a user using the following API action:

- **Retrieve Promoter**: This endpoint retrieves or creates a promoter for the authenticated user.

.. code-block:: bash

    GET http://localhost:8000/referrals/promoter
    Accept: application/json
    Authorization: Bearer your_token


Example response:

.. code-block:: json

    {
      "id": 2,
      "user": 1,
      "referralToken": "6B86B273FF",
      "referralLink": "http://localhost:8000/?ref=6B86B273FF",
      "currentBalance": 0,
      "totalEarned": 0,
      "totalPaid": 0,
      "created": "2024-08-24T12:12:03.374694Z",
      "updated": "2024-09-08T09:11:15.032367Z",
      "linkClicked": 0,
      "minWithdrawalBalance": "20.00",
      "commissionRate": 15.0
    }

2. Setting the Payout Method
-----------------------------

Promoters can set their preferred payout method using the following API action:

- **Set Payout Method**: This endpoint allows promoters to set their payout method (e.g., Wise, Crypto) and payment address (email or wallet address).

.. code-block:: bash

    PATCH http://localhost:8000/referrals/set-payout-method/
    Content-Type: application/json
    Authorization: Bearer your_token

    {
      "method": "wise",
      "payment_address": "example@gmail.com"
    }


Example response:

.. code-block:: json

    {
      "id": 2,
      "user": 1,
      "referralToken": "6B86B273FF",
      "referralLink": "http://localhost:8000/?ref=6B86B273FF",
      "activePayoutMethod": {
        "method": "wise",
        "paymentAddress": "example@gmail.com"
      },
      "currentBalance": 0,
      "totalEarned": 0,
      "totalPaid": 0,
      "created": "2024-08-24T12:12:03.374694Z",
      "updated": "2024-09-08T09:11:15.032367Z",
      "linkClicked": 0,
      "minWithdrawalBalance": "20.00",
      "commissionRate": 15.0
    }

The promoter’s payout method is used when processing their earnings.

3. Tracking Referrals and Earnings
-----------------------------------

Once a promoter is created, they can start sharing their referral link. The system tracks clicks on the referral link and the earnings generated from those referrals. Promoters can retrieve their recent earnings and view a breakdown of their performance over the last 7 days.

To view the promoter's recent earnings:

.. code-block:: bash

    GET http://localhost:8000/referrals/promoter-recent-earnings
    Accept: application/json
    Authorization: Bearer your_token

Example response:

.. code-block:: json

    [
        {
            "day": "Mon",
            "value": 50
        },
        {
            "day": "Tue",
            "value": 0
        },
        {
            "day": "Wed",
            "value": 30
        },
        {
            "day": "Thu",
            "value": 70
        },
        {
            "day": "Fri",
            "value": 20
        },
        {
            "day": "Sat",
            "value": 0
        },
        {
            "day": "Sun",
            "value": 10
        }
    ]

The response contains a list of the last 7 days, with each day showing the corresponding earnings value. Even if no earnings occurred on a particular day, it is still represented with a value of `0`. The earnings are grouped by the day of the week when they were created.

4. Incrementing Link Clicks
----------------------------

Every time a referral link is clicked, the system can increment the count of link clicks for the promoter. This can be done via the following API action:

.. code-block:: bash

    POST http://localhost:8000/referrals/increment-link-clicked/
    Content-Type: application/json
    Authorization: Bearer your_token

    {
      "referral_token": "6B86B273FF"
    }


Example response:

.. code-block:: json

    {
      "message": "Link clicked count incremented successfully"
    }