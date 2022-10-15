# Things Go Online example code for the XRPL-Developer-Grants-Wave-4.
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
import csv
import asyncio
import websockets
import base58
import time
import requests
import datetime

verbose = True

DeviceAccount = 'rJoKE1LjfdHS61KgnTLtvWw76kxtxJnsQ2' # The device account that tokenizes the sustainability measurement as a device token, called in this example KWH.
DeviceTokenIssuerAccount = 'rKWH2NPtXn636uodWJ3dLLM7wHmyG2qpz6' # The issuer account of the KWH token. 
TGOIssuerAccount = 'rTGoNeK6vpu28U2oE5tiqhH3x8z2jBhxv' # The issuer account of the TGO tokens. 
DestAccount = 'rEWRDZamZN1JQk8nsD7xPVpXAYVtQMTsRg' # The device's owner account to receive TGO in exchange to the device token KWH
DeviceSecret = 'sh3tU4dLtgonrboUogMkdwhTVcGtM'
deviceToken = "KWH"
swapToken = "TGO"
GoodWeLogin = "..."
GoodWePass = "..."
addLLS = 4
TimeOutSeq = addLLS * 4
Fee = 10

b58MemoFormat = base58.b58encode_check("application/json", alphabet=base58.XRP_ALPHABET)
b58HexMemoFormat =  bytes(b58MemoFormat).hex().upper()

# Cross-payment transaction
async def Swap(value, LLS):
  xValue = value*10 # This fixed quote value will be changed in the future for a query to TGO Oracle's service API
  async with websockets.connect("ws://localhost:6006") as websocket:
    # transaction to swap the device token KWH by the TGO token
    await websocket.send('{"id": 1, "command": "submit", "tx_json": { "TransactionType": "Payment", "Account": "' + DeviceAccount +  '", "Destination" : "' + DestAccount + '", "SendMax": {"currency": "'+ deviceToken +'", "value": "' + str(value) + '", "issuer": "' + DeviceTokenIssuerAccount + '"}, "Amount": { "currency": "'+ swapToken +'", "issuer": "' + TGOIssuerAccount + '", "value": "' + str(xValue) + '" }, "Fee": "'+ str(Fee) +'", "LastLedgerSequence": "' + str(LLS) + '", "Memos": [ { "Memo": { "MemoFormat": "'+ b58HexMemoFormat +'", "MemoData": "'+ b58HexMemo + '" } } ]}, "secret": "'+ DeviceSecret +'"}')
    async for message in websocket:
      return message

# Get the Ledger Current Index
async def LLSeq():
  async with websockets.connect("ws://localhost:6006") as websocket:
    await websocket.send('{"id": 2, "command": "ledger_current"}')
    async for message in websocket:
      return message

# Check the transaction_hash status
async def TxHash(tx_hash):
  async with websockets.connect("ws://localhost:6006") as websocket:
    await websocket.send('{ "id": 1, "command": "tx", "transaction": "'+ tx_hash +'", "binary": false }')
    async for message in websocket:
      return message



