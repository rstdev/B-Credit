#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
created by antimoth at 2018-01-04
"""

import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "btc_cacheserver.settings")

import time
import sys
import json
import random

from amqpstorm import Connection
from django.db import connection
from django.db.utils import OperationalError
from web3.exceptions import BadFunctionCallOutput

import base
from btc_cacheserver import settings
from btc_cacheserver.defines import WriteChainMsgTypes, ContractNames, InterfaceMethods
from btc_cacheserver.util.procedure_logging import Procedure


w3 = base.create_web3_instance(10000)


class OutGasError(Exception):
    pass


def update_data(method, *args):
    procedure = Procedure("<%s>" % method)
    interface = base.get_contract_instance(settings.INTERFACE_ADDRESS, base.get_abi_path(ContractNames.INTERFACE))
    tx = base.transaction_exec_v2(interface, method, *args)
    procedure.info("UPDATE_DATA tx is: %s", tx.transactionHash)
    if tx.get("cumulativeGasUsed", 0) == settings.BLOCKCHAIN_CALL_GAS_LIMIT:
        raise OutGasError("gas out limit! transaction failed!")


def update_loan(data):
    update_data(InterfaceMethods.UPDATE_LOAN, 
        ContractNames.LOAN_CONTROLLER,
        w3.toBytes(hexstr=data["user_tag"]), 
        w3.toBytes(hexstr=data["loan_tag"]), 
        data["platform"].encode("utf-8"),
        data["credit"] or 0
    )


def update_expend(data):
    update_data(InterfaceMethods.UPDATE_EXPEND,
        ContractNames.LOAN_CONTROLLER,
        w3.toBytes(hexstr=data["user_tag"]), 
        w3.toBytes(hexstr=data["loan_tag"]), 
        w3.toBytes(hexstr=data["expend_tag"]), 
        data["order_number"][-32:].encode("utf-8"),
        data["bank_card"].encode("utf-8"),
        data["purpose"].encode("utf-8"),
        data.get("overdue_days",0),
        data["apply_amount"],
        data["receive_amount"],
        int(data["time_stamp"]),
        data["interest"]
    )


def update_installment(data):
    update_data(InterfaceMethods.UPDATE_INSTALLMENT,
        ContractNames.LOAN_CONTROLLER,
        w3.toBytes(hexstr=data["user_tag"]), 
        w3.toBytes(hexstr=data["loan_tag"]), 
        w3.toBytes(hexstr=data["expend_tag"]), 
        w3.toBytes(hexstr=data["installment_tag"]), 
        data["installment_number"],
        int(data["repay_time"]),
        data["repay_amount"]
    )


def update_repayment(data):
    update_data(InterfaceMethods.UPDATE_REPAYMENT,
        ContractNames.LOAN_CONTROLLER,
        w3.toBytes(hexstr=data["user_tag"]), 
        w3.toBytes(hexstr=data["loan_tag"]), 
        w3.toBytes(hexstr=data["expend_tag"]), 
        w3.toBytes(hexstr=data["repayment_tag"]), 
        data["installment_number"],
        data.get("overdue_days", 0),
        data["repay_type"],
        data["repay_amount"],
        int(data["repay_time"])
    )


def mock_loan(data):
    update_data(InterfaceMethods.UPDATE_LOAN, 
        ContractNames.LOAN_CONTROLLER,
        w3.toBytes(hexstr=data["user_tag"]), 
        w3.toBytes(hexstr=data["loan_tag"]), 
        "",
        0
    )


def mock_expend(data):
    update_data(InterfaceMethods.UPDATE_EXPEND,
        ContractNames.LOAN_CONTROLLER,
        w3.toBytes(hexstr=data["user_tag"]), 
        w3.toBytes(hexstr=data["loan_tag"]), 
        w3.toBytes(hexstr=data["expend_tag"]), 
        "",
        "",
        "",
        0,
        0,
        0,
        int(time.time()),
        0
    )

def on_message(message):
    """This function is called on message received.
    :param message:
    :return:
    """
    time.sleep(random.randint(1, 10))
    procedure = Procedure("<MSG-%s>" % sys.argv[1])
    msg_body = message.body

    _json = json.loads(msg_body)
    _msg_type = _json["type"]

    data = _json["data"]
    try:
        user_tag_str = data["user_tag"]
        procedure.start(" message(%s) for user(%s)", _msg_type, user_tag_str)

        #  sure to create the user contract and the loan store contract
        base.get_loan_store_address(ContractNames.LOAN_CONTROLLER, user_tag_str)

        if WriteChainMsgTypes.MSG_TYPE_USER == _msg_type:
            base.get_loan_store_address(ContractNames.LOAN_CONTROLLER, user_tag_str)

        elif WriteChainMsgTypes.MSG_TYPE_LOAN == _msg_type:
            update_loan(data)

        elif WriteChainMsgTypes.MSG_TYPE_EXPEND == _msg_type:
            update_expend(data)

        elif WriteChainMsgTypes.MSG_TYPE_INSTALLMENT == _msg_type:
            update_installment(data)

        elif WriteChainMsgTypes.MSG_TYPE_REPAYMENT == _msg_type:
            update_repayment(data)

        else:
            raise Exception("unknown messsage type!")

        procedure.info("ACK_MSG, message is %s", msg_body)
        message.ack()

    except OperationalError:
        procedure.exception("MSG_MYSQL_ERROR, REJECT_REQUEUE_MSG, message is %s", msg_body)
        connection.close()
        message.reject(requeue=True)

    except BadFunctionCallOutput:
        controller_address = base.get_controller_address(ContractNames.LOAN_CONTROLLER)
        base.create_loan_contract(user_tag_str, controller_address)
        message.reject(requeue=True)

    except OutGasError:
        try:
            if WriteChainMsgTypes.MSG_TYPE_EXPEND == _msg_type:
                mock_loan(data)

            elif WriteChainMsgTypes.MSG_TYPE_INSTALLMENT == _msg_type:
                mock_expend(data)

            elif WriteChainMsgTypes.MSG_TYPE_REPAYMENT == _msg_type:
                mock_expend(data)

            else:
                raise Exception("upexpected OutGasError!")

            procedure.info("REJECT_REQUEUE_MSG, message is %s", msg_body)
            message.reject(requeue=True)

        except OutGasError:
            if WriteChainMsgTypes.MSG_TYPE_INSTALLMENT == _msg_type or WriteChainMsgTypes.MSG_TYPE_REPAYMENT == _msg_type:
                mock_loan(data)
                mock_expend(data)
                procedure.info("REJECT_REQUEUE_MSG_MSG, message is %s", msg_body)
                message.reject(requeue=True)
            else:
                procedure.exception("MSG_WRITE_BLOCK_ERROR, REJECT_REDISTRIBUTE, message is %s", msg_body)
                message.reject(requeue=False)

        except Exception:
            procedure.exception("MSG_WRITE_BLOCK_ERROR, REJECT_REDISTRIBUTE, message is %s", msg_body)
            message.reject(requeue=False)

    except Exception:
        procedure.exception("MSG_WRITE_BLOCK_ERROR, REJECT_REDISTRIBUTE, message is %s", msg_body)
        message.reject(requeue=False)



def consumer(queue_name):
    with Connection(settings.MQ_HOST, settings.MQ_USER, settings.MQ_PASSWORD, port=settings.MQ_PORT) as connection:
        
        with connection.channel() as channel:
            
            # Declare the Queue
            channel.queue.declare(queue_name, durable=True, arguments={"x-dead-letter-exchange": settings.WRITE_BLOCKCHAIN_EXCHANGE, "x-dead-letter-routing-key": settings.WRITE_BLOCKCHAIN_QUEUE, })
            channel.exchange.declare(settings.WRITE_BLOCKCHAIN_EXCHANGE, exchange_type="topic", durable=True)
            channel.queue.bind(queue_name, settings.WRITE_BLOCKCHAIN_EXCHANGE, queue_name)

            # Set QoS to 1.
            # This will limit the consumer to only prefetch a 1 messages.
            # This is a recommended setting, as it prevents the
            # consumer from keeping all of the messages in a queue to itself.
            channel.basic.qos(1)

            # Start consuming the queue using the callback
            # 'on_message' and last require the message to be acknowledged.
            channel.basic.consume(on_message, queue_name, no_ack=False)

            try:
                # Start consuming messages.
                # to_tuple equal to False means that messages consumed
                # are returned as a Message object, rather than a tuple.
                channel.start_consuming(to_tuple=False)
            except KeyboardInterrupt:
                channel.close()

if __name__ == '__main__':
    queue_name = settings.WRITE_BLOCKCHAIN_QUEUE + "_" + sys.argv[1]
    consumer(queue_name)
