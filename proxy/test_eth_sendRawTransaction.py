import unittest
import os
from web3 import Web3
from solcx import install_solc

# install_solc(version='latest')
install_solc(version='0.7.0')
from solcx import compile_source

EXTRA_GAS = int(os.environ.get("EXTRA_GAS", "0"))
proxy_url = os.environ.get('PROXY_URL', 'http://localhost:9090/solana')
proxy = Web3(Web3.HTTPProvider(proxy_url))
eth_account = proxy.eth.account.create('https://github.com/neonlabsorg/proxy-model.py/issues/147')
proxy.eth.default_account = eth_account.address

SUBSTRING_LOG_ERR_147 = 'Invalid Ethereum transaction nonce:'

STORAGE_SOLIDITY_SOURCE_147 = '''
pragma solidity >=0.7.0 <0.9.0;
/**
 * @title Storage
 * @dev Store & retrieve value in a variable
 */
contract Storage {
    uint256 number;
    /**
     * @dev Store value in variable
     * @param num value to store
     */
    function store(uint256 num) public {
        number = num;
    }
    /**
     * @dev Return value
     * @return value of 'number'
     */
    function retrieve() public view returns (uint256){
        return number;
    }
}
'''


class Test_eth_sendRawTransaction(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        print("\n\nhttps://github.com/neonlabsorg/proxy-model.py/issues/147")
        print('eth_account.address:', eth_account.address)
        print('eth_account.key:', eth_account.key.hex())
        compiled_sol = compile_source(STORAGE_SOLIDITY_SOURCE_147)
        contract_id, contract_interface = compiled_sol.popitem()
        storage = proxy.eth.contract(abi=contract_interface['abi'], bytecode=contract_interface['bin'])
        trx_deploy = proxy.eth.account.sign_transaction(dict(
            nonce=proxy.eth.get_transaction_count(proxy.eth.default_account),
            chainId=proxy.eth.chain_id,
            gas=987654321,
            gasPrice=0,
            to='',
            value=0,
            data=storage.bytecode),
            eth_account.key
        )
        print('trx_deploy:', trx_deploy)
        trx_deploy_hash = proxy.eth.send_raw_transaction(trx_deploy.rawTransaction)
        print('trx_deploy_hash:', trx_deploy_hash.hex())
        trx_deploy_receipt = proxy.eth.wait_for_transaction_receipt(trx_deploy_hash)
        print('trx_deploy_receipt:', trx_deploy_receipt)

        cls.storage_contract = proxy.eth.contract(
            address=trx_deploy_receipt.contractAddress,
            abi=storage.abi
        )

    @unittest.skip("a.i.")
    def test_01_call_retrieve_right_after_deploy(self):
        print("\ntest_01_call_retrieve_right_after_deploy")
        number = self.storage_contract.functions.retrieve().call()
        print('number:', number)
        self.assertEqual(number, 0)

    @unittest.skip("a.i.")
    def test_02_execute_with_right_nonce(self):
        print("\ntest_02_execute_with_right_nonce")
        right_nonce = proxy.eth.get_transaction_count(proxy.eth.default_account)
        trx_store = self.storage_contract.functions.store(147).buildTransaction({'nonce': right_nonce})
        print('trx_store:', trx_store)
        trx_store_signed = proxy.eth.account.sign_transaction(trx_store, eth_account.key)
        print('trx_store_signed:', trx_store_signed)
        trx_store_hash = proxy.eth.send_raw_transaction(trx_store_signed.rawTransaction)
        print('trx_store_hash:', trx_store_hash.hex())
        trx_store_receipt = proxy.eth.wait_for_transaction_receipt(trx_store_hash)
        print('trx_store_receipt:', trx_store_receipt)
        number = self.storage_contract.functions.retrieve().call()
        print('number:', number)
        self.assertEqual(number, 147)

    @unittest.skip("a.i.")
    def test_03_execute_with_low_gas(self):
        print("\ntest_03_execute_with_low_gas")
        right_nonce = proxy.eth.get_transaction_count(proxy.eth.default_account)
        trx_store = self.storage_contract.functions.store(148).buildTransaction({'nonce': right_nonce, 'gasPrice': 1})
        print('trx_store:', trx_store)
        trx_store['gas'] = trx_store['gas'] - 2 - EXTRA_GAS # less than estimated
        print('trx_store:', trx_store)
        trx_store_signed = proxy.eth.account.sign_transaction(trx_store, eth_account.key)
        print('trx_store_signed:', trx_store_signed)
        trx_store_hash = proxy.eth.send_raw_transaction(trx_store_signed.rawTransaction)
        print('trx_store_hash:', trx_store_hash.hex())
        trx_store_receipt = proxy.eth.wait_for_transaction_receipt(trx_store_hash)
        print('trx_store_receipt:', trx_store_receipt)
        self.assertEqual(trx_store_receipt['status'], 0)  # false Transaction mined but execution failed

    @unittest.skip("a.i.")
    def test_04_execute_with_bad_nonce(self):
        print("\ntest_04_execute_with_bad_nonce")
        bad_nonce = 1 + proxy.eth.get_transaction_count(proxy.eth.default_account)
        trx_store = self.storage_contract.functions.store(147).buildTransaction({'nonce': bad_nonce})
        print('trx_store:', trx_store)
        trx_store_signed = proxy.eth.account.sign_transaction(trx_store, eth_account.key)
        print('trx_store_signed:', trx_store_signed)
        try:
            trx_store_hash = proxy.eth.send_raw_transaction(trx_store_signed.rawTransaction)
            print('trx_store_hash:', trx_store_hash)
            self.assertTrue(False)
        except Exception as e:
            print('type(e):', type(e))
            print('e:', e)
            import json
            response = json.loads(str(e).replace('\'', '\"').replace('None', 'null'))
            print('response:', response)
            print('code:', response['code'])
            self.assertEqual(response['code'], -32002)
            print('substring_err_147:', SUBSTRING_LOG_ERR_147)
            logs = response['data']['logs']
            print('logs:', logs)
            log = [s for s in logs if SUBSTRING_LOG_ERR_147 in s][0]
            print(log)
            self.assertGreater(len(log), len(SUBSTRING_LOG_ERR_147))
            file_name = 'src/entrypoint.rs'
            self.assertTrue(file_name in log)

    @unittest.skip("a.i.")
    def test_05_transfer_one_gwei(self):
        print("\ntest_05_transfer_one_gwei")
        eth_account_alice = proxy.eth.account.create('alice')
        eth_account_bob = proxy.eth.account.create('bob')
        print('eth_account_alice.address:', eth_account_alice.address)
        print('eth_account_bob.address:', eth_account_bob.address)

        alice_balance_before_transfer = proxy.eth.get_balance(eth_account_alice.address)
        bob_balance_before_transfer = proxy.eth.get_balance(eth_account_bob.address)
        print('alice_balance_before_transfer:', alice_balance_before_transfer)
        print('bob_balance_before_transfer:', bob_balance_before_transfer)
        one_gwei = 1_000_000_000
        print('one_gwei:', one_gwei)

        trx_transfer = proxy.eth.account.sign_transaction(dict(
            nonce=proxy.eth.get_transaction_count(eth_account_alice.address),
            chainId=proxy.eth.chain_id,
            gas=987654321,
            gasPrice=0,
            to=eth_account_bob.address,
            value=one_gwei),
            eth_account_alice.key
        )

        print('trx_transfer:', trx_transfer)
        trx_transfer_hash = proxy.eth.send_raw_transaction(trx_transfer.rawTransaction)
        print('trx_transfer_hash:', trx_transfer_hash.hex())
        trx_transfer_receipt = proxy.eth.wait_for_transaction_receipt(trx_transfer_hash)
        print('trx_transfer_receipt:', trx_transfer_receipt)

        alice_balance_after_transfer = proxy.eth.get_balance(eth_account_alice.address)
        bob_balance_after_transfer = proxy.eth.get_balance(eth_account_bob.address)
        print('alice_balance_after_transfer:', alice_balance_after_transfer)
        print('bob_balance_after_transfer:', bob_balance_after_transfer)
        self.assertEqual(alice_balance_after_transfer, alice_balance_before_transfer - one_gwei)
        self.assertEqual(bob_balance_after_transfer, bob_balance_before_transfer + one_gwei)

    def test_06_transfer_one_and_a_half_gweis(self):
        print("\ntest_06_transfer_one_and_a_half_gweis")
        eth_account_alice = proxy.eth.account.create('alice')
        eth_account_bob = proxy.eth.account.create('bob')
        print('eth_account_alice.address:', eth_account_alice.address)
        print('eth_account_bob.address:', eth_account_bob.address)

        alice_balance_before_transfer = proxy.eth.get_balance(eth_account_alice.address)
        bob_balance_before_transfer = proxy.eth.get_balance(eth_account_bob.address)
        print('alice_balance_before_transfer:', alice_balance_before_transfer)
        print('bob_balance_before_transfer:', bob_balance_before_transfer)
        one_and_a_half_gweis = 1_500_000_000
        print('one_and_a_half_gweis:', one_and_a_half_gweis)

        trx_transfer = proxy.eth.account.sign_transaction(dict(
            nonce=proxy.eth.get_transaction_count(eth_account_alice.address),
            chainId=proxy.eth.chain_id,
            gas=987654321,
            gasPrice=0,
            to=eth_account_bob.address,
            value=one_and_a_half_gweis),
            eth_account_alice.key
        )

        print('trx_transfer:', trx_transfer)
        trx_transfer_hash = proxy.eth.send_raw_transaction(trx_transfer.rawTransaction)
        print('trx_transfer_hash:', trx_transfer_hash.hex())
        trx_transfer_receipt = proxy.eth.wait_for_transaction_receipt(trx_transfer_hash)
        print('trx_transfer_receipt:', trx_transfer_receipt)

        alice_balance_after_transfer = proxy.eth.get_balance(eth_account_alice.address)
        bob_balance_after_transfer = proxy.eth.get_balance(eth_account_bob.address)
        print('alice_balance_after_transfer:', alice_balance_after_transfer)
        print('bob_balance_after_transfer:', bob_balance_after_transfer)
        print('check https://github.com/neonlabsorg/neon-evm/issues/210')
        one_gwei = 1_000_000_000
        print('one_gwei:', one_gwei)
        self.assertEqual(alice_balance_after_transfer, alice_balance_before_transfer - one_gwei)
        self.assertEqual(bob_balance_after_transfer, bob_balance_before_transfer + one_gwei)


if __name__ == '__main__':
    unittest.main()
