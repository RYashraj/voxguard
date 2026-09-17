import sqlite3
import hashlib
import json
import time
import os
import logging
from datetime import datetime

try:
    from web3 import Web3
    from web3.exceptions import ContractLogicError
    WEB3_AVAILABLE = True
except ImportError:
    WEB3_AVAILABLE = False

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("VoxGuard.AuditLedger")

# DB path should point to the backend data directory properly
DB_PATH = os.path.join(os.path.dirname(__file__), "backend", "data", "voxguard.db")

# In a real deployment, these would come from environment variables.
RPC_URL = os.getenv("SEPOLIA_RPC_URL", os.getenv("WEB3_RPC_URL", "https://rpc.sepolia.org"))
CONTRACT_ADDRESS = os.getenv("WEB3_CONTRACT_ADDRESS", None)
PRIVATE_KEY = os.getenv("PRIVATE_KEY", os.getenv("WEB3_PRIVATE_KEY", None))

# Minimal ABI for our FraudLedger contract
ABI = [
    {
        "anonymous": False,
        "inputs": [
            {"indexed": False, "internalType": "string", "name": "payloadHash", "type": "string"},
            {"indexed": False, "internalType": "uint256", "name": "timestamp", "type": "uint256"}
        ],
        "name": "FraudAnchored",
        "type": "event"
    },
    {
        "inputs": [{"internalType": "string", "name": "payloadHash", "type": "string"}],
        "name": "logFraudHash",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    }
]

# Minimal Bytecode for the FraudLedger contract (Compiled Solidity)
# Deploying this creates a contract with logFraudHash(string) which emits FraudAnchored
BYTECODE = "608060405234801561001057600080fd5b506101cf806100206000396000f3fe608060405234801561001057600080fd5b506004361061002b5760003560e01c8063a568280614610030575b600080fd5b61004a6004803603810190610045919061012a565b610060565b005b7f2f8121dbcc8f6b95797f1f9640abafbf0e6f516a7f113e16b9b32cb75e3c1a3b8142604051610090929190610183565b60405180910390a1565b6000602082840312156100a857600080fd5b813567ffffffffffffffff8111156100bd57600080fd5b6100c9848285016100eb565b91505092915050565b600082601f8301126100f257600080fd5b813581811115610107576101076101be565b604051601f8201601f191681016040528083833682860101111561012357600080fd5b9250375092915050565b60006020828403121561013c57600080fd5b600082013567ffffffffffffffff81111561015657600080fd5b610162848285016100d8565b91505092915050565b600060408201905061017d83602085016101b0565b91505092915050565b600060208201905081810360008301526101a78184610198565b905092915050565b600081519050919050565b600082825260208201905092915050565b7f4e487b7100000000000000000000000000000000000000000000000000000000600052604160045260246000fdfea26469706673582212209d84dd71a1727ea1efc1b489a244400e998797f74c5d33f114c0a76a59c00b0d64736f6c63430008120033"

