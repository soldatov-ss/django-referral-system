.. django-referral-system documentation master file, created by
   sphinx-quickstart on Fri Sep  6 18:22:44 2024.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to django-referral-system's documentation!
==================================================

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   installation
   getting_started
   promoter
   referral
   referral_service
   wise_payouts


Key Features
============

* **Promoter Management**: Easily create and manage promoters who can invite referrals to join your platform.
* **Referral Tracking**: Promoters can track their list of referrals, including invitation details, sign-up status, and more.
* **Earnings Monitoring**: Promoters can view their recent earnings, aggregated by day for the last 7 days, including commissions from successful referrals.
* **Commission-Based Rewards**: Promoters earn money by receiving commissions from referrals they invite, with configurable commission rates based on the active referral program.
* **Customizable Payout Methods**: Promoters can set and update their preferred payout methods (e.g., Wise) and minimum withdrawal balances.
* **Wise Payout Integration**: Automatically generate CSV files for Wise payouts and process payouts for promoters whose balance meets the minimum withdrawal amount.
* **Email Invitation**: Promoters can send invitation emails to potential referrals with a custom HTML template. Ensure that the `BASE_REFERRAL_LINK` and `BASE_EMAIL` environment variables are properly set.
* **Refund Handling**: Automatically adjust promoter commissions in case of user refunds, ensuring that promoters only earn commissions for completed transactions.
* **Referral Program Flexibility**: Only one referral program can be active at a time, allowing for focused and streamlined referral management.
* **Detailed Payout History**: Promoters can view their full payout history, providing transparency and easy tracking of payment status.
* **Click Tracking**: Keep track of how many times a referral link has been clicked, helping promoters measure the performance of their referral efforts.

.. note::
   For detailed setup instructions, see the :ref:`installation` page.

License
=======

This package is licensed under the MIT License. See the LICENSE file for more details.

Contributing
============

If you find any issues or have suggestions, feel free to open an issue or submit a pull request.