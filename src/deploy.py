from web3 import Web3, HTTPProvider
import dotenv
from tools import to_address, get_content_from_file
import solcx
import sys
import os
import requests

dotenv.load_dotenv(verbose=True, override=True)

VERIFY = os.getenv('VERIFY', "False").title() == "True"

# must be defined and be correct, what to do in otherwise conditiona wasn't described
PRIVKEY = os.getenv('PRIVKEY')
RPCURL = os.getenv('RPCURL')
GASPRICE = int(os.getenv('GASPRICE'))
WALLETCONTRACT = os.getenv('WALLETCONTRACT')
SOLIDITY = os.getenv('SOLIDITY')
OWNERS = os.getenv('OWNERS').split()
THRESHOLD = int(os.getenv('THRESHOLD'))


def main():
    if len(sys.argv) == 2:
        filename = sys.argv[1]

        if os.path.exists(filename):
            solcx.install_solc(SOLIDITY)
            solcx.set_solc_version(SOLIDITY)
            intermediates = solcx.compile_files([filename], optimize=True, optimize_runs=200).get(
                filename + ":" + WALLETCONTRACT)

            if intermediates is not None:
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
                    contract_addr = txr['contractAddress']

                    if VERIFY:
                        json = {
                            "addressHash": contract_addr,
                            "compilerVersion": 'v' + str(solcx.get_solc_version(True)),
                            "contractSourceCode": get_content_from_file(filename),
                            "optimization": True,
                            "name": WALLETCONTRACT,
                            "constructorArguments": '000000000000000000000000000000000000000000000000000000000000004000'
                                                    '000000000000000000000000000000000000000000000000000000000000020000'
                                                    '000000000000000000000000000000000000000000000000000000000003000000'
                                                    '00000000000000000033e0e07ca86c869ade3fc9de9126f6c73dad105e00000000'
                                                    '000000000000000079dd14623c4d33413c0c28fdabc2285fdb1e572e0000000000'
                                                    '00000000000000130930e3e3d30bf8f975a729e948cdcc212ecfbb',
                            "evmVersion": "default",
                            "optimizationRuns": 200
                        }
                        response = requests.post('https://blockscout.com/poa/sokol/api?module=contract&action=verify',
                                                 json=json)
                        if response.status_code == 200:
                            print('Verification message:', response.json()['message'])
                        else:
                            print('Error:', response.status_code, response.reason)

                    if os.getenv('DEV'):
                        dotenv.set_key(dotenv.find_dotenv(), "WALLETCONTRACTADDRESS", contract_addr)

                    print("Deployed at " + contract_addr)
                    return

                except Exception as ex:
                    if str(ex).find('Insufficient funds') != -1:
                        problem = "The balance of the account " + to_address(PRIVKEY) + " is not enough to deploy."
                    else:
                        raise ex
                        # problem = "The JSON RPC URL " + RPCURL + " is not accessible"
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
