from web3 import Web3, HTTPProvider
from dotenv import load_dotenv
from tools import to_address
import solcx
import sys
import os

load_dotenv(verbose=True, override=True)

PRIVKEY        = os.getenv('PRIVKEY')
RPCURL         = os.getenv('RPCURL')
GASPRICE       = os.getenv('GASPRICE')
WALLETCONTRACT = os.getenv('WALLETCONTRACT').title()
SOLIDITY       = os.getenv('SOLIDITY')
OWNERS         = os.getenv('OWNERS').split()
THRESHOLD      = os.getenv('THRESHOLD')
VERIFY         = os.getenv('VERIFY')

solcx.install_solc(SOLIDITY)

def main():
    if len(sys.argv) == 2:
        filename = sys.argv[1]
        if os.path.exists(filename):
            intermediates = solcx.compile_files([filename]).get(filename+":"+WALLETCONTRACT)

            if intermediates is not None:
                abi = intermediates["abi"]
                code = intermediates["bin"]
                
                web3 = Web3(HTTPProvider(RPCURL)) # TODO: AC-002-04

                tx = web3.eth.contract(bytecode=code, abi=abi).constructor(OWNERS, THRESHOLD).buildTransaction({
                    'gasPrice': GASPRICE if GASPRICE is not None else web3.eth.gasPrice,
                    'nonce': web3.eth.getTransactionCount(to_address(PRIVKEY))
                })

                signed = web3.eth.account.signTransaction(tx, private_key=PRIVKEY)

                try:
                    tx_hash = web3.eth.sendRawTransaction(signed.rawTransaction)
                    txr = web3.eth.waitForTransactionReceipt(tx_hash)
                    print("Deployed at " + txr['contractAddress'])
                except Exception as ex:
                    if str(ex).find('Insufficient funds') != -1:
                        return None
                    else:
                        raise ex

                return

            problem = "There is no contract `" + WALLETCONTRACT + "` in " + filename
        else:
            problem = "There is no file: " + filename
    else:
        problem = "Contract is not provided"

    print('Nothing to deploy.')
    print(problem)

if __name__ == '__main__':
    main()