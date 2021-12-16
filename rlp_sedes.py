import functools
from typing import Any, Optional, Tuple, Sequence, NamedTuple

from eth_typing import Address, BlockNumber, Hash32, ChecksumAddress
from eth_utils import encode_hex, humanize_hash, keccak, to_canonical_address, big_endian_to_int, to_int, int_to_big_endian, decode_hex, to_bytes
from eth.db.trie import make_trie_root_and_nodes
import rlp
from rlp import sedes
from web3 import Web3
from web3.types import TxData, BlockIdentifier
from cytoolz import concat, groupby

address = sedes.Binary.fixed_length(20, allow_empty=True)
hash32 = sedes.Binary.fixed_length(32)
uint32 = sedes.BigEndianInt(32)
uint256 = sedes.BigEndianInt(256)
trie_root = sedes.Binary.fixed_length(32, allow_empty=True)


@functools.total_ordering
class BlockHeader(rlp.Serializable):  # type: ignore
    fields = [
        ("parent_hash", hash32),
        ("uncles_hash", hash32),
        ("coinbase", address),
        ("state_root", trie_root),
        ("transaction_root", trie_root),
        ("receipt_root", trie_root),
        ("bloom", uint256),
        ("difficulty", sedes.big_endian_int),
        ("block_number", sedes.big_endian_int),
        ("gas_limit", sedes.big_endian_int),
        ("gas_used", sedes.big_endian_int),
        ("timestamp", sedes.big_endian_int),
        ("extra_data", sedes.binary),
        ("mix_hash", sedes.binary),
        ("nonce", sedes.Binary(8, allow_empty=True)),
    ]

    def __init__(
        self,
        difficulty: int,
        block_number: BlockNumber,
        gas_limit: int,
        timestamp: int,
        coinbase: Address,
        parent_hash: Hash32,
        uncles_hash: Hash32,
        state_root: Hash32,
        transaction_root: Hash32,
        receipt_root: Hash32,
        bloom: int,
        gas_used: int,
        extra_data: bytes,
        mix_hash: Hash32,
        nonce: bytes,
    ) -> None:
        super().__init__(
            parent_hash=parent_hash,
            uncles_hash=uncles_hash,
            coinbase=coinbase,
            state_root=state_root,
            transaction_root=transaction_root,
            receipt_root=receipt_root,
            bloom=bloom,
            difficulty=difficulty,
            block_number=block_number,
            gas_limit=gas_limit,
            gas_used=gas_used,
            timestamp=timestamp,
            extra_data=extra_data,
            mix_hash=mix_hash,
            nonce=nonce,
        )

    def __str__(self) -> str:
        return "<BlockHeader #{0} {1}>".format(
            self.block_number, humanize_hash(self.hash),
        )

    def __eq__(self, other: Any) -> bool:
        if not type(self) is type(other):
            return False
        return bool(self.hash == other.hash)

    def __lt__(self, other: "BlockHeader") -> bool:
        return bool(self.block_number < other.block_number)

    _hash: Optional[Hash32] = None

    @property
    def hash(self) -> Hash32:
        if self._hash is None:
            self._hash = Hash32(keccak(rlp.encode(self)))
        return self._hash

    @property
    def hex_hash(self) -> str:
        return encode_hex(self.hash)


def retrieve_header(w3: Web3, block_number: int) -> BlockHeader:
    w3_block = w3.eth.getBlock(block_number)
    header = BlockHeader(
        difficulty=w3_block["difficulty"],
        block_number=w3_block["number"],
        gas_limit=w3_block["gasLimit"],
        timestamp=w3_block["timestamp"],
        coinbase=to_canonical_address(w3_block["miner"]),
        parent_hash=Hash32(w3_block["parentHash"]),
        uncles_hash=Hash32(w3_block["sha3Uncles"]),
        state_root=Hash32(w3_block["stateRoot"]),
        transaction_root=Hash32(w3_block["transactionsRoot"]),
        receipt_root=Hash32(w3_block["receiptsRoot"]),
        bloom=big_endian_to_int(bytes(w3_block["logsBloom"])),
        gas_used=w3_block["gasUsed"],
        extra_data=bytes(w3_block["extraData"]),
        mix_hash=Hash32(w3_block["mixHash"]),
        nonce=bytes(w3_block["nonce"]),
    )
    if header.hash != Hash32(w3_header["hash"]):
        raise ValueError(
            f"Reconstructed header hash does not match expected: "
            f"expected={encode_hex(w3_header['hash'])}  actual={header.hex_hash}"
        )
    return header


class LegacyTransaction(rlp.Serializable):  # type: ignore
    fields = (
        ('nonce', sedes.big_endian_int),
        ('gas_price', sedes.big_endian_int),
        ('gas', sedes.big_endian_int),
        ('to', address),
        ('value', sedes.big_endian_int),
        ('data', sedes.binary),
        ('v', sedes.big_endian_int),
        ('r', sedes.big_endian_int),
        ('s', sedes.big_endian_int),
    )

    def encode(self) -> bytes:
        return rlp.encode(self)


