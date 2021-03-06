import os
import sys

from dotenv import load_dotenv
from web3 import Web3, HTTPProvider

from contractWrapper import ContractWrapper
from tools import get_ABI, to_address

load_dotenv(verbose=True, override=True)

PRIVKEY = os.getenv('PRIVKEY')
RPCURL = os.getenv('RPCURL')
GASPRICE = int(os.getenv('GASPRICE'))
WALLETCONTRACTADDRESS = os.getenv('WALLETCONTRACTADDRESS')

# VERIFY = os.getenv('VERIFY')
# WALLETCONTRACT = os.getenv('WALLETCONTRACT').title()
# SOLIDITY = os.getenv('SOLIDITY')
# OWNERS = os.getenv('OWNERS').split()
# THRESHOLD = int(os.getenv('THRESHOLD'))


web3 = Web3(HTTPProvider(RPCURL))
web3.eth.defaultAccount = to_address(PRIVKEY)

abi = get_ABI(WALLETCONTRACTADDRESS)
contract = ContractWrapper(w3=web3, gas=GASPRICE, user_pk=PRIVKEY, abi=abi, address=WALLETCONTRACTADDRESS)


def add(addr):
    print(addr)
    tx = contract.addOwner(addr)

    e_ok = contract.events.ActionConfirmed().processReceipt(tx)

    if not e_ok:
        print("It is not the wallet owner. Nothing to do.")
        return
    owner_id = e_ok[0].args.id

    e_req = contract.events.RequestToAddOwner().processReceipt(tx)

    if len(e_req) > 0 and (tx.transactionHash != e_req[0].transactionHash):
        print(f"Confirmation 0x{owner_id.hex()} was already sent. Nothing to do.")
        return
    print("Confirmation 0x" + owner_id.hex())

    print(f"Sent at 0x{tx.transactionHash.hex()}")

    confirms = len(contract.events.ActionConfirmed.createFilter(fromBlock="0x0",
                                                                argument_filters={"id": owner_id}).get_all_entries())

    th = contract.getThreshold()
    print(f"It is {confirms} of {th} confirmations", end='')

    is_exists = len(contract.events.OwnerExists().processReceipt(tx))
    is_added = len(contract.events.OwnerAdded().processReceipt(tx))
    if is_exists:
        print(" -- but cannot be executed.\nOwner exists.")
    if is_added:
        print(" -- executed.")


def main():
    if len(sys.argv) > 2:
        cmd = sys.argv[1]
        cmds = {
            "add": add
        }
        cmds[cmd](*sys.argv[2:])


if __name__ == '__main__':
    # a = web3.eth.account.create()
    # print(a.address, a.privateKey.hex())
    # add(a.address)
    main()
