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

METHOD_SHOW_MAP = {"none":u"", "getLoanByIndex":u"借款", "updateLoan":u"借款",
                   "getExpendByIndex":u"支用", "updateExpenditure":u"支用",
                   "getInstallmentByIndex":u"分期", "updateInstallment":u"分期",
                   "getRepaymentByIndex":u"还款", "updateRepayment":u"还款" }

TYPE_SHOW_MAP = {-1:u"部署合约", 0:u"转账", 1:u"查询", 2:u"写入"}

provider = RPCProvider(host=settings.BLOCKCHAIN_RPC_HOST, port=settings.BLOCKCHAIN_RPC_PORT)
w3 = Web3(provider)
new_block_filter = w3.eth.filter('latest')
new_transaction_filter = w3.eth.filter('latest')

def ws_connect(message):
    message.reply_channel.send({"accept": True})
    Group("chain").add(message.reply_channel)
    def new_block_callback(block_hash):
        data_list = []
        block_num = w3.eth.getBlock(block_hash).number
        for i in range(10):
            block_info = w3.eth.getBlock(block_num - i)
            data = {
                    "blocknumber": block_info['number'],
                    "miner": block_info['miner'],
                    "time": block_info['timestamp'],
                    "tx_count": len(block_info['transactions'])
            }
            data_list.append(data)
        datas = {"blockchain":data_list}
        json_data = json.dumps(datas)
        #sys.stdout.write("New Block: {0}\r\n".format(json_data))
        #sys.stdout.flush()
        Group("chain").send({"text": json_data})

    def new_transaction_callback(block_hash):
        data_list = []
        #block_num = w3.eth.getTransaction(tx_hash).blockNumber
        block_num = w3.eth.getBlock(block_hash).number
        #block_num = w3.eth.blockNumber
        for i in range(100):
            block = w3.eth.getBlock(block_num - i)
            bt_list = block.transactions
            bt_list.reverse()
            for th in bt_list:
                tx_info = w3.eth.getTransaction(th)
                if tx_info['input']=="0x":
                    tx_type = 0
                    method_name = 'none'
                elif not tx_info['to']:
                    tx_type = -1
                    method_name = 'none'
                else:
                    method_name, args = decode_input(tx_info['input'])
                    tx_type = METHOD_TYPE_MAP[method_name]
                data = {
                        "tx_hash": th,
                        "from": tx_info['from'],
                        "to": tx_info['to'],
                        "type": TYPE_SHOW_MAP[tx_type],
                        "fee": tx_info['gas']*tx_info['gasPrice'],
                        "info": METHOD_SHOW_MAP[method_name],
                        "time": block.timestamp
                }
                data_list.append(data)
                if len(data_list) > 9:
                    break
            else:
                continue
            break
        datas = {"transactions":data_list}
        json_data = json.dumps(datas)
        #sys.stdout.write("New TX: {0}".format(json_data))
        #sys.stdout.flush()
        Group("chain").send({"text": json_data})

    if not new_block_filter.running:
        new_block_filter.watch(new_block_callback)
    if not new_transaction_filter.running:
        new_transaction_filter.watch(new_transaction_callback)

def ws_disconnect(message):
    Group("chain").discard(message.reply_channel)