class AccountAccesses(rlp.Serializable):
    fields = (
        ('account', address),
        ('storage_keys', sedes.CountableList(sedes.BigEndianInt(32))),
    )


class AccessListTransaction(rlp.Serializable):
    fields = (
        ('chain_id', sedes.big_endian_int),
        ('nonce', sedes.big_endian_int),
        ('gas_price', sedes.big_endian_int),
        ('gas', sedes.big_endian_int),
        ('to', address),
        ('value', sedes.big_endian_int),
        ('data', sedes.binary),
        ('access_list', sedes.CountableList(AccountAccesses)),
        ('v', sedes.big_endian_int),
        ('r', sedes.big_endian_int),
        ('s', sedes.big_endian_int),
    )

    def encode(self) -> bytes:
        return rlp.encode(self)


class DynamicFeeTransaction(rlp.Serializable):
    fields = (
        ('chain_id', sedes.big_endian_int),
        ('nonce', sedes.big_endian_int),
        ('max_priority_fee_per_gas', sedes.big_endian_int),
        ('max_fee_per_gas', sedes.big_endian_int),
        ('gas', sedes.big_endian_int),
        ('to', address),
        ('value', sedes.big_endian_int),
        ('data', sedes.binary),
        ('access_list', sedes.CountableList(AccountAccesses)),
        ('v', sedes.big_endian_int),
        ('r', sedes.big_endian_int),
        ('s', sedes.big_endian_int),
    )

    def encode(self) -> bytes:
        return rlp.encode(self)


class TypedTransaction:
    def __init__(self, transaction) -> None:
        if isinstance(transaction, LegacyTransaction):
            self.transaction_type = 0
        elif isinstance(transaction, AccessListTransaction):
            self.transaction_type = 1
        elif isinstance(transaction, DynamicFeeTransaction):
            self.transaction_type = 2
        else:
            raise ValueError("Unsupported")
        self.transaction = transaction

    def encode(self) -> bytes:
        return to_bytes(self.transaction_type) + self.transaction.encode()


class BlockBody(rlp.Serializable):  # type: ignore
    fields = [
        ("transactions", sedes.CountableList(sedes.binary)),
        ("uncles", sedes.CountableList(BlockHeader)),
    ]

    def __init__(
        self,
        transactions: Sequence[bytes],
        uncles: Sequence[BlockHeader],
    ) -> None:
        super().__init__(
            transactions=transactions,
            uncles=uncles,
        )


class Log(rlp.Serializable):
    fields = [
        ('address', address),
        ('topics', sedes.CountableList(uint32)),
        ('data', sedes.binary)
    ]


class Receipt(rlp.Serializable):
    fields = [
        ('state_root', sedes.binary),
        ('gas_used', sedes.big_endian_int),
        ('bloom', uint256),
        ('logs', sedes.CountableList(Log))
    ]

    def encode(self) -> bytes:
        return rlp.encode(self)


def _to_canonical_receipt(w3_receipt) -> Receipt:
    logs = tuple(
        Log(
            to_canonical_address(w3_log["address"]),
            tuple(big_endian_to_int(topic) for topic in w3_log["topics"]),
            decode_hex(w3_log["data"]),
        ) for w3_log in w3_receipt["logs"]
    )

    if 'root' in w3_receipt:
        root = decode_hex(w3_receipt["root"])
    else:
        root = w3_receipt["status"].to_bytes(32, 'big')
    return Receipt(
        root,
        w3_receipt["gasUsed"],
        to_int(w3_receipt["logsBloom"]),
        logs,
    )


def retrieve_receipts_bundle(w3: Web3, block_number: int) -> Tuple[Receipt, ...]:
    w3_block = w3.eth.getBlock(block_number)
    w3_receipts = tuple(
        w3.eth.getTransactionReceipt(tx_hash) for tx_hash in w3_block["transactions"]
    )
    receipts = tuple(
        _to_canonical_receipt(w3_receipt) for w3_receipt in w3_receipts
    )
    receipts_root, _ = make_trie_root_and_nodes(receipts)
    #if receipts_root != w3_block["receiptsRoot"]:
    #    raise ValueError(
    #        f"Reconstructed receipt trie does not match: ours={receipts_root}  theirs={w3_block['receiptsRoot']}"
    #    )
    return receipts


