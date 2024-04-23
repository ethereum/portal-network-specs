# Execution Chain History Network

This document is the specification for the sub-protocol that supports on-demand availability of Ethereum execution chain history data.

## Overview

The chain history network is a [Kademlia](https://pdos.csail.mit.edu/~petar/papers/maymounkov-kademlia-lncs.pdf) DHT that uses the [Portal Wire Protocol](./portal-wire-protocol.md) to establish an overlay network on top of the [Discovery v5](https://github.com/ethereum/devp2p/blob/master/discv5/discv5-wire.md) protocol.

Execution chain history data consists of historical block headers, block bodies (transactions and ommer) and block receipts.

In addition, the chain history network provides individual epoch accumulators for the full range of pre-merge blocks mined before the transition to proof of stake.

### Data

#### Types

* Block headers
* Block bodies
    * Transactions
    * Ommers
* Receipts
* Header epoch accumulators (pre-merge only)

#### Retrieval

The network supports the following mechanisms for data retrieval:

* Block header by block header hash
* Block body by block header hash
* Block receipts by block header hash
* Header epoch accumulator by epoch accumulator hash

> The presence of the pre-merge header accumulators provides an indirect way to lookup blocks by their number, but is restricted to pre-merge blocks.  Retrieval of blocks by their number for post-merge blocks is not intrinsically supported within this network.

> This sub-protocol does **not** support retrieval of transactions by hash, only the full set of transactions for a given block. See the "Canonical Transaction Index" sub-protocol of the Portal Network for more information on how the portal network implements lookup of transactions by their individual hashes.


## Specification

### Distance Function

The history network uses the stock XOR distance metric defined in the portal wire protocol specification.


### Content ID Derivation Function

The history network uses the SHA256 Content ID derivation function from the portal wire protocol specification.


### Wire Protocol

The [Portal wire protocol](./portal-wire-protocol.md) is used as wire protocol for the history network.


#### Protocol Identifier

As specified in the [Protocol identifiers](./portal-wire-protocol.md#protocol-identifiers) section of the Portal wire protocol, the `protocol` field in the `TALKREQ` message **MUST** contain the value of `0x500B`.

#### Supported Message Types

The history network supports the following protocol messages:

- `Ping` - `Pong`
- `Find Nodes` - `Nodes`
- `Find Content` - `Found Content`
- `Offer` - `Accept`


#### `Ping.custom_data` & `Pong.custom_data`

In the history network the `custom_payload` field of the `Ping` and `Pong` messages is the serialization of an SSZ Container specified as `custom_data`:

```python
custom_data = Container(data_radius: uint256)
custom_payload = SSZ.serialize(custom_data)
```


### Routing Table

The history network uses the standard routing table structure from the Portal Wire Protocol.

### Node State

#### Data Radius

The history network includes one additional piece of node state that should be tracked.  Nodes must track the `data_radius` from the Ping and Pong messages for other nodes in the network.  This value is a 256 bit integer and represents the data that a node is "interested" in.  We define the following function to determine whether node in the network should be interested in a piece of content.

```python
interested(node, content) = distance(node.id, content.id) <= node.radius
```

A node is expected to maintain `radius` information for each node in its local node table. A node's `radius` value may fluctuate as the contents of its local key-value store change.

A node should track their own radius value and provide this value in all Ping or Pong messages it sends to other nodes.

### Data Types

#### Constants

We define the following constants which are used in the various data type definitions.

```python
MAX_TRANSACTION_LENGTH = 2**24  # ~= 16 million
# Maximum transaction body length is achieved by filling calldata with 0's
# until the block limit of (currently) 30M gas is reached.
# At a gas cost of 4 per 0-byte, that produces a 7.5MB transaction. We roughly
# double that size to a maximum of >16 million for some headroom. Note that
# EIP-4488 would put a roughly 1MB limit on transaction length, effectively. So
# increases are not planned (instead, the opposite).

MAX_TRANSACTION_COUNT = 2**14  # ~= 16k
# 2**14 simple transactions would use up >340 million gas at 21k gas each.
# Current gas limit tops out at 30 million gas.

MAX_RECEIPT_LENGTH = 2**27  # ~= 134 million
# Maximum receipt length is logging a bunch of data out, currently at a cost of
# 8 gas per byte. Since that is double the cost of 0 calldata bytes, the
# maximum size is roughly half that of the transaction: 3.75 million bytes.
# But there is more reason for protocol devs to constrain the transaction length,
# and it's not clear what the practical limits for receipts are, so we should add more buffer room.
# Imagine the cost drops by 2x and the block gas limit goes up by 8x. So we add 2**4 = 16x buffer.

_MAX_HEADER_LENGTH = 2**13  # = 8192
# Maximum header length is fairly stable at about 500 bytes. It might change at
# the merge, and beyond. Since the length is relatively small, and the future
# of the format is unclear to me, I'm leaving more room for expansion, and
# setting the max at about 8 kilobytes.

MAX_ENCODED_UNCLES_LENGTH = _MAX_HEADER_LENGTH * 2**4  # = 2**17 ~= 131k
# Maximum number of uncles is currently 2. Using 16 leaves some room for the
# protocol to increase the number of uncles.

MAX_WITHDRAWAL_COUNT = 16
# Number sourced from consensus specs
# https://github.com/ethereum/consensus-specs/blob/f7352d18cfb91c58b1addb4ea509aedd6e32165c/presets/mainnet/capella.yaml#L12
# MAX_WITHDRAWAL_COUNT = MAX_WITHDRAWALS_PER_PAYLOAD

WITHDRAWAL_LENGTH = 64
# Withdrawal: index (u64), validator_index (u64), address, amount (u64)
#   - 8 + 8 + 20 + 8 = 44 bytes
#   - allow extra space for rlp encoding overhead

SHANGHAI_TIMESTAMP = 1681338455
# Number sourced from EIP-4895
```

#### Encoding Content Values for Validation

The encoding choices generally favor easy verification of the data, minimizing decoding. For
example:
- `keccak(encoded-uncles) == header.uncles_hash`
- Each `encoded-transaction` can be inserted into a trie to compare to the
  `header.transactions_root`
- Each `encoded-receipt` can be inserted into a trie to compare to the `header.receipts_root`

Combining all of the block body in RLP, in contrast, would require that a validator loop through
each receipt/transaction and re-rlp-encode it, but only if it is a legacy transaction.


#### Block Header


```python
# Content types

PreMergeAccumulatorProof = Vector[Bytes32, 15]

BlockHeaderProof = Union[None, PreMergeAccumulatorProof]

BlockHeaderWithProof = Container[
  header: ByteList, # RLP encoded header in SSZ ByteList
  proof: BlockHeaderProof
]
```

```python
# Content and content key

block_header_key = Container(block_hash: Bytes32)
selector         = 0x00

block_header_with_proof = BlockHeaderWithProof(header: rlp.encode(header)), proof: proof)

content          = SSZ.serialize(block_header_with_proof)
content_key      = selector + SSZ.serialize(block_header_key)
```

> **_Note:_** The `BlockHeaderProof` allows to provide headers without a proof (`None`).
For pre-merge headers, clients SHOULD NOT accept headers without a proof
as there is the `PreMergeAccumulatorProof` solution available.
For post-merge headers, there is currently no proof solution and clients SHOULD
accept headers without a proof.

#### Block Body

After the addition of `withdrawals` to the block body in the [EIP-4895](https://eips.ethereum.org/EIPS/eip-4895),
clients need to support multiple encodings for the block body content type. For the time being,
since a client is required for block body validation it is recommended that clients implement
the following sequence to decode & validate block bodies.
- Receive raw block body content value.
- Fetch respective header from the network.
- Compare header timestamp against `SHANGHAI_TIMESTAMP` to determine what encoding scheme the block body uses.
- Decode the block body using either pre-shanghai or post-shanghai encoding.
- Validate the decoded block body against the roots in the header.

```python
block_body_key          = Container(block_hash: Bytes32)
selector                = 0x01

all_transactions        = SSZList(ssz_transaction, max_length=MAX_TRANSACTION_COUNT)
ssz_transaction         = SSZList(encoded_transaction: ByteList, max_length=MAX_TRANSACTION_LENGTH)
encoded_transaction     =
  if transaction.is_typed:
    return transaction.type_byte + rlp.encode(transaction)
  else:
    return rlp.encode(transaction)
ssz_uncles              = SSZList(encoded_uncles: ByteList, max_length=MAX_ENCODED_UNCLES_LENGTH)
encoded_uncles          = rlp.encode(list_of_uncle_headers)
all_withdrawals         = SSZList(ssz_withdrawal, max_length=MAX_WITHDRAWAL_COUNT)
ssz_withdrawal          = SSZList(encoded_withdrawal: ByteList, max_length=MAX_WITHDRAWAL_LENGTH)
encoded_withdrawal      = rlp.encode(withdrawal)

pre-shanghai content    = Container(all_transactions: SSZList(...), ssz_uncles: SSZList(...))
post-shanghai content   = Container(all_transactions: SSZList(...), ssz_uncles: SSZList(encoded_uncles), all_withdrawals: SSZList(...))
content_key             = selector + SSZ.serialize(block_body_key)
```

Note 1: The type-specific encoding might be different in future transaction types, but this encoding
works for all current transaction types.

Note 2: The `list_of_uncle_headers` refers to the array of uncle headers [defined in the devp2p spec](https://github.com/ethereum/devp2p/blob/master/caps/eth.md#block-encoding-and-validity).

#### Receipts

```python
receipt_key         = Container(block_hash: Bytes32)
selector            = 0x02

ssz_receipt         = SSZList(encoded_receipt: ByteList, max_length=MAX_RECEIPT_LENGTH)
encoded_receipt     =
  if receipt.is_typed:
    return type_byte + rlp.encode(receipt)
  else:
    return rlp.encode(receipt)

content             = SSZList(ssz_receipt, max_length=MAX_TRANSACTION_COUNT)
content_key         = selector + SSZ.serialize(receipt_key)
```

Note the type-specific encoding might be different in future receipt types, but this encoding works
for all current receipt types.


#### Epoch Accumulator

```python
epoch_accumulator_key = Container(epoch_hash: Bytes32)
selector              = 0x03
epoch_hash            = hash_tree_root(epoch_accumulator)

content               = SSZ.serialize(epoch_accumulator)
content_key           = selector + SSZ.serialize(epoch_accumulator_key)
```


### Algorithms

#### The "Pre Merge Accumulator"

The "Pre Merge Accumulator" is based on the [double-batched merkle log accumulator](https://ethresear.ch/t/double-batched-merkle-log-accumulator/571) that is currently used in the beacon chain.  This data structure is designed to allow nodes in the network to "forget" the deeper history of the chain, while still being able to reliably receive historical headers with a proof that the received header is indeed from the canonical chain (as opposed to an uncle mined at the same block height).  This data structure is only used for pre-merge blocks.

The accumulator is defined as an [SSZ](https://ssz.dev/) data structure with the following schema:

```python
EPOCH_SIZE = 8192 # blocks
MAX_HISTORICAL_EPOCHS = 131072  # 2**17

# An individual record for a historical header.
HeaderRecord = Container[block_hash: bytes32, total_difficulty: uint256]

# The records of the headers from within a single epoch
EpochAccumulator = List[HeaderRecord, max_length=EPOCH_SIZE]

PreMergeAccumulator = Container[
    historical_epochs: List[bytes32, max_length=MAX_HISTORICAL_EPOCHS],
    current_epoch: EpochAccumulator,
]
```

The algorithm for building the accumulator is as follows.


```python
def update_accumulator(accumulator: PreMergeAccumulator, new_block_header: BlockHeader) -> None:
    # get the previous total difficulty
    if len(accumulator.current_epoch) == 0:
        # genesis
        last_total_difficulty = 0
    else:
        last_total_difficulty = accumulator.current_epoch[-1].total_difficulty

    # check if the epoch accumulator is full.
    if len(accumulator.current_epoch) == EPOCH_SIZE:
        # compute the final hash for this epoch
        epoch_hash = hash_tree_root(accumulator.current_epoch)
        # append the hash for this epoch to the list of historical epochs
        accumulator.historical_epochs.append(epoch_hash)
        # initialize a new empty epoch
        accumulator.current_epoch = []

    # construct the concise record for the new header and add it to the current epoch.
    header_record = HeaderRecord(new_block_header.hash, last_total_difficulty + new_block_header.difficulty)
    accumulator.current_epoch.append(header_record)
```

The network provides no mechanism for acquiring the *master* version of this accumulator.  Clients are encouraged to solve this however they choose, with the suggestion that they include a frozen copy of the accumulator at the point of the merge within their client code, and provide a mechanism for users to override this value if they so choose.

#### PreMergeAccumulatorProof

The `PreMergeAccumulatorProof` is a Merkle proof as specified in the
[SSZ Merke proofs specification](https://github.com/ethereum/consensus-specs/blob/dev/ssz/merkle-proofs.md#merkle-multiproofs).

It is a Merkle proof for the `BlockHeader`'s block hash on the relevant
`EpochAccumulator` object. The selected `EpochAccumulator` must be the one where
the `BlockHeader`'s block hash is part of. The `GeneralizedIndex` selected must
match the leave of the `EpochAccumulator` merkle tree which holds the
`BlockHeader`'s block hash.

An `PreMergeAccumulatorProof` for a specific `BlockHeader` can be used to verify that
this `BlockHeader` is part of the canonical chain. This is done by verifying the
Merkle proof with the `BlockHeader`'s block hash as leave and the
`EpochAccumulator` digest as root. This digest is available in the
`PreMergeAccumulator`.

As the `PreMergeAccumulator` only accounts for blocks pre-merge, this proof can
only be used to verify blocks pre-merge.
