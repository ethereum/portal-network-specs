# Execution Canonical Block Index Network

This document is the specification for the sub-protocol that supports on-demand availability of Ethereum execution chain block number to block header hash index data.

## Overview

The canonical block index network is a [Kademlia](https://pdos.csail.mit.edu/~petar/papers/maymounkov-kademlia-lncs.pdf) DHT that uses the [Portal Wire Protocol](./portal-wire-protocol.md) to establish an overlay network on top of the [Discovery v5](https://github.com/ethereum/devp2p/blob/master/discv5/discv5-wire.md) protocol.

Execution chain canonical block index data consists of historical block headers via block number

### Data

#### Types

- Block Number Index

#### Retrieval

The network supports the following mechanisms for data retrieval:

- Block header by block header number

## Specification

### Distance Function

The canonical block index network uses the stock XOR distance metric defined in the portal wire protocol specification.

### Content ID Derivation Function

The history network uses the SHA256 Content ID derivation function from the portal wire protocol specification.

### Wire Protocol

The [Portal wire protocol](./portal-wire-protocol.md) is used as wire protocol for the history network.

#### Protocol Identifier

As specified in the [Protocol identifiers](./portal-wire-protocol.md#protocol-identifiers) section of the Portal wire protocol, the `protocol` field in the `TALKREQ` message **MUST** contain the value of `0x5010`.

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

#### Block Number Index

```python
# Content types

HistoricalHashesAccumulatorProof = Vector[Bytes32, 15]

BlockHeaderProof = Union[None, HistoricalHashesAccumulatorProof]

BlockHeaderWithProof = Container(
  header: ByteList[MAX_HEADER_LENGTH], # RLP encoded header in SSZ ByteList
  proof: BlockHeaderProof
)
```


```python
# Content and content key

block_number_key = Container(block_number: Bytes32)
block_header_with_proof = BlockHeaderWithProof(header: rlp.encode(header), proof: proof)
selector         = 0x10


content          = SSZ.serialize(block_header_with_proof)
content_key      = selector + SSZ.serialize(block_number_key)
```

> **_Note:_** The `BlockHeaderProof` allows to provide headers without a proof (`None`).
For pre-merge headers, clients SHOULD NOT accept headers without a proof
as there is the `HistoricalHashesAccumulatorProof` solution available.
For post-merge headers, there is currently no proof solution and clients MAY
accept headers without a proof.

### Validation

We have 2 possible models for this network
- (Option 1) Block Index stores the header
- (Option 2) Block Index stores the header's hash

Pro's of Option 1
- One less step for validation than option 2 which would then require fetching the header from the history network
- Copy's the validation scheme used in the history network, which inherently validates the block number is valid
- Has less latency as you don't have to make 2 synchronous requests only 1
- simpler seeding

Con's of Option 1
- Requires less then 10GB to store the full index

Pro's of Option 2
- Requires less then 1GB to store the full index
  
Con's of Option 2
- Requires a synchronous fetch from the History Network for the block header, which adds a lot of latency
- seeding requires the header to validate the content key is correct


Option 1 was choose due to
- having lower latency
- only 9GB more storage required
- simpler seeding


