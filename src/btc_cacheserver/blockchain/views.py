from django.shortcuts import render

import json
import logging
import time
import pytz

from datetime import datetime, timedelta
from django.utils import timezone
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.db.models import Q
from web3 import Web3, RPCProvider

from btc_cacheserver import settings
from btc_cacheserver.blockchain.models import BlockNumberRecording
from btc_cacheserver.contract.models import LoanInfo, ExpendInfo, RepaymentInfo, ContractDeployInfo
from btc_cacheserver.util import common
from btc_cacheserver.defines import ContractNames
from btc_cacheserver.blockchain.decode_contract import decode_input, is_create_user_tx
from btc_cacheserver.blockchain.consumers import TYPE_SHOW_MAP, METHOD_TYPE_MAP
from btc_cacheserver.blockchain import decode_base
from btc_cacheserver.blockchain.consumers_v2 import contract_addresses_map_names
from btc_cacheserver.blockchain import defines

Log = logging.getLogger("scripts")
provider = RPCProvider(host=settings.BLOCKCHAIN_RPC_HOST, port=settings.BLOCKCHAIN_RPC_PORT)
w3 = Web3(provider)


@require_http_methods(['GET'])
@csrf_exempt
def get_block_detail_info_v2(request, number):
    if not str(number).isdigit():
        Log.warn("block number is error.")
        return JsonResponse({"msg": "block number is error.", "code": -1})

    try:
        block_info = w3.eth.getBlock(int(number))

        if not block_info:
            Log.warn("Block is not exist.")
            return JsonResponse({"msg": "Block is not exist.", "code": -1})
        transactions = block_info.transactions

        trans_info = []
        for tx_hash in transactions:
            tx_data = w3.eth.getTransaction(tx_hash)

            if tx_data.to is None:
                tx_type = defines.TransactionTypes.DEPLOY_TX

            elif tx_data["value"]:
                tx_type = defines.TransactionTypes.TRANSFER

            else:
                contract_name = contract_addresses_map_names.get(tx_data.to)
                if not contract_name:
                    record = ContractDeployInfo.objects.filter(address=tx_data.to)
                    if not record:
                        Log.warn("*!*!*unresolved contract address*!*!*")
                        continue
                    else:
                        contract_name = record[0].name

                tx_type, args = decode_base.decode_input(tx_data.input, contract_name)
            # print(contract_name, tx_type)

            tx_data = {
                "tx_hash": tx_data.hash,
                "type": defines.map_tx_types_to_show_names.get(tx_type, ""),
                "from": tx_data["from"],
                "to": tx_data.to,
                "value": tx_data.value
            }
            trans_info.append(tx_data)

        data = {"msg": "",
                "code": 0,
                "blockchain": {
                    "hash": block_info.hash,
                    "difficulty": block_info.difficulty,
                    "miner": block_info.miner,
                    "tx_count": len(block_info.transactions),
                    "gas_limit": block_info.gasLimit,
                    "gas_used": block_info.gasUsed,
                    "time": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(block_info.timestamp)),
                    "size": block_info.size,
                    "extra_data": block_info.extraData,
                    "transactions": trans_info
                    }
                }
        return JsonResponse(data)

    except Exception as err:
        Log.error(str(err), exc_info=True)
        return JsonResponse({
            'code': -1,
            'msg': str(err)
        })

@require_http_methods(['GET'])
@csrf_exempt
def get_block_detail_info(request, number):
    if not str(number).isdigit():
        Log.warn("block number is error.")
        return JsonResponse({"msg": "block number is error.", "code": -1})

    try:
        block_info = w3.eth.getBlock(int(number))

        if not block_info:
            Log.warn("Block is not exist.")
            return JsonResponse({"msg": "Block is not exist.", "code": -1})
        transactions = block_info.transactions

        trans_info = []
        for tx_hash in transactions:
            transaction = w3.eth.getTransaction(tx_hash)

            if transaction['to']:
                method_name, args = decode_input(transaction['input'])
                if method_name in METHOD_TYPE_MAP:
                    tx_type = METHOD_TYPE_MAP[method_name]
                elif transaction['input'] == '0x':
                    tx_type = 0
                else:
                    # Log.warn("tx has to and input is not empty.tx_hash:{}".format(th))
                    continue
            else:
                if is_create_user_tx(transaction['input']):
                    tx_type = -1
                else:
                    # Log.warn("tx has no to and not create_user_tx.tx_hash:{}".format(th))
                    continue

            tx_data = {
                "tx_hash": transaction.hash,
                "type": TYPE_SHOW_MAP[tx_type],
                "from": transaction["from"],
                "to": transaction.to,
                "value": transaction.value
            }
            trans_info.append(tx_data)

        data = {"msg": "",
                "code": 0,
                "blockchain": {
                    "hash": block_info.hash,
                    "difficulty": block_info.difficulty,
                    "miner": block_info.miner,
                    "tx_count": len(block_info.transactions),
                    "gas_limit": block_info.gasLimit,
                    "gas_used": block_info.gasUsed,
                    "time": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(block_info.timestamp)),
                    "size": block_info.size,
                    "extra_data": block_info.extraData,
                    "transactions": trans_info
                    }
                }
        return JsonResponse(data)

    except Exception as err:
        Log.error(str(err), exc_info=True)
        return JsonResponse({
            'code': -1,
            'msg': str(err)
        })


