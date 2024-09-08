Wise Payouts
============

This section explains how the `PromoterPayoutService` handles sending payouts via Wise to eligible promoters.

1. Sending Wise Payouts
------------------------

The `send_wise_csv_for_promoters_payouts` method is responsible for generating a CSV file for Wise payouts and processing payouts for eligible promoters. It checks which promoters have a balance that meets or exceeds their minimum withdrawal amount and creates payouts for those promoters.

- **Method**: `send_wise_csv_for_promoters_payouts`

.. code-block:: python

    promoter_payout_service.send_wise_csv_for_promoters_payouts()

### Example

Assume a promoter has a balance of $100, which meets or exceeds their minimum withdrawal balance of $50. The system will generate a Wise payout for that promoter and include the following data in the CSV file:

.. code-block:: csv

    name,recipientEmail,amount,sourceCurrency,targetCurrency,amountCurrency,type
    John Doe,johndoe@example.com,100.00,USD,USD,target,EMAIL

### Key Points:

- **Payout Method**: The `payout_method` for these payouts is set to `'wise'`, and the `EMAIL` type is used, meaning payouts are processed based on the recipient’s email address.
- **Currency**: The payout currency is set to USD by default, but it can be changed by passing additional arguments to the method.
- **Balance Check**: Only promoters with a balance greater than or equal to their `min_withdrawal_balance` will be included in the payout.

2. CSV Generation
------------------

The method generates the CSV data for Wise using a pandas DataFrame. The resulting CSV string can be sent to Wise for processing.

### Example CSV Data

.. code-block:: csv

    name,recipientEmail,amount,sourceCurrency,targetCurrency,amountCurrency,type
    Jane Smith,janesmith@example.com,150.00,USD,USD,target,EMAIL
    John Doe,johndoe@example.com,100.00,USD,USD,target,EMAIL

This CSV file contains all the necessary information to process payouts through Wise, ensuring that the correct amount is paid to the corresponding recipient via email.

3. Payout Creation
-------------------

After generating the payout data, the service automatically creates a payout record for each eligible promoter and marks their pending commissions as paid.

- **Method**: `create_payout`

.. code-block:: python

    promoter_payout_service.create_payout(
        promoter=promoter_instance,
        amount=promoter_instance.current_balance,
        payout_method='wise'
    )

This method saves a `PromoterPayout` record for each promoter, and any commissions marked as "pending" are updated to "paid".

.. note::

    Ensure that the promoters have a valid payout method (Wise) and that their balance meets the minimum withdrawal requirement to process payouts. The system will skip promoters who do not meet these conditions.
