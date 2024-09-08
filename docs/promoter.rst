Promoter Logic
==============


Promoter Creation
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


Get Referral Link
-----------------------------
Promoters can retrieve their unique referral link, which they can share with others to invite referrals.

.. code-block:: bash

    GET http://localhost:8000/referrals/get-referral-link
    Accept: application/json
    Authorization: Bearer your_token

Example response:

.. code-block:: json

    {
        "referralLink": "http://localhost:8000/?ref=6B86B273FF"
    }

Set the Payout Method
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

Tracking Referrals and Earnings
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

Incrementing Link Clicks
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



List of Referrals
----------------------------

Promoters can retrieve a list of referrals they have invited.

.. code-block:: bash

    GET http://localhost:8000/referrals/
    Accept: application/json
    Authorization: Bearer your_token

Example response:

.. code-block:: json

    {
      "count": 1,
      "pages": 1,
      "results": [
        {
          "userId": 2,
          "email": "john_doe@example.com",
          "status": "signup",
          "invitationMethod": "email",
          "commissionRate": "15.00",
          "commissionAmount": 0,
          "commissionStatus": null
        }
      ]
    }


Promoter Payment History
----------------------------

Promoters can retrieve a history of their payouts, including details such as the payout amount and the date it was processed.

.. code-block:: bash

    GET http://localhost:8000/referrals/payouts
    Accept: application/json
    Authorization: Bearer your_token

Example response:

.. code-block:: json

    [
        {
            "id": 1,
            "created": "2024-08-30T10:00:00Z",
            "amount": 100
        },
        {
            "id": 2,
            "created": "2024-08-25T15:30:00Z",
            "amount": 50
        }
    ]

This endpoint returns a list of payouts made to the authenticated promoter. Each payout includes the payout ID, the date and time when the payout was created, and the payout amount.

Set Minimum Withdrawal Balance
---------------------------------

Promoters can set a custom minimum withdrawal balance. This balance determines the minimum amount the promoter needs to accumulate before they can request a payout.

.. code-block:: bash

    PATCH http://localhost:8000/referrals/set-min-withdrawal-balance/
    Content-Type: application/json
    Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzI1NzkwMTc2LCJpYXQiOjE3MjU3ODkyNzYsImp0aSI6ImJiMDFhMTJhNTZhODQyODNhMjJjYzg0NzIwZDFiMGVlIiwidXNlcl9pZCI6MX0.MqYcy-UTPeQY6Dy4gIMA3LMBOVHJihsHoeUpJSqNb1w

    {
      "min_withdrawal_balance": 50.00
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
      "updated": "2024-09-08T09:54:46.883465Z",
      "linkClicked": 1,
      "minWithdrawalBalance": "50.00",
      "commissionRate": 15.0
    }