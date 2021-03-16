from tools import to_address
from web3.exceptions import SolidityError, ContractLogicError


class ContractWrapper:
    gas_price = None
    user_priv_key = None
    user_acc = None

    def __init__(self, w3, gas, user_pk, **kwargs):
        """
        Методы автоматически определяются как call или buildTransaction
        > методы определенные как call возвращают результат функции
        > методы определенные как bT возвращают рецепт отправленной транзакции

        Args:
            w3 (Web3): экземпляр web3 для общения с блокчеином.
            **kwargs (type): парамтры как для eth.contract().
        """

        gas_price = gas
        user_priv_key = user_pk
        user_acc = to_address(user_pk)

        contract = w3.eth.contract(**kwargs)

        # setup events
        self.events = contract.events

        # setup constructor
        def construct(*args, **kwargs):
            tx = contract.constructor(*args, **kwargs).buildTransaction({
                'gasPrice': gas_price,
                'nonce': w3.eth.getTransactionCount(user_acc)
            })

            signed = w3.eth.account.signTransaction(tx, private_key=user_priv_key)
            tx_hash = w3.eth.sendRawTransaction(signed.rawTransaction)

            tx_receipt = w3.eth.waitForTransactionReceipt(tx_hash)
            return tx_receipt

        setattr(self, 'constructor', construct)

        # setup contract methods
        for elem in kwargs['abi']:
            if 'name' in elem:
                try:
                    # choose call or buildTransaction
                    if elem['stateMutability'] == 'view':
                        def funct(name):
                            def func(*args, **kwargs):
                                return getattr(contract.functions, name)(*args, **kwargs).call()

                            return func
                    elif elem['stateMutability'] == 'nonpayable' or \
                            elem['stateMutability'] == 'pure' or \
                            elem['stateMutability'] == 'payable':
                        def funct(name):
                            def func(*args, **kwargs):
                                value = 0 if 'value' not in kwargs.keys() else kwargs.pop('value')

                                tx = {
                                    'to': contract.address,
                                    'value': value,
                                    'gas': 1000000,
                                    'gasPrice': gas_price,
                                    'nonce': w3.eth.getTransactionCount(user_acc),
                                    'data': contract.encodeABI(fn_name=name, args=args, kwargs=kwargs)
                                }

                                try:
                                    signed = w3.eth.account.signTransaction(tx, private_key=user_priv_key)
                                    tx_hash = w3.eth.sendRawTransaction(signed.rawTransaction)
                                    tx_receipt = w3.eth.waitForTransactionReceipt(tx_hash)
                                    return tx_receipt
                                except Exception as q:
                                    print(q)
                            return func
                    setattr(self, elem['name'], funct(elem['name']))
                except KeyError:
                    pass
                except ContractLogicError as ex:
                    print(ex)
                    pass
