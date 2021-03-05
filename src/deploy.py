import solcx
import sys
import os
from dotenv import load_dotenv
from pprint import pprint

load_dotenv(verbose=True, override=True)

RPCURL         = os.getenv('RPCURL')
GASPRICE       = os.getenv('GASPRICE')
WALLETCONTRACT = os.getenv('WALLETCONTRACT')
SOLIDITY       = os.getenv('SOLIDITY')
OWNERS         = os.getenv('OWNERS').split()
THRESHOLD      = os.getenv('THRESHOLD')
VERIFY         = os.getenv('VERIFY')

solcx.install_solc(SOLIDITY)

def main():
    if len(sys.argv) == 2:
        if os.path.exists(sys.argv[1]):
            solcx.compile_files([sys.argv[1]])
            return
        else:
            problem = "There is no file: " + sys.argv[1]
    else:
        problem = "Contract is not provided"

    print('Nothing to deploy.')
    print(problem)

if __name__ == '__main__':
    main()