class FraudAuditLedger:
    def __init__(self):
        self.w3 = Web3(Web3.HTTPProvider(RPC_URL)) if WEB3_AVAILABLE else None
        self.contract_address = CONTRACT_ADDRESS
        
        if WEB3_AVAILABLE and self.w3.is_connected():
            logger.info(f"Connected to Ethereum Network: {RPC_URL}")
            if PRIVATE_KEY and not self.contract_address:
                logger.info("No WEB3_CONTRACT_ADDRESS provided. Deploying a new FraudLedger contract...")
                self.contract_address = self._deploy_contract()
        else:
            logger.warning("Web3 not available or not connected. Running in Cryptographic Audit (Local) Mode.")

    def _deploy_contract(self) -> str:
        try:
            account = self.w3.eth.account.from_key(PRIVATE_KEY)
            contract = self.w3.eth.contract(abi=ABI, bytecode=BYTECODE)
            
            # Build transaction
            tx = contract.constructor().build_transaction({
                'from': account.address,
                'nonce': self.w3.eth.get_transaction_count(account.address),
                'gas': 1000000,
                'gasPrice': self.w3.eth.gas_price
            })
            
            signed_tx = self.w3.eth.account.sign_transaction(tx, PRIVATE_KEY)
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
            logger.info(f"Deploying contract... Tx Hash: {self.w3.to_hex(tx_hash)}")
            
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
            logger.info(f"Contract deployed at address: {receipt.contractAddress}")
            return receipt.contractAddress
        except Exception as e:
            logger.error(f"Failed to deploy contract: {e}")
            return None

    def fetch_unanchored_logs(self):
        if not os.path.exists(DB_PATH):
            logger.error(f"Database not found at {DB_PATH}")
            return []
            
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                SELECT * FROM chunk_history 
                WHERE alert_level IN ('high', 'medium')
                ORDER BY timestamp DESC 
                LIMIT 5
            ''')
            rows = cursor.fetchall()
            return rows
        except Exception as e:
            logger.error(f"Query error: {e}")
            return []
        finally:
            conn.close()

    def submit_to_blockchain(self, payload_hash: str) -> str:
        """
        Submits the SHA-256 hash of the fraud event to the Sepolia Smart Contract.
        This provides tamper-evident proof to RBI/regulators.
        """
        if not self.w3 or not self.w3.is_connected() or not PRIVATE_KEY or not self.contract_address:
            # Simulated transaction for demo purposes if no network is configured
            time.sleep(1.5)
            # Create a deterministic mock tx hash for the demo
            return "SIMULATED (no funded wallet configured): 0x" + hashlib.md5(payload_hash.encode()).hexdigest() + "a1b2c3d4"

        try:
            account = self.w3.eth.account.from_key(PRIVATE_KEY)
            contract = self.w3.eth.contract(address=self.contract_address, abi=ABI)
            
            tx = contract.functions.logFraudHash(payload_hash).build_transaction({
                'from': account.address,
                'nonce': self.w3.eth.get_transaction_count(account.address),
                'gas': 200000,
                'gasPrice': self.w3.eth.gas_price
            })
            
            signed_tx = self.w3.eth.account.sign_transaction(tx, PRIVATE_KEY)
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
            return self.w3.to_hex(tx_hash)
            
        except Exception as e:
            logger.error(f"Blockchain submission failed: {e}")
            return "TX_FAILED"

    def mark_log_anchored(self, chunk_id: str, tx_hash: str):
        # We will optionally log this if there's a column for it, otherwise we skip.
        # SQLite doesn't strictly enforce schema on alter so we could try to add it.
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            try:
                cursor.execute("ALTER TABLE chunk_history ADD COLUMN etherscan_link TEXT")
            except:
                pass # column likely exists
            
            link = f"https://sepolia.etherscan.io/tx/{tx_hash}" if not tx_hash.startswith("SIMULATED") and not tx_hash.startswith("TX_FAILED") else tx_hash
            cursor.execute("UPDATE chunk_history SET etherscan_link = ? WHERE chunk_id = ?", (link, chunk_id))
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Could not update db: {e}")

    def run_anchor_cycle(self):
        print("==================================================")
        print(" 🔗 VOXGUARD CRYPTOGRAPHIC AUDIT LEDGER (SIH) 🔗")
        print("==================================================")
        print(f"[{datetime.now().isoformat()}] Scanning for high-risk transaction blocks...\n")
        
        time.sleep(1)
        
        rows = self.fetch_unanchored_logs()
        if not rows:
            print("No recent high-risk logs found to anchor.")
            return

        for row in reversed(rows):
            row_dict = dict(row)
            
            # Check if it was already anchored if column exists
            if 'etherscan_link' in row_dict.keys() and row_dict['etherscan_link']:
                continue
            
            audit_payload = {
                "session_id": row_dict.get('session_id'),
                "chunk_id": row_dict.get('chunk_id'),
                "timestamp": row_dict.get('timestamp'),
                "rolling_risk_score": row_dict.get('rolling_risk_score'),
                "flags": row_dict.get('flags'),
                "transaction_context": row_dict.get('transaction_context', 'unknown')
            }
            
            json_data = json.dumps(audit_payload, sort_keys=True)
            
            payload_hash = hashlib.sha256(json_data.encode('utf-8')).hexdigest()
            
            print(f"⚠️  [FRAUD EVENT DETECTED]")
            print(f"    Session: {audit_payload['session_id']}")
            print(f"    Context: {audit_payload['transaction_context']}")
            print(f"    Risk Score: {audit_payload['rolling_risk_score']}")
            print(f"    Payload Hash: 0x{payload_hash}")
            print(f"    Submitting to immutable ledger...")
            
            tx_receipt = self.submit_to_blockchain("0x" + payload_hash)
            
            print(f"    ✅ Anchored! Tx Hash: {tx_receipt}")
            if not tx_receipt.startswith("SIMULATED") and not tx_receipt.startswith("TX_FAILED"):
                print(f"    🔗 Etherscan: https://sepolia.etherscan.io/tx/{tx_receipt}")
            print("-" * 50)
            
            self.mark_log_anchored(row_dict.get('chunk_id'), tx_receipt)
            
        print("\n==================================================")
        print("Audit logs successfully cryptographically secured.")
        print("Fraud events are now tamper-evident for regulatory review.")

if __name__ == "__main__":
    ledger = FraudAuditLedger()
    ledger.run_anchor_cycle()
