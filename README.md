# XRPL-Developer-Grants-Wave-4
XRPL Developer Grants Wave 4 -  Proof of concept or prototype 

Code to swap the device-token KWH by the TGO token.

The code needs error handling improvements, but its functionality can be evaluated.

# How it works:
1) It uses the crosspayment payment type mechanism to do the token swap operation.
2) The Device's XRP Ledger account is pre-loaded with an ammount of device-token KWH.
3) Then, it measures the energy produced by a solar power plant. In this example, the code queries
the API of the manufacturer of the power inverter to obtain the amount of energy produced by it.
4) After measuring the energy produced, it sends an equivalent amount of KWH tokens to
pay for TGO token to be sent to the device's owner XRPL account, as a cross-currency payment transaction.
5) The issuer account keeps a KWH-TGO pair order in the order-book at a given quote in such a way that
the cross-payment transaction finds a path in the XRP Ledger to swap the device-token (KWH) by the
TGO token at the rate given by the issuer order, whose value will be determined by the oracle code
to be developed during the grant period.
