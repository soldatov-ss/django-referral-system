Referral Service Logic
======================

This section explains the backend logic of the `ReferralService` class, which handles various operations related to referral programs.

Getting the Referrer by User ID
----------------------------------

The service can retrieve the referrer (promoter) associated with a specific user ID.

- **Method**: `get_referrer_by_user_id`

.. code-block:: python

    referrer = ReferralService.get_referrer_by_user_id(user_id=1)


Handling Subscription Purchases
----------------------------------

When a referred user purchases a subscription, the `ReferralService` updates the referral status to `Active` and generates a commission for the promoter.

- **Method**: `handle_purchase_subscription`

.. code-block:: python

    ReferralService.handle_purchase_subscription(
        user=user_instance,
        amount_paid=10000,  # original paid amount in cents
        invoice_external_id=12345   # an optional external invoice ID (e.g. chargeebe_id).
    )


The method updates the user's referral status and calculates the commission based on the amount paid.

Handling Refunds
--------------------

If a referred user requests a refund, the service updates the referral status to `Refund` and processes a refund commission.

- **Method**: `handle_user_refund`

.. code-block:: python

    ReferralService.handle_user_refund(
        user=user_instance,
        amount_refunded=5000,   # refunded amount in cents
        amount_paid=10000,  # original paid amount in cents
        invoice_external_id=12345   # an optional external invoice ID (e.g. chargeebe_id).
    )


The method sets the referral status to `Refund` and adjusts the commission accordingly.

Example refund scenario:

- Original Payment: $100 (commission: $10)
- Amount Refunded: $50
- Adjusted Commission: The promoter’s commission is reduced proportionally to $5, and a new refund commission of -$5 is recorded.

### Example

If a promoter originally earned a $10 commission on a $100 subscription, and the user is refunded 50% ($50), the promoter’s adjusted commission will be:

Example refund record:

.. code-block:: python

    {
        "amount": -5,  # negative value representing the refund
        "status": "refund",
        "invoice_external_id": 12345
    }


In this case, the promoter's final commission will be $5, reflecting the amount that corresponds to the portion of the user's payment that was not refunded.

.. note::

    It is possible for a promoter to have a negative balance if multiple refunds are processed and the refunded amounts exceed the promoter’s total earned commissions. This can occur if the promoter has already been paid for referrals, but the referred users later request refunds.


Sending Referral Invitation Emails
----------------------------------

The `send_referral_invitation_email` method allows promoters to send an email invitation containing a referral link.

- **Method**: `send_referral_invitation_email`

.. code-block:: python

    ReferralService.send_referral_invitation_email(
        emails_to=["invitee@example.com"],
        invitation_link="http://localhost:8000/?ref=6B86B273FF",
        promoter_full_name="John Doe",
        subject="Join us!",
        template_path="app_name/referral_invitation.html"
    )

### Key Requirements

1. **Environment Variables**:

Make sure to set the following environment variables in your `.env` file before sending referral invitation emails:

   .. code-block:: bash

       BASE_REFERRAL_LINK=
       BASE_EMAIL=
These variables are necessary for generating the referral link and setting the "from" email address.


2. **Correct Template Path**:

   You must correctly pass the path to the HTML email template when calling this method.

   Example of saving an email template in Django:

   - Full Path: `app_name/templates/app_name/referral_invitation.html`

.. note::

    The referral link sent by email contains an extra param `ref-source=email` for future tracking.

    .. code-block:: bash

        GET http://localhost:8000/?ref=6B86B273FF&ref-source=email

