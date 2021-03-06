import os
import sys

from dotenv import load_dotenv
from web3 import Web3, HTTPProvider

from contractWrapper import ContractWrapper
from tools import get_ABI, to_address, keccak_shifted

from web3.exceptions import ContractLogicError

load_dotenv(verbose=True, override=True)

PRIVKEY = os.getenv('PRIVKEY')
RPCURL = os.getenv('RPCURL')
GASPRICE = int(os.getenv('GASPRICE'))
WALLETCONTRACTADDRESS = os.getenv('WALLETCONTRACTADDRESS')

web3 = Web3(HTTPProvider(RPCURL))
web3.eth.handleRevert = True

abi = get_ABI(WALLETCONTRACTADDRESS)

contract = ContractWrapper(w3=web3, gas=GASPRICE, user_pk=PRIVKEY, abi=abi, address=WALLETCONTRACTADDRESS)


# def add(addr):
#     tx = contract.addOwner(addr)
#
#     e_ok = contract.events.ActionConfirmed().processReceipt(tx)
#
#     if not e_ok:
#         print("It is not the wallet owner. Nothing to do.")
#         return
#     owner_id = e_ok[0].args.id
#
#     e_req = contract.events.RequestToAddOwner().processReceipt(tx)
#
#     if len(e_req) > 0 and (tx.transactionHash != e_req[0].transactionHash):
#         print(f"Confirmation 0x{owner_id.hex()} was already sent. Nothing to do.")
#         return
#     print("Confirmation 0x" + owner_id.hex())
#
#     print(f"Sent at 0x{tx.transactionHash.hex()}")
#
#     confirms = len(contract.events.ActionConfirmed.createFilter(fromBlock="0x0",
#                                                                 argument_filters={"id": owner_id}).get_all_entries())
#
#     th = contract.getThreshold()
#     print(f"It is {confirms} of {th} confirmations", end='')
#
#     is_exists = len(contract.events.OwnerExists().processReceipt(tx))
#     is_added = len(contract.events.OwnerAdded().processReceipt(tx))
#     if is_exists:
#         print(" -- but cannot be executed.\nOwner exists.")
#     if is_added:
#         print(" -- executed.")


def add(addr):
    def post(tx, is_finished_ok):
        if tx.status:
            pass
        if not is_finished_ok and (add in contract.getOwners()):  # TODO
            print(" -- but cannot be executed.\nOwner exists.")

    tx = execute(lambda: contract.addOwner(addr),
                 contract.events.RequestToAddOwner(),
                 contract.events.OwnerAdded(),
                 post,
                 keccak_shifted(addr))


def remove(addr):
    def post(tx, is_end):
        pass

    tx = execute(lambda: contract.removeOwner(addr),
                 contract.events.RequestToRemoveOwner(),
                 contract.events.OwnerRemoved(),
                 post,
                 keccak_shifted(addr))


def execute(tx_cmd, req_evt, end_evt, post_check, fallback_id):
    tx = tx_cmd()

    if not contract.isOwner(contract.user_acc):
        print("It is not the wallet owner. Nothing to do.")
        return tx

    e_ok = contract.events.ActionConfirmed().processReceipt(tx)

    owner_id = e_ok[0].args.id if e_ok else fallback_id
    e_req = req_evt.processReceipt(tx)

    if len(e_req) > 0 and (tx.transactionHash != e_req[0].transactionHash):
        print(f"Confirmation 0x{owner_id.hex()} was already sent. Nothing to do.")
        return tx
    print("Confirmation 0x" + owner_id.hex())

    print(f"Sent at 0x{tx.transactionHash.hex()}")

    confirms = len(contract.events.ActionConfirmed.createFilter(fromBlock="0x0",
                                                                argument_filters={"id": owner_id}).get_all_entries())

    print(f"It is {min(1, confirms)} of {contract.getThreshold()} confirmations", end='')

    is_added = len(end_evt.processReceipt(tx))
    if is_added:
        print(" -- executed.")

    post_check(tx, is_added)
    return tx


def get(mode):
    if mode == 'owners':
        print("The current owners list:")

        owners = set()
        add_filter = contract.events.OwnerAdded.createFilter(fromBlock='earliest', toBlock='latest')
        rmv_filter = contract.events.OwnerRemoved.createFilter(fromBlock='earliest', toBlock='latest')

        for event in add_filter.get_all_entries():
            owners.add(event['args']['newowner'])

        for event in rmv_filter.get_all_entries():
            owners.remove(event['args']['owner'])

        print(*owners, sep='\n')
    
    elif mode == 'thresh':
        print(f"Required number of confirmations: {contract.getThreshold()}")
    elif mode == '':
        pass
    elif mode == '':
        pass


def transfer(to, value):
    try:
        print(contract.isOwner(contract.user_acc))
        txr, _ = contract.transfer(to, int(value))
    except ContractLogicError as e:
        e = str(e)
        if e == "execution reverted: this method is only for owners, you are not an owner":
            print("It is not the wallet owner. Nothing to do.")
    else:
        aid = contract.events.ActionConfirmed().processReceipt(txr)[0]['id']
        cc = contract.confirmationsCount(aid)
        thr = contract.getThreshold()

        if cc == 1:
            print("Confirmation " + aid)
        
        print("Sent at " + txr['transactionHash'])
        print(f"It is {cc} of {thr} confirmations" + (" -- executed." if cc >= thr else ""))

def main():
    if len(sys.argv) > 2:
        cmd = sys.argv[1]
        cmds = {
            "add": add,
            "remove": remove,
            "get": get,
            "transfer": transfer
        }
        cmds[cmd](*sys.argv[2:])


if __name__ == '__main__':
    # a = web3.eth.account.create()
    # print(a.address, a.privateKey.hex())
    # add(a.address)
    # get("owners")
    # add("0x130930e3E3D30bF8F975a729e948CdCc212ECFBB")#a.address)
    # get("thresh")
    main()