def VERBOSE(msg):
  ts = time.time()
  if verbose:
    print(datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S') + " - " + msg)

# Info to be published as the transaction's Memo 
x = {
  "name": "Solar Energy Generated",
  "unit": "kWh",
  "delta_value": 0,
  "total_value": 0
}

etotal_inv01_ant = 0
etotal_inv02_ant = 0
firstrun = 1

filejson = {}
try:
  with open('lastenergy.json', 'r+', encoding='utf-8') as f:
    try:
      filejson = json.load(f)
    except ValueError:
      VERBOSE('Decoding JSON has failed')
    else:
      if('etotal_inv01_ant' in filejson):
        etotal_inv01_ant = filejson['etotal_inv01_ant']
        VERBOSE("Reading from json file: etotal_inv01_ant <" + str(etotal_inv01_ant) + ">")
        if(etotal_inv01_ant>0):
          firstrun = 0
      if('etotal_inv02_ant' in filejson):
        etotal_inv02_ant = filejson['etotal_inv02_ant']
        VERBOSE("Reading from json file: etotal_inv02_ant <" + str(etotal_inv02_ant) + ">")
        if(etotal_inv02_ant>0):
          firstrun = 0
except:
  VERBOSE('Error openning the file')
#except ValueError as e:
  #VERBOSE('Error openning the file'+e)

while 1:
  # Login into the website API
  url = 'https://www.semsportal.com/api/v2/Common/CrossLogin'
  payload = '{"account":"'+ GoodWeLogin +'","pwd":"'+ GoodWePass +'"}'# If you need to test the code,, please ask us the account and password
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
  VERBOSE("Reading from GoodWe: Etotal_inv01 = " + str(etotal_inv01))
  VERBOSE("Reading from GoodWe: Etotal_inv02 = " + str(etotal_inv02))

  if (firstrun and (etotal_inv01 > 0) and (etotal_inv02 > 0)):
    etotal_inv01_ant = etotal_inv01
    etotal_inv02_ant = etotal_inv02
    filejson = {'etotal_inv01_ant':0, 'etotal_inv02_ant':0}
    firstrun = 0


  # We need to calculate the amount of energy produced since the last Loop calculation
  if (etotal_inv01_ant):
    deltaE_inv01 = (etotal_inv01*10 - etotal_inv01_ant*10)/10
  else:
    deltaE_inv01 = 0

  if (etotal_inv02_ant):
    deltaE_inv02 = (etotal_inv02*10 - etotal_inv02_ant*10)/10
  else:
    deltaE_inv02 = 0

  # Here we have the amount of energy produced since the last Loop calculation
  deltaE = (deltaE_inv01*10 + deltaE_inv02*10)/10

  x["delta_value"] = deltaE
  # Here we have the total amount of energy produced by the power inverters since they've started to operate
  x["total_value"] = (etotal_inv01*10 + etotal_inv02*10)/10

  
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
        respSwap = asyncio.run(Swap(deltaE, (int(rLLSeq["result"]["ledger_current_index"]) + addLLS)))
        ts = time.time()
        rSwap = json.loads(respSwap)
        VERBOSE(str(rSwap))
        if(('status' in rSwap) and (rSwap["status"] == "success")):
          if(('result' in rSwap) and ('engine_result' in rSwap["result"])):
            if(rSwap["result"]["engine_result"] == "tesSUCCESS"):
              etotal_inv01_ant =  etotal_inv01
              etotal_inv02_ant =  etotal_inv02
              VERBOSE("Cross-Payment transaction: " + rSwap["result"]["engine_result"])
              VERBOSE("Energy Produced Registered in the Blockchain")
              filejson = {'etotal_inv01_ant':etotal_inv01_ant, 'etotal_inv02_ant':etotal_inv02_ant}
              try:
                with open('lastenergy.json', 'w+', encoding='utf-8') as f:
                  json.dump(filejson, f, ensure_ascii=True, indent=4)
              except ValueError:
                VERBOSE('Error openning the file')
              try:
                with open('history_registry.json', 'a', encoding='utf-8') as csvf:
                  history_writer = csv.writer(csvf, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
                  history_writer.writerow([datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S'), rSwap["result"]["tx_json"]["hash"], deltaE, "S"])
              except ValueError:
                VERBOSE('Error openning the history_registry file')
            else:
              VERBOSE("Cross-Payment transaction: " + rSwap["result"]["engine_result"])
              time.sleep(TimeOutSeq)
              if(('tx_json' in rSwap["result"]) and ('hash' in rSwap["result"]["tx_json"])):
                txhash = rSwap["result"]["tx_json"]["hash"]
                VERBOSE("Transaction Hash found: Now, verifying the Transaction status: " + txhash)
                respTxHash = asyncio.run(TxHash(txhash))
                rTxHash = json.loads(respTxHash)
                if(('status' in rTxHash) and (rTxHash["status"] == "success")):
                  if(('result' in rTxHash) and ('meta' in rTxHash["result"]) and ('TransactionResult' in rTxHash["result"]["meta"])):
                    if(rTxHash["result"]["meta"]["TransactionResult"] == "tesSUCCESS"):
                      etotal_inv01_ant =  etotal_inv01
                      etotal_inv02_ant =  etotal_inv02
                      VERBOSE("Cross-Payment transaction: " + rTxHash["result"]["meta"]["TransactionResult"])
                      VERBOSE("Energy Produced Registered in the Blockchain")
                      filejson = {'etotal_inv01_ant':etotal_inv01_ant, 'etotal_inv02_ant':etotal_inv02_ant}
                      try:
                        with open('lastenergy.json', 'w+', encoding='utf-8') as f:
                          json.dump(filejson, f, ensure_ascii=True, indent=4)
                      except ValueError:
                        VERBOSE('Error openning the file')
                      try:
                        with open('history_registry.json', 'a', encoding='utf-8') as csvf:
                          history_writer = csv.writer(csvf, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
                          #ts = time.time()
                          #history_writer.writerow([datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S'), txhash, deltaE])
                          history_writer.writerow([datetime.datetime.fromtimestamp(rTxHash["result"]["date"]+946684800).strftime('%Y-%m-%d %H:%M:%S'), txhash, deltaE, "Q"])
                      except ValueError:
                        VERBOSE('Error openning the history_registry file')
                    else:
                      VERBOSE("TxHash call - Cross-Payment transaction: " + rTxHash["result"]["meta"]["TransactionResult"])
                  else:
                    if('result' in rTxHash):
                      VERBOSE("TxHash call -  transaction Result: " + str(rTxHash["result"]))
                else:
                  if('status' in rTxHash):
                    VERBOSE("TxHash call - Status: " + str(rTxHash["status"]))
                  else:
                    VERBOSE("TxHash call - There is no Status field")
              else:
                VERBOSE("Transaction HASH not found")

    else:
      if('status' in rLLSeq):
        VERBOSE("LLSeq call - Status: " + str(rLLSeq["status"]))

  time.sleep(60)# execute the code at each 5 minutes
