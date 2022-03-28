# Things Go Online example code for the XRPL-Developer-Grants-Wave-3.
# Code to swap the device-token KWH by the TGO token.
# The code needs error handling improvements, but its functionality can be evaluated.
# How it works:
# 1) It uses the crosspayment payment type mechanism to do the token swap operation.
# 2) The Device's XRP Ledger account is pre-loaded with an ammount of device-token KWH.
# 3) Then, it measures the energy produced by a solar power plant. In this example, the code queries
# the API of the manufacturer of the power inverter to obtain the amount of energy produced by it.
# 4) After measuring the energy produced, it sends an equivalent amount of KWH tokens to
# pay for TGO token to be sent to the device's owner XRPL account, as a cross-payment transaction.
# 5) The issuer account keeps a KWH-TGO pair order in the order-book at a given quote in such a way that
# the cross-payment transaction finds a path in the XRP Ledger to swap the device-token (KWH) by the
# TGO token at the rate given by the issuer order, whose value will be determined by the oracle code
# to be developed during the grant period.
#
import json
import asyncio
import websockets
import base58
import time
import requests

verbose = True

DeviceAccount = 'r...'# The device account that tokenizes the sustainability measurement as a device token, called in this example KWH.
IssuerAccount = 'r...'# The issuer account of the KWH and TGO tokens. In this example the issuer is the same for both tokens.
DestAccount = 'r...'# The device's owner account to receive TGO in exchange to the device token KWH

b58MemoFormat = base58.b58encode_check("application/json", alphabet=base58.XRP_ALPHABET)
b58HexMemoFormat =  bytes(b58MemoFormat).hex().upper()

# Cross-payment transaction
async def Swap(value, LLS):
  xotValue = value*500 # This fixed quote value will be changed in the future for a query to TGO Oracle's service API
  async with websockets.connect("ws://localhost:6060") as websocket:
    # transaction to swap the device token KWH by the TGO token
    await websocket.send('{"id": 1, "command": "submit", "tx_json": { "TransactionType": "Payment", "Account": "' + DeviceAccount +  '", "Destination" : "' + DestAccount + '", "SendMax": {"currency": "KWH", "value": "' + str(value) + '", "issuer": "' + IssuerAccount + '"}, "Amount": { "currency": "TGO", "issuer": "' + IssuerAccount + '", "value": "' + str(xotValue) + '" }, "Fee": "20", "LastLedgerSequence": "' + str(LLS) + '", "Memos": [ { "Memo": { "MemoFormat": "'+ b58HexMemoFormat +'", "MemoData": "'+ b58HexMemo + '" } } ]}, "secret": "s..."}')
    async for message in websocket:
      return message

# Get the Ledger Current Index
async def LLSeq():
  async with websockets.connect("ws://localhost:6060") as websocket:
    await websocket.send('{"id": 2, "command": "ledger_current"}')
    async for message in websocket:
      return message

def VERBOSE(msg):
  if verbose:
    print(msg)

# Info to be published as the transaction's Memo 
x = {
  "name": "Solar Energy Generated",
  "unit": "kWh",
  "delta_value": 0,
  "total_value": 0
}

etotal_inv01_ant = 0
etotal_inv02_ant = 0

while 1:
  # Login into the website API
  url = 'https://www.semsportal.com/api/v2/Common/CrossLogin'
  payload = '{"account":"...","pwd":"..."}'# If you need to test the code,, please ask us the account and password
  headers = {'content-type': 'application/json', 'Connect': 'keep-alive', 'User-Agent': 'PVMaster/2.1.0 (iPhone; iOS 13.0; Scale/2.00)', 'Accept-Language': 'en;q=1', 'Token': '{"version":"v2.1.0","client":"ios","language":"en"}' }
  r = requests.post(url, data=payload, headers=headers)
  login = r.json()

  # request the API info about the energy produced by the power inverters
  url = 'https://www.semsportal.com/api/v2/PowerStation/GetMonitorDetailByPowerstationId'
  payload = '{"powerStationId":"a9eba054-9b0a-4a57-8dd9-6b1e3bd4960d"}'
  headers = {'Content-Type': 'application/json', 'Accept': '*/*', 'User-Agent': 'PVMaster/2.1.0 (iPhone; iOS 13.0; Scale/2.00)', 'Accept-Language': 'DE;q=1', 'Token': json.dumps(login["data"])}
  r = requests.post(url, data=payload, headers=headers)
  PowerSt = r.json()

  #There are two inverters. So we need to get the energy production from both
  etotal_inv01 = PowerSt["data"]["inverter"][0]["etotal"]
  etotal_inv02 = PowerSt["data"]["inverter"][1]["etotal"]

  # We need to calculate the amount of energy produced since the last Loop calculation
  if (etotal_inv01_ant):
    deltaE_inv01 = (etotal_inv01 - etotal_inv01_ant)
  else:
    deltaE_inv01 = 0

  if (etotal_inv02_ant):
    deltaE_inv02 = (etotal_inv02 - etotal_inv02_ant)
  else:
    deltaE_inv02 = 0
  etotal_inv01_ant =  etotal_inv01
  etotal_inv02_ant =  etotal_inv02

  # Here we have the amount of energy produced since the last Loop calculation
  deltaE = deltaE_inv01 + deltaE_inv02

  x["delta_value"] = deltaE
  # Here we have the total amount of energy produced by the power inverters since they've started to operate
  x["total_value"] = (etotal_inv01 + etotal_inv02)
  
  # Prepare a Json to be sent as a Memo
  y = json.dumps(x)
  b58HexMemo =  bytes(y,"utf-8").hex().upper()
  
  if deltaE>0:
    # Get the Ledger current index
    respLLSeq = asyncio.run(LLSeq())
    rLLSeq = json.loads(respLLSeq)
    if(('status' in rLLSeq) and (rLLSeq["status"] == "success")):
      if(('result' in rLLSeq) and ('ledger_current_index' in rLLSeq["result"])):
        # Send the cross-payment transaction to swap the device token KWH to TGO token
        respSwap = asyncio.run(Swap(deltaE, (int(rLLSeq["result"]["ledger_current_index"]) + 15)))
        VERBOSE(respSwap)

  time.sleep(300)# execute the code at each 5 minutes

