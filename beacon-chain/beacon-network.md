# Beacon Chain Network
**Notice**: This document is a work-in-progress for researchers and implementers.

This document is the specification for the Portal Network overlay network that supports the on-demand availability of Beacon Chain data.

## Overview

A beacon chain light client could keep track of the chain of beacon block headers by performing Light client state updates
following the light client [sync protocol](https://github.com/ethereum/consensus-specs/blob/dev/specs/altair/light-client/sync-protocol.md).
The [LightClientBootstrap](https://github.com/ethereum/consensus-specs/blob/dev/specs/altair/light-client/sync-protocol.md#lightclientbootstrap) structure allow setting up a
[LightClientStore](https://github.com/ethereum/consensus-specs/blob/dev/specs/altair/light-client/sync-protocol.md#lightclientstore) with the initial sync committee and block header from a user-configured trusted block root.

Once the client establishes a recent header, it could sync to other headers by processing objects of type [LightClientUpdate](https://github.com/ethereum/consensus-specs/blob/dev/specs/altair/light-client/sync-protocol.md#lightclientupdate),
[LightClientFinalityUpdate](https://github.com/ethereum/consensus-specs/blob/dev/specs/altair/light-client/sync-protocol.md#lightclientfinalityupdate)
and [LightClientOptimisticUpdate](https://github.com/ethereum/consensus-specs/blob/dev/specs/altair/light-client/sync-protocol.md#lightclientoptimisticupdate).
These data types allow a client to stay up-to-date with the beacon chain.

To verify canonicalness of an execution block header older than ~27 hours, we need the ongoing `BeaconState` accumulator (state.historical_summaries) which stores Merkle roots of recent history logs.

The Beacon Chain network is a [Kademlia](https://pdos.csail.mit.edu/~petar/papers/maymounkov-kademlia-lncs.pdf) DHT that forms an overlay network on top of
the [Discovery v5](https://github.com/ethereum/devp2p/blob/master/discv5/discv5-wire.md) network. The term *overlay network* means that the beacon chain network operates
with its routing table independent of the base Discovery v5 routing table and uses the extensible `TALKREQ` and `TALKRESP` messages from the base Discovery v5 protocol for communication.

The `TALKREQ` and `TALKRESP` protocol messages are application-level messages whose contents are specific to the Beacon Chain Light Client network. We specify these messages below.

The Beacon Chain network uses a modified version of the routing table structure from the Discovery v5 network and the lookup algorithm from section 2.3 of the Kademlia paper.

### Data

#### Types

* LightClientBootstrap
* LightClientUpdate
* LightClientFinalityUpdate
* LightClientOptimisticUpdate
* HistoricalSummaries

Light client data types are specified in light client [sync protocol](https://github.com/ethereum/consensus-specs/blob/dev/specs/altair/light-client/sync-protocol.md#containers).

#### Retrieval

The network supports the following mechanisms for data retrieval:

* `LightClientBootstrap` structure by a post-Altair beacon block root.
* `LightClientUpdatesByRange` - requests the `LightClientUpdate` instances in the sync committee period range [start_period, start_period + count), leading up to the current head sync committee period as selected by fork choice.
* The latest `LightClientFinalityUpdate` known by a peer.
* The latest `LightClientOptimisticUpdate` known by a peer.
* The latest `HistoricalSummaries` known by a peer.

## Specification

### Distance Function

The beacon chain network uses the stock XOR distance metric defined in the portal wire protocol specification.

### Content ID Derivation Function

The beacon chain network uses the SHA256 Content ID derivation function from the portal wire protocol specification.

### Wire Protocol

The [Portal wire protocol](./portal-wire-protocol.md) is used as the wire protocol for the Beacon Chain Light Client network.

#### Protocol Identifier

As specified in the [Protocol identifiers](./portal-wire-protocol.md#protocol-identifiers) section of the Portal wire protocol, the `protocol` field in the `TALKREQ` message **MUST** contain the value of `0x501A`.

#### Supported Messages Types

The beacon chain network supports the following protocol messages:

- `Ping` - `Pong`
- `Find Nodes` - `Nodes`
- `Find Content` - `Found Content`
- `Offer` - `Accept`

#### `Ping.custom_data` & `Pong.custom_data`

In the beacon chain network the `custom_payload` field of the `Ping` and `Pong` messages is the serialization of an SSZ Container specified as `custom_data`:

```
custom_data = Container(data_radius: uint256)
custom_payload = serialize(custom_data)
```

### Routing Table

The Beacon Chain Network uses the standard routing table structure from the Portal Wire Protocol.

### Node State

#### Data Radius

The Beacon Chain Network includes one additional piece of node state that should be tracked. Nodes must track the `data_radius`
from the Ping and Pong messages for other nodes in the network. This value is a 256 bit integer and represents the data that
a node is "interested" in.

We define the following function to determine whether node in the network should be interested in a piece of content:

```
interested(node, content) = distance(node.id, content.id) <= node.radius
```

A node is expected to maintain `radius` information for each node in its local node table. A node's `radius` value may fluctuate as the contents of its local key-value store change.

A node should track their own radius value and provide this value in all Ping or Pong messages it sends to other nodes.

### Data Types

The beacon chain DHT stores the following data items:

* LightClientBootstrap
* LightClientUpdate

The following data objects are ephemeral and we store only the latest values:

* LightClientFinalityUpdate
* LightClientOptimisticUpdate
* HistoricalSummaries

#### Constants

We use the following constants from the beacon chain specs which are used in the various data type definitions:

```py
# Maximum number of `LightClientUpdate` instances in a single request
# Defined in https://github.com/ethereum/consensus-specs/blob/dev/specs/altair/light-client/p2p-interface.md#configuration
MAX_REQUEST_LIGHT_CLIENT_UPDATES = 2**7  # = 128

# Maximum number of `HistoricalSummary` records
# Defined in https://github.com/ethereum/consensus-specs/blob/dev/specs/phase0/beacon-chain.md#state-list-lengths
HISTORICAL_ROOTS_LIMIT = 2**24  # = 16,777,216
```

#### ForkDigest
4-byte fork digest for the current beacon chain version and ``genesis_validators_root``.

#### LightClientBootstrap

```
light_client_bootstrap_key = Container(block_hash: Bytes32)
selector                   = 0x00

content                    = ForkDigest + SSZ.serialize(LightlientBootstrap)
content_key                = selector + SSZ.serialize(light_client_bootstrap_key)
```

#### LightClientUpdatesByRange

```
light_client_update_keys   = Container(start_period: uint64, count: uint64)
selector                   = 0x01

content                    = SSZList(ForkDigest + LightClientUpdate, max_lenght=MAX_REQUEST_LIGHT_CLIENT_UPDATES)
content_key                = selector + SSZ.serialize(light_client_update_keys)
```

#### LightClientFinalityUpdate

```
light_client_finality_update_key  = 0 (uint8)
selector                          = 0x02

content                           = ForkDigest + SSZ.serialize(light_client_finality_update)
content_key                       = selector + SSZ.serialize(light_client_finality_update_key)
```

> A `0` in the content key is equivalent to the request for the latest
LightClientFinalityUpdate that the requested node has available.

#### LightClientOptimisticUpdate

```
light_client_optimistic_update_key   = 0 (uint8)
selector                             = 0x03

content                              = ForkDigest + SSZ.serialize(light_client_optimistic_update)
content_key                          = selector + SSZ.serialize(light_client_optimistic_update_key)
```

> A `0` in the content key is equivalent to the request for the latest
LightClientOptimisticUpdate that the requested node has available.

#### HistoricalSummaries

Latest `HistoricalSummaries` object is stored in the network every 256 epochs (8192 slots).
```
HistoricalSummariesProof = Vector[Bytes32, 5]

historical_summaries_with_proof = HistoricalSummariesWithProof(
    epoch: uint64,
    # HistoricalSummary object is defined in consensus specs: 
    # https://github.com/ethereum/consensus-specs/blob/dev/specs/capella/beacon-chain.md#historicalsummary.
    historical_summaries: SSZList(HistoricalSummary, max_length=HISTORICAL_ROOTS_LIMIT),
    proof: HistoricalSummariesProof
)

historical_summaries_key   = 0 (uint8)
selector                   = 0x04

content                    = ForkDigest + SSZ.serialize(historical_summaries_with_proof)
content_key                = selector + SSZ.serialize(historical_summaries_key)
```

> A `0` in the content key is equivalent to the request for the latest
HistoricalSummaries that the requested node has available.

### Algorithms

#### Portal Gossip

TODO

#### Validation

Validating `LightClientFinalityUpdate` and `LightClientOptimisticUpdate` follows the gossip domain(gossipsub) [consensus specs](https://github.com/ethereum/consensus-specs/blob/dev/specs/altair/light-client/p2p-interface.md#the-gossip-domain-gossipsub).
