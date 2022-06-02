# Execution Chain History Network

This document is the specification for the sub-protocol that supports on-demand availability of Ethereum execution chain history data.

## Overview

Execution chain history data consists of historical block headers, block bodies (transactions and ommer), and receipts.

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

#### Retrieval

* Block header by block header hash
* Block body by block header hash
* Block receipts by block header hash

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

### Content: Keys and Values

The chain history DHT stores the following data items:

* Block headers
* Block bodies
* Receipts

Each of these data items are represented as a key-value pair. Denote the key for a data item by `content-key`. Denote the value for an item as `content`.

All `content-key` values are encoded and decoded as an [`SSZ Union`](https://github.com/ethereum/consensus-specs/blob/dev/ssz/simple-serialize.md#union) type.
```
content-key = Union[blockheader, blockbody, receipt]
serialized-content-key = serialize(content-key)
```

#### Block Header

```
selector     = 0x00
content-key  = Container(chain-id: uint16, block-hash: Bytes32)
content      = rlp(header)
```

#### Block Body

```
selector                = 0x01
content-key             = Container(chain-id: uint16, block-hash: Bytes32)
content                 = Container(all-transactions, serialized-uncles)
all-transactions        = SSZList(serialized-transaction, max-length=2**14)
serialized-transaction  = SSZList(encoded-transaction: Byte, max-length=2**24)
encoded-transaction     =
  if transaction.is_typed:
    return type_byte + rlp.encode(transaction)
  else:
    return rlp.encode(transaction)
serialized-uncles       = SSZList(encoded-uncles: Byte, max-length=2**17)
encoded-uncles          = rlp.encode(list-of-uncle-headers)
```

Note the type-specific encoding might be different in future transaction types, but this encoding
works for all current transaction types.

#### Receipts

```
selector            = 0x02
content-key         = Container(chain-id: uint16, block-hash: Bytes32)
content             = SSZList(serialized-receipt, max-length=2**14)
serialized-receipt  = SSZList(encoded-receipt: Byte, max-length=2**23)
encoded-receipt     =
  if receipt.is_typed:
    return type_byte + rlp.encode(receipt)
  else:
    return rlp.encode(receipt)
```

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
