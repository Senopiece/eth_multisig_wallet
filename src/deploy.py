from web3 import Web3, HTTPProvider
from dotenv import load_dotenv
from tools import to_address
import solcx
import sys
import os

import itertools # TODO: remove

load_dotenv(verbose=True, override=True)

# may be None
VERIFY = os.getenv('VERIFY') # TODO

# must be defined, what to do in otherwise conditiona wasn't described
PRIVKEY        = os.getenv('PRIVKEY')
RPCURL         = os.getenv('RPCURL')
GASPRICE       = int(os.getenv('GASPRICE'))
WALLETCONTRACT = os.getenv('WALLETCONTRACT').title()
SOLIDITY       = os.getenv('SOLIDITY')
OWNERS         = os.getenv('OWNERS').split()
THRESHOLD      = int(os.getenv('THRESHOLD'))

def main():
    if len(sys.argv) == 2:
        filename = sys.argv[1]

        if os.path.exists(filename):
            solcx.install_solc(SOLIDITY)
            intermediates = solcx.compile_files([filename]).get(filename+":"+WALLETCONTRACT)

            if intermediates is not None:
                try:
                    web3 = Web3(HTTPProvider(RPCURL))

                    abi = intermediates["abi"]
                    code = intermediates["bin"]

                    tx = web3.eth.contract(bytecode=code, abi=abi).constructor(OWNERS, THRESHOLD).buildTransaction({
                        'gasPrice': GASPRICE if GASPRICE is not None else web3.eth.gasPrice,
                        'nonce': web3.eth.getTransactionCount(to_address(PRIVKEY))
                    })

                    signed = web3.eth.account.signTransaction(tx, private_key=PRIVKEY)

                    try:
                        tx_hash = web3.eth.sendRawTransaction(signed.rawTransaction)
                        txr = web3.eth.waitForTransactionReceipt(tx_hash)
                        print("Deployed at " + txr['contractAddress'])
                        return
                    except Exception as ex:
                        if str(ex).find('Insufficient funds') != -1:
                            problem = "The balance of the account " + to_address(PRIVKEY) + " is not enough to deploy."
                        else:
                            raise ex # Such conditions wasn't described
                except:
                    problem = "The JSON RPC URL " + RPCURL + " is not accessible"
            else:
                problem = "There is no contract `" + WALLETCONTRACT + "` in " + filename
        else:
            problem = "There is no file: " + filename
    else:
        problem = "Contract is not provided"

    print('Nothing to deploy.')
    print(problem)

if __name__ == '__main__':
    main()