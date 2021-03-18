import os
import json
import requests
import solcx
from eth_account import Account
from web3 import Web3

BS_BASE = "https://blockscout.com/poa/sokol/api"
SOLIDITY = os.getenv('SOLIDITY', "v0.7.6")


def to_address(priv_key):
    prefix = '' if priv_key.startswith('0x') else '0x'
    return Account.privateKeyToAccount(prefix + priv_key).address


def get_ABI(addr, local_path=None):
    resp = requests.get(BS_BASE + f"?module=contract&action=getabi&address={addr}")
    data = resp.json()
    if resp.status_code != 200 or data["message"] != "OK":
        local_path = "contracts/multisig.sol" if 'src' in os.getcwd() else "src/contracts/test.sol"
        solcx.install_solc(SOLIDITY)
        solcx.set_solc_version(SOLIDITY)
        intermediates = solcx.compile_files([local_path])
        return intermediates[next(filter(lambda x: 'ERC20' not in x, intermediates.keys()))]["abi"]
    else:
        return json.loads(data["result"])


def keccak_shifted(txt):
    return (int.from_bytes(Web3.keccak(hexstr=txt), 'big') >> 1).to_bytes(32, 'big')


def get_content_from_file(filename):
    with open(filename) as f:
        return f.read()
