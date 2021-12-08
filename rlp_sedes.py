import functools
from typing import Any, Optional

from eth_typing import Address, BlockNumber, Hash32
from eth_utils import encode_hex, humanize_hash, keccak, to_canonical_address, big_endian_to_int,
import rlp
from rlp import sedes
from web3 import Web3

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
    w3_header = w3.eth.getBlock(block_number)
    header = BlockHeader(
        difficulty=w3_header["difficulty"],
        block_number=w3_header["number"],
        gas_limit=w3_header["gasLimit"],
        timestamp=w3_header["timestamp"],
        coinbase=to_canonical_address(w3_header["miner"]),
        parent_hash=Hash32(w3_header["parentHash"]),
        uncles_hash=Hash32(w3_header["sha3Uncles"]),
        state_root=Hash32(w3_header["stateRoot"]),
        transaction_root=Hash32(w3_header["transactionsRoot"]),
        receipt_root=Hash32(w3_header["receiptsRoot"]),
        bloom=big_endian_to_int(bytes(w3_header["logsBloom"])),
        gas_used=w3_header["gasUsed"],
        extra_data=bytes(w3_header["extraData"]),
        mix_hash=Hash32(w3_header["mixHash"]),
        nonce=bytes(w3_header["nonce"]),
    )
    if header.hash != Hash32(w3_header["hash"]):
        raise ValueError(
            f"Reconstructed header hash does not match expected: "
            f"expected={encode_hex(w3_header['hash'])}  actual={header.hex_hash}"
        )
    return header