def _to_canonical_transaction(w3_transaction) -> Tuple[bytes, ...]:
    try:
        transaction_type = to_int(hexstr=w3_transaction["type"])
    except KeyError:
        transaction_type = 0

    if transaction_type == 0:
        transaction = LegacyTransaction(
            w3_transaction["nonce"],
            w3_transaction["gasPrice"],
            w3_transaction["gas"],
            to_canonical_address(w3_transaction["to"]) if w3_transaction["to"] is not None else b'',
            w3_transaction["value"],
            decode_hex(w3_transaction["input"]),
            w3_transaction["v"],
            big_endian_to_int(w3_transaction["r"]),
            big_endian_to_int(w3_transaction["s"]),
        )
    elif transaction_type == 1:
        transaction = AccessListTransaction(
            to_int(hexstr=w3_transaction["chainId"]),
            w3_transaction["nonce"],
            w3_transaction["gasPrice"],
            w3_transaction["gas"],
            to_canonical_address(w3_transaction["to"]) if w3_transaction["to"] is not None else b'',
            w3_transaction["value"],
            decode_hex(w3_transaction["input"]),
            w3_transaction["accessList"],
            w3_transaction["v"],
            big_endian_to_int(w3_transaction["r"]),
            big_endian_to_int(w3_transaction["s"]),
        )
    elif transaction_type == 2:
        transaction = DynamicFeeTransaction(
            to_int(hexstr=w3_transaction["chainId"]),
            w3_transaction["nonce"],
            w3_transaction["maxPriorityFeePerGas"],
            w3_transaction["maxFeePerGas"],
            w3_transaction["gas"],
            to_canonical_address(w3_transaction["to"]) if w3_transaction["to"] is not None else b'',
            w3_transaction["value"],
            decode_hex(w3_transaction["input"]),
            w3_transaction["accessList"],
            w3_transaction["v"],
            big_endian_to_int(w3_transaction["r"]),
            big_endian_to_int(w3_transaction["s"]),
        )
    else:
        raise ValueError(f"Unsupported transaction type: type={transaction_type}  tx={w3_transaction}")

    return transaction


BERLIN_MAINNET_BLOCK = BlockNumber(12244000)


def retrieve_block(w3: Web3, block_number: int) -> BlockHeader:
    w3_block = w3.eth.getBlock(block_number, full_transactions=True)
    transactions = tuple(
        _to_canonical_transaction(transaction)
        for transaction
        in w3_block["transactions"]
    )
    if block_number >= BERLIN_MAINNET_BLOCK:
        transactions = tuple(
            TypedTransaction(transaction)
            for transaction in transactions
        )
    uncles = tuple(
        _to_canonical_uncle(uncle)
        for uncle
        in w3_block["uncles"]
    )
    transactions_root, _ = make_trie_root_and_nodes(transactions)
    if transactions_root != w3_block["transactionsRoot"]:
        raise ValueError(
            f"Reconstructed transaction trie does not match: ours={transactions_root}  theirs={w3_block['transactionsRoot']}"
        )
    uncles_hash = keccak(rlp.encode(uncles))
    if uncles_hash != w3_block["sha3Uncles"]:
        raise ValueError(
            f"Reconstructed ommers trie does not match: ours={uncles_hash}  theirs={w3_block['sha3Uncles']}"
        )

    return BlockBody(transactions=transactions, uncles=uncles)


class Account(rlp.Serializable):
    """
    RLP object for accounts.
    """
    fields = [
        ('nonce', sedes.big_endian_int),
        ('balance', sedes.big_endian_int),
        ('storage_root', trie_root),
        ('code_hash', hash32)
    ]

    def __init__(self,
                 nonce: int,
                 balance: int,
                 storage_root: bytes,
                 code_hash: bytes,
                 ) -> None:
        super().__init__(nonce, balance, storage_root, code_hash)

    def __repr__(self) -> str:
        return (
            f"Account(nonce={self.nonce}, balance={self.balance}, "
            f"storage_root=0x{self.storage_root.hex()}, "
            f"code_hash=0x{self.code_hash.hex()})"
        )


ADDR_WETH = "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"


def get_proof_size(w3: Web3, address: Address) -> int:
    w3_proof = w3.eth.getProof(address, [])
    proof_elements = w3_proof["accountProof"]
    account = Account(
        nonce=w3_proof["nonce"],
        balance=w3_proof["balance"],
        storage_root=w3_proof["storageHash"],
        code_hash=w3_proof["codeHash"],
    )

    return len(rlp.encode(proof_elements))


class AccountAccessList(NamedTuple):
    address: ChecksumAddress
    slots: Tuple[int, ...]


AccessList = Tuple[AccountAccessList, ...]


def get_tx_access_list(w3: Web3, w3_transaction: TxData) -> AccessList:
    tx_params = {
        'to': w3_transaction['to'],
        'from': w3_transaction['from'],
        #'gas': hex(w3_transaction['gas']),
        'gasPrice': hex(w3_transaction['gasPrice']),
        'value': hex(w3_transaction['value']),
        'input': w3_transaction['input'],
    }
    w3_access_list = w3.access_list.create_access_list(tx_params, hex(w3_transaction['blockNumber'] - 1))
    return tuple(
        AccountAccessList(item['address'], item['storageKeys']) for item in w3_access_list['accessList']
    )


def get_block_access_list(w3: Web3, block_identifier: BlockIdentifier) -> AccessList:
    w3_block = w3.eth.getBlock(block_identifier, full_transactions=True)
    tx_access_lists = tuple(
        get_tx_access_list(w3, w3_transaction)
        for w3_transaction in w3_block['transactions']
    )
    grouped_access_lists = groupby(0, concat(tx_access_lists))
    assert False


def get_recently_used_storage_slots(w3: Web3) -> Tuple[Tuple[Address, Tuple[int, ...]], ...]:
    for w3_block in _iter_blocks(w3):
        for w3_transaction in w3_block['transactions']:
            ...