@require_http_methods(['GET'])
@csrf_exempt
def get_transaction_detail_info(request, txhash):
    if not txhash:
        Log.warn("Transaction hash is error.")
        return JsonResponse({"msg": "Transaction hash is error.", "code": -1})

    try:
        _txhash = "0x" + txhash
        transaction_info = w3.eth.getTransaction(_txhash)
        if not transaction_info:
            Log.warn("Transaction is not exist.")
            return JsonResponse(
                {"msg": "Transaction is not exist.", "code": -1})

        transaction_receipt = w3.eth.getTransactionReceipt(_txhash)
        block_info = w3.eth.getBlock(transaction_info.blockNumber)

        data = {"msg": "",
                "code": 0,
                "transactions": {
                    "hash": transaction_info.hash,
                    "block_number": transaction_info.blockNumber,
                    "time": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(block_info.timestamp)),
                    "from": transaction_info["from"],
                    "to": transaction_info.to,
                    "value": transaction_info.value,
                    "gas_limit": block_info.gasLimit,
                    "gas_used": transaction_receipt.gasUsed
                    }
                }

        return JsonResponse(data)

    except Exception as err:
        Log.error(str(err), exc_info=True)
        return JsonResponse({
            'code': -1,
            'msg': str(err)
        })


@require_http_methods(['GET'])
@csrf_exempt
def get_blocknumber_recording(request):
    t_start = request.GET.get('start_time', '')
    t_end = request.GET.get('end_time', '')

    try:
        if t_start and t_end:
            datetime_query = Q(time__range=(t_start, t_end))
            block_recording = BlockNumberRecording.objects.filter(datetime_query)
        else:
            utc_tz = pytz.timezone("UTC")
            block_recording = BlockNumberRecording.objects.filter(time__gte=utc_tz.localize(datetime.utcnow() - timedelta(days=2)))

        number_list = [block.blocknumber for block in block_recording]
        time_list = [timezone.localtime(block.time).strftime("%Y-%m-%d %H:%M:%S") for block in block_recording]

        data = {
            "msg": "",
            "code": 0,
            "blockchain": {
                "blocknumber": number_list,
                "time": time_list
            }
        }

        return JsonResponse(data)
    except Exception as err:
        Log.error(str(err), exc_info=True)
        return JsonResponse({
            'code': -1,
            'msg': str(err)
        })


@require_http_methods(['GET'])
@csrf_exempt
def get_total_number(request):
    try:
        total_platform = LoanInfo.objects.count()
        total_loan = ExpendInfo.objects.count()
        total_repay = RepaymentInfo.objects.count()

        data = {
            "msg": "",
            "code": 0,
            "blockchain": {
                "total_platform": total_platform,
                "total_loan": total_loan,
                "total_repay": total_repay
            }
        }

        return JsonResponse(data)
    except Exception as err:
        Log.error(str(err), exc_info=True)
        return JsonResponse({
            'code': -1,
            'msg': str(err)
        })


@require_http_methods(['GET'])
@csrf_exempt
def get_account_info(request, address):
    if not address:
        Log.warn("User address is error.")
        return JsonResponse({"msg": "User address is error.", "code": -1})

    try:
        _address = "0x" + address
        accounts = w3.eth.accounts

        if not (_address in accounts):
            nouser_msg = "Cannot find user,address is {}.".format(_address)
            Log.warn(nouser_msg)
            return JsonResponse({"msg": nouser_msg, "code": -1})

        tx_count = w3.eth.getTransactionCount(_address)
        contract = common.get_contract_instance(settings.TOKEN_ADDRESS,
                                                common.get_abi_path(ContractNames.TOKEN))

        balanceof = common.transaction_exec_local_result(contract, "balanceOf", _address)

        data = {
            "msg": "",
            "code": 0,
            "account": {
                "address": _address,
                "tx_count": tx_count,
                "balance": balanceof
            }
        }
        return JsonResponse(data)

    except Exception as err:
        Log.error(str(err), exc_info=True)
        return JsonResponse({
            'code': -1,
            'msg': str(err)
        })
