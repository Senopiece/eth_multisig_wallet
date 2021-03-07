import os

import requests
import solcx
from eth_account import Account

BS_BASE = "https://blockscout.com/poa/sokol/api"
SOLIDITY = os.getenv('SOLIDITY', "v0.7.6")


def to_address(priv_key):
    prefix = '' if priv_key.startswith('0x') else '0x'
    return Account.privateKeyToAccount(prefix + priv_key).address


def get_ABI(addr, default_local_path="contracts/test.sol"):
    resp = requests.get(BS_BASE + f"?module=contract&action=getabi&address={addr}")
    data = resp.json()
    abi = data["result"]
    if resp.status_code != 200 or data["message"] != "OK":
        solcx.install_solc(SOLIDITY)
        intermediates = solcx.compile_files([default_local_path])
        abi = intermediates[next(filter(lambda x: 'ERC20' not in x, intermediates.keys()))]["abi"]
    return abi
