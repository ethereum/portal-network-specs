# Chain History Storage Network

This document is a preliminary specification for a networking protocol that supports on-demand availability of Ethereum chain history data.

## Overview

Chain history data consists of historical block headers and block bodies, where a block body consists of transactions and transaction receipts.

The data stored in the chain history storage network will support the following [eth](https://github.com/ethereum/devp2p/blob/master/caps/eth.md) protocol requests:

* `GetBlockHeaders (0x03)`
* `GetBlockBodies (0x05)`
* `GetReceipts (0x0f)`

The chain history storage network is a [Kademlia](https://pdos.csail.mit.edu/~petar/papers/maymounkov-kademlia-lncs.pdf) DHT that forms an overlay network on top of a [Discovery v5](https://github.com/ethereum/devp2p/blob/master/discv5/discv5-wire.md) network.

The history network uses the following protocol messages from the Discovery v5 network:

* `PING (0x01)`
* `PONG (0x02)`
* `FINDNODE (0x03)`
* `NODES (0x04)`
* `TALKREQ (0x05)`
* `TALKRESP (0x06)`

The `TALKREQ` and `TALKRESP` protocol messages are application-level messages whose contents are specific to the history protocol. We specify these messages below.

The history protocol uses the node table structure from the Discovery v5 network and the lookup algorithm from section 2.3 of the Kademlia paper.

### Data

Types:

* Block headers
* Block bodies
    * Transactions
    * Receipts

Lookups:

* Block header by block header hash
* Block body by block header hash
* Block receipts by block header hash

This specification does not support block lookups by number or transaction lookups by hash. To support these lookups, we will require a specification for a block header accumulator so that we can return the canonical block for a given height or the transaction for a given hash included in some canonical block.

### Data Bridge

Participants in the `eth` protocol are responsible for injecting data into the network. These nodes act as a bridge between the `eth` protocol and the chain history network. Once the data is present within the network, that data is distributed to nodes "close" to that data. We define a notion of distance between some node and some data item below.

### Data Completeness
In order to ensure that the network holds the entirety of the chain history, a separate process searches for missing data. Upon discovery of some missing data, that node issues a request to a bridge node for that data. The bridge node responds with the data, and it is distributed in the same way that new history is distributed.

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

We derive a `content-id` from the `content-key` as `H(content-key)` where `H` denotes the [placeholder] hash function, which outputs 32-byte values. The `content-id` represents the key in the DHT that we use for `distance` calculations.

All `content-key` values are encoded and decoded according to SSZ sedes.

#### Block Header

```
content-key  = Container(chain-id: uint16, content-type: uint8, block-hash: Bytes32)
content-type = 0x01
```

#### Block Body

```
content-key  = Container(chain-id: uint16, content-type: uint8, block-hash: Bytes32)
content-type = 0x02
```

#### Receipts

```
content-key  = Container(chain-id: uint16, content-type: uint8, block-hash: Bytes32)
content-type = 0x03
```

### Radius

We define a `distance` function that maps a `node-id` and `content-id` pair to a 256-bit unsigned integer identically to the `distance` function for pairs of `node-id` values.

Each node specifies a `radius` value, a 256-bit unsigned integer that represents the data that a node is "interested" in.

```
interested(node, content) = distance(node.id, content.id) <= node.radius
```

A node is expected to maintain `radius` information for each node in its local node table. A node's `radius` value may fluctuate as the contents of its local key-value store change.

### Protocol Messages

All protocol messages are transmitted via the `TALKREQ` and `TALKRESP` messages defined by the Discovery v5 protocol.

Below is the general message encoding for all `TALKREQ` messages.

```
protocol              = portal-history
request               = protocol-message-type || protocol-message
protocol-message-type = uint8
protocol-message      = byte array
```

Below is the general message encoding for all `TALKRESP` messages.

```
response              = protocol-message-type || protocol-message
protocol-message-type = uint8
protocol-message      = byte array
```

All `protocol-message` values are encoded and decoded according to SSZ sedes.

If the size of a message would exceed the max packet size of 1280 bytes, then the transmission of the message contents would occur over [uTP](https://github.com/ethereum/stateless-ethereum-specs/blob/master/discv5-utp.md).

uTP connections are initiated with randomly generated connection IDs. Upon sending a message with some `connection-id`, the sender should initiate a uTP stream using `connection-id`. Upon receiving a message that contains some `connection-id`, the recipient should listen for an incoming uTP connection with `connection-id`.

NOTE: The `Offer`/`Accept`/`Store` messages do not conform to the request/response paradigm of Discovery v5. We plan to propose a change to the base protocol definition to loosen the language.

#### Ping (0x01)

Communicate `radius` information of the sender, and request `radius` information of the recipient.

```
protocol-message-type = 0x01
protocol-message      = Container(radius: uint256)
```

#### Pong (0x02)

In response to a `Ping` message, communicate `radius` information of the sender.

```
protocol-message-type = 0x02
protocol-message      = Container(radius: uint256)
```

#### FindNode (0x03)

Request a list of ENR values for nodes whose `logdistance` from the recipient's `node-id` is equal to one of the specified values.

```
protocol-message-type = 0x03
protocol-message      = Container(distances: List[uint8, 256])
```

Each element of `distances` **MUST** be unique. A zero value in the `distances` list represents a request for the recipient's ENR value.

#### FoundNodes (0x04)

In response to a `FindNode` message, communicate a list of RLP-encoded ENR values for nodes whose `logdistance` value satisfies the request.

```
protocol-message-type = 0x04
protocol-message      = Container(total: uint8, enrs: List[Bytes, 32])
```

The recipient may know of more than 32 nodes that satisfy the request. In this case, the recipient will need to send multiple `FoundNodes` messages in response to the `FindNode` message.

Here, `total` denotes the total number of `FoundNodes` messages that the sender of the `FindNode` message should expect in response.

Each ENR **MUST** be unique to some `node-id`. Each ENR **MUST** correspond to an element in the `distances` field of the `FindNode` request.

#### FindContent (0x05)

Request the data for `content` with `content-key`, or a list of ENR values for nodes whose `distance` from `content-id` is smaller than that of the recipient.

The encoding of `content-key` for all possible data items is specified above.

```
protocol-message-type = 0x05
protocol-message      = Container(content-key: Bytes)
```

#### FoundContent (0x06)

In response to a `FindContent` message, communicate one of the following:

* A connection ID for a uTP stream to transmit the requested  data
* A list of RLP-encoded ENR values with maximum length of 32
* A byte-array that encodes the requested data

```
protocol-message-type = 0x06
protocol-message      = Container(connection-id: Bytes4, enrs: List[Bytes, 32], content: Bytes)
```

If the node does not hold the requested content, and the node does not know of any nodes with eligible ENR values, then the node should return `connection-id` as a zero byte array, `enrs` as an empty list and `content` as an empty byte-array.

#### Offer (0x07)

Communicate to the recipient that the data for `content-key` is available for transmission.

```
protocol-message-type = 0x07
protocol-message      = Container(content-key: Bytes)
```

#### Accept (0x08)

In response to a `Offer` message, request the data for `content-key`.

```
protocol-message-type = 0x08
protocol-message      = Container(content-key: Bytes)
```

If a node transmits a `Accept` message, then we expect that node to store the corresponding data locally following the subsequent `Store` message.

#### Store (0x09)

In response to a `Accept` message, communicate one of the following:

* A connection ID for a uTP stream to transmit the requested  data
* A byte-array that encodes the requested data

```
protocol-message-type = 0x09
protocol-message      = Container(connection-id: Bytes4, content: Bytes)
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

### Lookup

We use the lookup algorithm described in section 2.3 of the Kademlia paper. A "node lookup" is the execution of the algorithm to find the `k` closest nodes to some `node-id`. A "content lookup" is the execution of the algorithm to find the data for `content-id` or the `k` closest nodes to `content-id`.

A `FindNode` request corresponds to a node lookup, and a `FindContent` request corresponds to a content lookup.

The lookup algorithm is also used to identify nodes that should receive `Offer` messages to store some data.

### Joining the Network

We follow the join procedure described in the Kademlia paper.

In order to join the network, a node `u` must know some node `v` who is already participating in the network. Node `u` inserts `v` into the appropriate k-bucket and then sends a `FindNode` request to `v` for its own node ID. Then, node `u` refreshes all k-buckets with distances further than its closest neighbor. To refresh a bucket, a node selects a random node ID in the bucket's range and performs a `FindNode` for that ID.

### Finding Nodes

A node's routing table is initially populated by the `FindNode` messages that the node sends when it joins the network.

Following the join phase, a node's k-buckets are generally kept fresh by network traffic. When a node learns of a new contact (through node lookups), it attempts to insert the contact into the appropriate k-bucket. A node keeps track of the last node lookup it performed for each k-bucket, and it will regularly refresh any k-buckets with no recent lookups.

### Finding Content

To find a piece of content for `content-id`, a node performs a content lookup via `FindContent`. If the lookup succeeds, then the requestor sends a `Offer` message for the content to the closest node it observed that did not return the value and whose `radius` contains `content-id`.

### Storing Content

To store a piece of content with key `content-id`, a node performs a lookup to find the `k` closest nodes with radii that contain `content-id`. Then the node sends `Offer` RPCs to those nodes. For any node that responds to the `Offer` RPC with a `Accept` RPC, the local node responds with a `Store` RPC for the content.

The network cannot make guarantees about the storage of particular content. A lazy node may ignore all `Offer` RPCs. A malicious node may send `Accept` RPCs and ignore the `Store` RPCs. The offer-accept mechanism is in place to require that nodes explicitly accept some data before another node attempts to transmit that data. The mechanism prevents the unnecessary consumption of bandwidth in the presence of lazy nodes. However, it does not defend against malicious nodes who accept offers for data with no intent to store it.
