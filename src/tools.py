from eth_account import Account

def to_address(priv_key):
    prefix = '' if priv_key.startswith('0x') else '0x'
    return Account.privateKeyToAccount(prefix + priv_key).address
