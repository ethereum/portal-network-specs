# Execution Chain History Network

This document is the specification for the sub-protocol that supports on-demand availability of Ethereum execution chain history data.

## Overview

Execution chain history data consists of historical block headers, block bodies (transactions and ommer), and receipts.
In addition, it facilitates acquisition of a snapshot of the "Header Accumulator" data structure.

The chain history network is a [Kademlia](https://pdos.csail.mit.edu/~petar/papers/maymounkov-kademlia-lncs.pdf) DHT that forms an overlay network on top of the [Discovery v5](https://github.com/ethereum/devp2p/blob/master/discv5/discv5-wire.md) network. The term *overlay network* means that the history network operates with its own independent routing table and uses the extensible `TALKREQ` and `TALKRESP` messages from the base Discovery v5 protocol for communication.

The `TALKREQ` and `TALKRESP` protocol messages are application-level messages whose contents are specific to the history network. We specify these messages below.

The history network uses the node table structure from the Discovery v5 network and the lookup algorithm from section 2.3 of the Kademlia paper.

### Data

#### Types

* Block headers
* Block bodies
    * Transactions
    * Omners
* Receipts
* Header epoch accumulators
* Header master accumulator

#### Retrieval

* Block header by block header hash
* Block body by block header hash
* Block receipts by block header hash
* Header epoch accumulator by epoch accumulator hash
* Header master accumulator by master accumulator hash or by requesting latest


<!-- TODO: we can actually provide header by block number or block by block
number by requesting the right epoch accumulator, so this could be adjusted -->
> This sub-protocol does **not** support:
>
> - Header by block number
> - Block by block number
> - Transaction by hash
>
> Support for the indices needed to do these types of lookups is the responsibility of the "Execution Canonical Indices" sub-protocol of the Portal Network.


## Specification

### Distance

Nodes in the history network are represented by their [EIP-778 Ethereum Node Record (ENR)](https://eips.ethereum.org/EIPS/eip-778) from the Discovery v5 network. A node's `node-id` is derived according to the node's identity scheme, which is specified in the node's ENR. A node's `node-id` represents its address in the DHT.

The `node-id` is a 32-byte identifier. We define the `distance` function that maps a pair of `node-id` values to a 256-bit unsigned integer identically to the Discovery v5 network.

```
distance(n1, n2) = n1 XOR n2
```

Similarly, we define a `logdistance` function identically to the Discovery v5 network.

```
logdistance(n1, n2) = log2(distance(n1, n2))
```

### The "Header Accumulator"

The "Header Accumulator" is based on the [double-batched merkle log accumulator](https://ethresear.ch/t/double-batched-merkle-log-accumulator/571) that is currently used in the beacon chain.  This data structure is designed to allow nodes in the network to "forget" the deeper history of the chain, while still being able to reliably receive historical headers with a proof that the received header is indeed from the canonical chain (as opposed to an uncle mined at the same block height).

The accumulator is defined as an [SSZ](https://ssz.dev/) data structure with the following schema:

```python
EPOCH_SIZE = 8192 # blocks
MAX_HISTORICAL_EPOCHS = 131072  # 2**17

# An individual record for a historical header.
HeaderRecord = Container[block_hash: bytes32, total_difficulty: uint256]

# The records of the headers from within a single epoch
EpochAccumulator = List[HeaderRecord, max_length=EPOCH_SIZE]

MasterAccumulator = Container[
    historical_epochs: List[bytes32, max_length=MAX_HISTORICAL_EPOCHS],
    current_epoch: EpochAccumulator,
]
```

The algorithm for managing the accumulator is as follows.

> TODO: provide a written spec too

```python
def update_accumulator(accumulator: MasterAccumulator, new_block_header: BlockHeader) -> None:
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

#### Growth over time

Each `HeaderRecord` is 64 bytes meaning the `EpochAccumulator` can range from `0 - 64 * EPOCH_SIZE` bytes (0-512KB) over the course of a single epoch.

The `Accumulator.historical_epochs` grows by 32 bytes per epoch.

At a 13 second block time we expect:

- ~1 epochs per day
- ~6 epochs per week
- ~25 epochs per month
- ~296 epochs per year

Ignoring fluxuations in the size of `Accumulator.current_epoch` we should expect the size of the accumulator to grow at a rate of roughly 10kb per year.

### Content: Keys and Values

The chain history DHT stores the following data items:

* Block headers
* Block bodies
* Receipts
* Header epoch accumulators
* Header master accumulator

Each of these data items are represented as a key-value pair. Denote the key for a data item by `content-key`. Denote the value for an item as `content`.

All `content_key` values are encoded and decoded as an [`SSZ Union`](https://github.com/ethereum/consensus-specs/blob/dev/ssz/simple-serialize.md#union) type.
```
content_key = Union[block_header_key, block_body_key, receipt_key, epoch_accumulator_key, master_accumulator_key]
serialized_content_key = SSZ.serialize(content_key)
```

#### Constants

```py
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
```

#### Block Header

```
block_header_key = Container(chain_id: uint16, block_hash: Bytes32)
selector         = 0x00

content          = rlp.encode(header)
```

#### Block Body

```
block_body_key          = Container(chain_id: uint16, block_hash: Bytes32)
selector                = 0x01

content                 = Container(all_transactions, ssz_uncles)
all_transactions        = SSZList(ssz_transaction, max_length=MAX_TRANSACTION_COUNT)
ssz_transaction         = SSZList(encoded_transaction: Byte, max_length=MAX_TRANSACTION_LENGTH)
encoded_transaction     =
  if transaction.is_typed:
    return type_byte + rlp.encode(transaction)
  else:
    return rlp.encode(transaction)
ssz_uncles              = SSZList(encoded_uncles: Byte, max_length=MAX_ENCODED_UNCLES_LENGTH)
encoded_uncles          = rlp.encode(list_of_uncle_headers)
```

Note the type-specific encoding might be different in future transaction types, but this encoding
works for all current transaction types.

#### Receipts

```
receipt_key         = Container(chain_id: uint16, block_hash: Bytes32)
selector            = 0x02

content             = SSZList(ssz_receipt, max_length=MAX_TRANSACTION_COUNT)
ssz_receipt         = SSZList(encoded_receipt: Byte, max_length=MAX_RECEIPT_LENGTH)
encoded_receipt     =
  if receipt.is_typed:
    return type_byte + rlp.encode(receipt)
  else:
    return rlp.encode(receipt)
```

#### Epoch Accumulator

```
epoch_accumulator_key = Container(epoch_hash: Bytes32)
selector              = 0x03
epoch_hash            = hash_tree_root(epoch_accumulator)

content               = SSZ.serialize(epoch_accumulator)
```

#### Master Accumulator

```
master_accumulator_key = Union[None, master_hash: Bytes32]
selector               = 0x04
master_hash            = hash_tree_root(master_accumulator)

content                = SSZ.serialize(master_accumulator)
```

> A `None` in the content key is equivalent to the request of the latest
master accumulator that the requested node has available.

Note the type-specific encoding might be different in future receipt types, but this encoding works
for all current receipt types.

#### Encoding Content Values for Validation

The encoding choices generally favor easy verification of the data, minimizing decoding. For
example:
- `keccak(encoded-uncles) == header.uncles_hash`
- Each `encoded-transaction` can be inserted into a trie to compare to the
  `header.transactions_root`
- Each `encoded-receipt` can be inserted into a trie to compare to the `header.receipts_root`

Combining all of the block body in RLP, in contrast, would require that a validator loop through
each receipt/transaction and re-rlp-encode it, but only if it is a legacy transaction.

#### Content ID

We derive a `content-id` from the `content-key` as `H(serialized-content-key)` where `H` denotes the SHA-256 hash function, which outputs 32-byte values. The `content-id` represents the key in the DHT that we use for `distance` calculations.

<!-- TODO: the content-id of the accumulators could probably be directly
the hash_tree_root value, to avoid another hashing operation? -->

### Radius

We define a `distance` function that maps a `node-id` and `content-id` pair to a 256-bit unsigned integer identically to the `distance` function for pairs of `node-id` values.

Each node specifies a `radius` value, a 256-bit unsigned integer that represents the data that a node is "interested" in.

```
interested(node, content) = distance(node.id, content.id) <= node.radius
```

A node is expected to maintain `radius` information for each node in its local node table. A node's `radius` value may fluctuate as the contents of its local key-value store change.

### Wire Protocol

The [Portal wire protocol](./portal-wire-protocol.md) is used as wire protocol for the history network.

As specified in the [Protocol identifiers](./portal-wire-protocol.md#protocol-identifiers) section of the Portal wire protocol, the `protocol` field in the `TALKREQ` message **MUST** contain the value of `0x500B`.

The history network supports the following protocol messages:
- `Ping` - `Pong`
- `Find Nodes` - `Nodes`
- `Find Content` - `Found Content`
- `Offer` - `Accept`

In the history network the `custom_payload` field of the `Ping` and `Pong` messages is the serialization of an SSZ Container specified as `custom_data`:
```
custom_data = Container(data_radius: uint256)
custom_payload = serialize(custom_data)
```

<!-- TODO: Add the accumulator root hash as custom data to the ping/pong
payloads as was done in the header gossip network? Lets figure this out when
also figuring out how to kick off with a accumulator snapshot. -->


## Algorithms and Data Structures

### Node State

We adapt the node state from the Discovery v5 protocol. Assume identical definitions for the replication parameter `k` and a node's k-bucket table. Also assume that the routing table follows the structure and evolution described in section 2.4 of the Kademlia paper.

Nodes keep information about other nodes in a routing table of k-buckets. This routing table is distinct from the node's underlying Discovery v5 routing table.

A node associates the following tuple with each entry in its routing table:

```
node-entry := (node-id, radius, ip, udp)
```

The `radius` value is the only node information specific to the overlay protocol. This information is refreshed by the `Ping` and `Pong` protocol messages.

A node should regularly refresh the information it keeps about its neighbors. We follow section 4.1 of the Kademlia paper to improve efficiency of these refreshes. A node delays `Ping` checks until it has a useful message to send to its neighbor.

When a node discovers some previously unknown node, and the corresponding k-bucket is full, the newly discovered node is put into a replacement cache sorted by time last seen. If a node in the k-bucket fails a liveness check, and the replacement cache for that bucket is non-empty, then that node is replaced by the most recently seen node in the replacement cache.

Consider a node in some k-bucket to be "stale" if it fails to respond to β messages in a row, where β is a system parameter. β may be a function of the number of previous successful liveness checks or of the age of the neighbor. If the k-bucket is not full, and the corresponding replacement cache is empty, then stale nodes should only be flagged and not removed. This ensures that a node who goes offline temporarily does not void its k-buckets.


### Accumulator Acquisition

New nodes entering the network will need to acquire an up-to-date snapshot of the accumulator.

The Header Gossip Network does provide the ability to acquire a snapshot of another node's accumulator. Since the accumulator is not a part of the base protocol (and thus is not part of the block header), nodes will have to do their own due diligence to either build the full accumulator from genesis or to adequately verify and validate a snapshot acquired from another peer.

TODO: provide basic probabilistic approach for verification of an accumulator snapshot.
