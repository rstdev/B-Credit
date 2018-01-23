import sys
import json
from web3 import Web3, RPCProvider
from channels import Group
from btc_cacheserver import settings
from btc_cacheserver.blockchain.decode_contract import decode_input

METHOD_TYPE_MAP = {"getLoanByIndex":1, "updateLoan":2,
                   "getExpendByIndex":1, "updateExpenditure":2,
                   "getInstallmentByIndex":1, "updateInstallment":2,
                   "getRepaymentByIndex":1, "updateRepayment":2 }

provider = RPCProvider(host=settings.BLOCKCHAIN_RPC_HOST, port=settings.BLOCKCHAIN_RPC_PORT)
w3 = Web3(provider)
new_block_filter = w3.eth.filter('latest')
new_transaction_filter = w3.eth.filter('pending')

def ws_connect(message):
    message.reply_channel.send({"accept": True})
    Group("chain").add(message.reply_channel)
    def new_block_callback(block_hash):
        block_info = w3.eth.getBlock(block_hash)
        data = {"blockchain": {
                    "blocknumber": block_info['number'],
                    "miner": block_info['miner'],
                    "time": block_info['timestamp'],
                    "tx_count": len(block_info['transactions'])
                    }
               }
        json_data = json.dumps(data)
        sys.stdout.write("New Block: {0}\r\n".format(json_data))
        sys.stdout.flush()
        Group("chain").send({"text": json_data})

    def new_transaction_callback(tx_hash):
        tx_info = w3.eth.getTransaction(tx_hash)
        if tx_info['input']=="0x":
            tx_type = 0
        else:
            method_name, args = decode_input(tx_info['input'])
            tx_type = METHOD_TYPE_MAP[method_name]
        data = {"transactions": {
                    "tx_hash": tx_hash,
                    "from": tx_info['from'],
                    "to": tx_info['to'],
                    "type": tx_type,
                    "fee": tx_info['gas']*tx_info['gasPrice'],
                    }
               }
        json_data = json.dumps(data)
        sys.stdout.write("New TX: {0}".format(json_data))
        sys.stdout.flush()
        Group("chain").send({"text": json_data})

    if not new_block_filter.running:
        new_block_filter.watch(new_block_callback)
    if not new_transaction_filter.running:
        new_transaction_filter.watch(new_transaction_callback)

def ws_disconnect(message):
    Group("chain").discard(message.reply_channel)
