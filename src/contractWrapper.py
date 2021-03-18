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

        self.gas_price = gas
        self.user_priv_key = user_pk
        self.user_acc = to_address(user_pk)

        contract = w3.eth.contract(**kwargs)

        # setup events
        self.events = contract.events

        # setup constructor
        def construct(*args, **kwargs):
            tx = contract.constructor(*args, **kwargs).buildTransaction({
                'gasPrice': self.gas_price,
                'nonce': w3.eth.getTransactionCount(self.user_acc)
            })

            signed = w3.eth.account.signTransaction(tx, private_key=self.user_priv_key)
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
                    else:
                        def funct(name):
                            def func(*args, **kwargs):
                                value = 0 if 'value' not in kwargs.keys() else kwargs.pop('value')

                                # this line will throw detailed exception with revert reason in case of fault (an instance of ContractLogicError)
                                getattr(contract.functions, name)(*args, **kwargs).call()

                                tx = {
                                    'to': contract.address,
                                    'value': value,
                                    'gas': 1000000,
                                    'gasPrice': self.gas_price,
                                    'nonce': w3.eth.getTransactionCount(self.user_acc),
                                    'data': contract.encodeABI(fn_name=name, args=args, kwargs=kwargs)
                                }

                                signed = w3.eth.account.signTransaction(tx, private_key=self.user_priv_key)
                                tx_hash = w3.eth.sendRawTransaction(signed.rawTransaction)
                                tx_receipt = w3.eth.waitForTransactionReceipt(tx_hash)
                                return tx_receipt

                            return func
                    setattr(self, elem['name'], funct(elem['name']))
                except KeyError:
                    pass
