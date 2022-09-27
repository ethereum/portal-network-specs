# Beacon Chain Light Client Network
**Notice**: This document is a work-in-progress for researchers and implementers.

This document is the specification for the Portal Network overlay network that supports the on-demand availability of Beacon Chain light client data.

## Overview

A beacon chain light client could keep track of the chain of beacon block headers by performing Light client state updates
following the light client [sync protocol](https://github.com/ethereum/consensus-specs/blob/dev/specs/altair/light-client/sync-protocol.md).
The [LightClientBootstrap](https://github.com/ethereum/consensus-specs/blob/dev/specs/altair/light-client/sync-protocol.md#lightclientbootstrap) structure allow setting up a
[LightClientStore](https://github.com/ethereum/consensus-specs/blob/dev/specs/altair/light-client/sync-protocol.md#lightclientstore) with the initial sync committee and block header from a user-configured trusted block root.

Once the client establishes a recent header, it could sync to other headers by processing objects of type [LightClientUpdate](https://github.com/ethereum/consensus-specs/blob/dev/specs/altair/light-client/sync-protocol.md#lightclientupdate),
[LightClientFinalityUpdate](https://github.com/ethereum/consensus-specs/blob/dev/specs/altair/light-client/sync-protocol.md#lightclientfinalityupdate)
and [LightClientOptimisticUpdate](https://github.com/ethereum/consensus-specs/blob/dev/specs/altair/light-client/sync-protocol.md#lightclientoptimisticupdate).
These data types allow a client to stay up-to-date with the beacon chain.

The Beacon Chain Light Client network is a [Kademlia](https://pdos.csail.mit.edu/~petar/papers/maymounkov-kademlia-lncs.pdf) DHT that forms an overlay network on top of
the [Discovery v5](https://github.com/ethereum/devp2p/blob/master/discv5/discv5-wire.md) network. The term *overlay network* means that the light client network operates
with its routing table independent of the base Discovery v5 routing table and uses the extensible `TALKREQ` and `TALKRESP` messages from the base Discovery v5 protocol for communication.

The `TALKREQ` and `TALKRESP` protocol messages are application-level messages whose contents are specific to the Beacon Chain Light Client network. We specify these messages below.

The Beacon Chain Light Client network uses a modified version of the routing table structure from the Discovery v5 network and the lookup algorithm from section 2.3 of the Kademlia paper.

### Portal Gossip Algorithm

A gossip network allows participants to receive regular updates on a particular data type. The key point of differentiation between a portal network gossip
channel and a regular gossip channel, e.g. the gossip topic `beacon_block` used by regular beacon chain clients, is that a portal network participant could choose an <em>interest radius</em> `r`.
Participants only process messages that are within their chosen radius boundary.

- Each gossip participant has a `node_id`. A `node_id` is a 256 bit unsigned integer, i.e. `0 <= node_id < 2**256`.
- There is a distance function. It measures the distance between two `node_id`. It also measures the distance between `node_id` and `content_id`.

#### Validation
Validating `LightClientFinalityUpdate` and `LightClientOptimisticUpdate` follows the gossip domain(gossipsub) [consensus specs](https://github.com/ethereum/consensus-specs/blob/dev/specs/altair/light-client/p2p-interface.md#the-gossip-domain-gossipsub).

### Data

#### Types

* LightClientBootstrap
* LightClientUpdate
* LightClientFinalityUpdate
* LightClientOptimisticUpdate

All data types are specified in light client [sync protocol](https://github.com/ethereum/consensus-specs/blob/dev/specs/altair/light-client/sync-protocol.md#containers).

#### Retrieval

* Requests the `LightClientBootstrap` structure corresponding to a given post-Altair beacon block root.
* `LightClientUpdatesByRange` - requests the `LightClientUpdate` instances in the sync committee period range [start_period, start_period + count), leading up to the current head sync committee period as selected by fork choice.
* The latest `LightClientFinalityUpdate` known by a peer.
* The latest `LightClientOptimisticUpdate` known by a peer.

## Specification

### Distance

Nodes in the light client network are represented by their [EIP-778 Ethereum Node Record (ENR)](https://eips.ethereum.org/EIPS/eip-778) from the Discovery v5 network.
A node's `node-id` is derived according to the node's identity scheme, which is specified in the node's ENR. A node's `node-id` represents its address in the DHT.

The `node-id` is a 32-byte identifier. We define the `distance` function that maps a pair of `node-id` values to a 256-bit unsigned integer identically to the Discovery v5 network.

```
distance(n1, n2) = n1 XOR n2
```

Similarly, we define a `logdistance` function identically to the Discovery v5 network.

```
logdistance(n1, n2) = log2(distance(n1, n2))
```

### Content: Keys and Values

The beacon chain light client DHT stores the following data items:

* LightClientBootstrap
* LightClientUpdate

The following data objects are ephemeral and we store only the latest values:

* LightClientFinalityUpdate
* LightClientOptimisticUpdate

Each of these data items are represented as a key-value pair.

- The "key" for each data item is defined as `content_key`.
- The "value" for each data item is defined as `content`.

See each of the individual data item definitions for their individual `content` and `content_key` definitions.

#### Constants

```py
# Maximum number of `LightClientUpdate` instances in a single request
MAX_REQUEST_LIGHT_CLIENT_UPDATES = 2**7  # = 128
```

#### LightClientBootstrap

```
light_client_bootstrap_key = Container(block_hash: Bytes32)
selector                   = 0x00

content                    = SSZ.serialize(LightlientBootstrap)
content_key                = selector + SSZ.serialize(light_client_bootstrap_key)
```

#### LightClientUpdatesByRange

```
light_client_update_keys   = Container(start_period: uint64, count: uint64)
selector                   = 0x01

content                    = SSZList(LightClientUpdate, max_lenght=MAX_REQUEST_LIGHT_CLIENT_UPDATES)
content_key                = selector + SSZ.serialize(light_client_update_keys)
```

#### LightClientFinalityUpdate

```
light_client_finality_update_key  = Container(None)
selector                          = 0x02

content                           = SSZ.serialize(light_client_finality_update)
content_key                       = selector + SSZ.serialize(light_client_finality_update_key)
```

> A `None` in the content key is equivalent to the request for the latest
LightClientFinalityUpdate that the requested node has available.

#### LightClientOptimisticUpdate

```
light_client_optimistic_update_key   = Container(None)
selector                             = 0x03

content                              = SSZ.serialize(light_client_optimistic_update)
content_key                          = selector + SSZ.serialize(light_client_optimistic_update_key)
```

> A `None` in the content key is equivalent to the request for the latest
LightClientOptimisticUpdate that the requested node has available.

#### Content ID

We derive a `content-id` from the `content_key` as `H(content_key)` where `H` denotes the SHA-256 hash function, which outputs 32-byte values. The `content-id` represents the key in the DHT that we use for `distance` calculations.

### Radius

We define a `distance` function that maps a `node-id` and `content-id` pair to a 256-bit unsigned integer identically to the `distance` function for pairs of `node-id` values.

Each node specifies a `radius` value, a 256-bit unsigned integer that represents the data that a node is "interested" in.

```
interested(node, content) = distance(node.id, content.id) <= node.radius
```

A node is expected to maintain `radius` information for each node in its local node table. A node's `radius` value may fluctuate as the contents of its local key-value store change.

### Wire Protocol

The [Portal wire protocol](./portal-wire-protocol.md) is used as the wire protocol for the Beacon Chain Light Client network.

As specified in the [Protocol identifiers](./portal-wire-protocol.md#protocol-identifiers) section of the Portal wire protocol, the `protocol` field in the `TALKREQ` message **MUST** contain the value of `0x501A`.

The beacon chain light client network supports the following protocol messages:
- `Ping` - `Pong`
- `Find Nodes` - `Nodes`
- `Find Content` - `Found Content`
- `Offer` - `Accept`

In the beacon chain light client network the `custom_payload` field of the `Ping` and `Pong` messages is the serialization of an SSZ Container specified as `custom_data`:
```
custom_data = Container(data_radius: uint256)
custom_payload = serialize(custom_data)
```

## Algorithms and Data Structures

### Node State

We adopt the node state from the Discovery v5 protocol. Assume identical definitions for the replication parameter `k` and a node's k-bucket table. Also, assume that the routing table follows the structure and evolution described in section 2.4 of the Kademlia paper.

Nodes keep information about other nodes in a routing table of k-buckets. This routing table is distinct from the node's underlying Discovery v5 routing table.

A node associates the following tuple with each entry in its routing table:

```
node-entry := (node-id, radius, ip, udp)
```

The `radius` value is the only node information specific to the overlay protocol. This information is refreshed by the `Ping` and `Pong` protocol messages.

A node should regularly refresh the information it keeps about its neighbors. We follow section 4.1 of the Kademlia paper to improve the efficiency of these refreshes. A node delays `Ping` checks until it has a useful message to send to its neighbor.

When a node discovers some previously unknown node and the corresponding k-bucket is full, the newly discovered node is put into a replacement cache sorted by the time last seen. If a node in the k-bucket fails a liveliness check, and the replacement cache for that bucket is non-empty, then that node is replaced by the most recently seen node in the replacement cache.

Consider a node in some k-bucket to be "stale" if it fails to respond to β messages in a row, where β is a system parameter. β may be a function of the number of previous successful liveliness checks or the age of the neighbor. If the k-bucket is not full, and the corresponding replacement cache is empty, then stale nodes should only be flagged and not removed. This ensures that a node that goes offline temporarily does not void its k-buckets.
