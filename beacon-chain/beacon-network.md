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

The [Portal wire protocol](../portal-wire-protocol.md) is used as the wire protocol for the Beacon Chain Light Client network.

#### Protocol Identifier

As specified in the [Protocol identifiers](../portal-wire-protocol.md#protocol-identifiers) section of the Portal wire protocol, the `protocol` field in the `TALKREQ` message **MUST** contain the value of `0x501A`.

#### Supported Messages Types

The beacon chain network supports the following protocol messages:

- `Ping` - `Pong`
- `FindNodes` - `Nodes`
- `FindContent` - `FoundContent`
- `Offer` - `Accept`

#### `Ping.payload` & `Pong.payload`

In the beacon chain network the `payload` field of the `Ping` and `Pong` messages. The first packet between another client MUST be [Type 0: Client Info, Radius, and Capabilities Payload](../ping-extensions/extensions/type-0.md). Then upgraded to the latest payload supported by both of the clients.

List of currently supported payloads, by latest to oldest.
-  [Type 1 Basic Radius Payload](../ping-extensions/extensions/type-1.md)

### Routing Table

The Beacon Chain Network uses the standard routing table structure from the Portal Wire Protocol.

### Node State

#### Data Storage and Retrieval

Nodes running the beacon chain network MUST store and provide all beacon light
client content for the range as is specified by the consensus light client
specifications: https://github.com/ethereum/consensus-specs/blob/dev/specs/altair/light-client/full-node.md#deriving-light-client-data

This means that data radius and the concept of closeness to data is not
applicable for this content.

When a node cannot fulfill a request for any of this data it SHOULD return an
empty list of ENRs. It MAY return a list of ENRs of nodes that have provided
this data in the past.

When a node gossips any of this data, it MUST use [random gossip](./beacon-network.md/#random-gossip) instead of neighborhood gossip.


#### Data Radius

The Beacon Chain Network includes one additional piece of node state that should be tracked. Nodes must track the `data_radius`
from the Ping and Pong messages for other nodes in the network. This value is a 256 bit integer and represents the data that
a node is "interested" in.

We define the following function to determine whether node in the network should be interested in a piece of content:

```python
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

```python
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

```python
light_client_bootstrap_key = Container(block_hash: Bytes32)
selector                   = 0x10

content                    = ForkDigest + SSZ.serialize(LightClientBootstrap)
content_key                = selector + SSZ.serialize(light_client_bootstrap_key)
```

#### LightClientUpdatesByRange

```python
light_client_update_keys   = Container(start_period: uint64, count: uint64)
selector                   = 0x11

content                    = List(ForkDigest + LightClientUpdate, limit=MAX_REQUEST_LIGHT_CLIENT_UPDATES)
content_key                = selector + SSZ.serialize(light_client_update_keys)
```

> If a node cannot provide one of the `LightClientUpdate` objects in the
the requested range it MUST NOT reply any content.

#### LightClientFinalityUpdate

```python
light_client_finality_update_key  = Container(finalized_slot: uint64)
selector                          = 0x12

content                           = ForkDigest + SSZ.serialize(light_client_finality_update)
content_key                       = selector + SSZ.serialize(light_client_finality_update_key)
```

> The `LightClientFinalityUpdate` objects are ephemeral and only the latest is
of use to the node. The content key requires the `finalized_slot` to be provided
so that this object can be more efficiently gossiped. Nodes should decide to
reject an `LightClientFinalityUpdate` in case it is not newer than the one they
already have.
For `FindContent` requests, a node will either know the last previous finalized
slot, if it has been following the updates, or it will have to guess slots that
are potentially finalized.

#### LightClientOptimisticUpdate

```python
light_client_optimistic_update_key   = Container(optimistic_slot: uint64)
selector                             = 0x13

content                              = ForkDigest + SSZ.serialize(light_client_optimistic_update)
content_key                          = selector + SSZ.serialize(light_client_optimistic_update_key)
```

> The `LightClientOptimisticUpdate` objects are ephemeral and only the latest is
of use to the node. The content key requires the `optimistic_slot` (corresponding to
the `signature_slot` in the the update) to be provided so that this
object can be more efficiently gossiped. Nodes should decide to reject an
`LightClientOptimisticUpdate` in case it is not newer than the one they already have.
For `FindContent` requests, a node should compute the current slot based on its local clock
and then use that slot as a starting point for retrieving the most recent update.

#### HistoricalSummaries

Latest `HistoricalSummariesWithProof` object is stored in the network every epoch, even though the `historical_summaries` only updates every period (8192 slots). This is done to have an up to date proof every epoch, which makes it easier to verify the `historical_summaries` when starting the beacon light client sync.

```python

# Definition of generalized index (gindex):
# https://github.com/ethereum/consensus-specs/blob/d8cfdf2626c1219a40048f8fa3dd103ae8c0b040/ssz/merkle-proofs.md#generalized-merkle-tree-index
HISTORICAL_SUMMARIES_GINDEX_CAPELLA* = get_generalized_index(capella.BeaconState, 'historical_summaries') # = 59
HISTORICAL_SUMMARIES_GINDEX_ELECTRA* = get_generalized_index(BeaconState, 'historical_summaries') # = 91

HistoricalSummariesProofCapella = Vector[Bytes32, floorlog2(HISTORICAL_SUMMARIES_GINDEX_CAPELLA)]
HistoricalSummariesProof = Vector[Bytes32, floorlog2(HISTORICAL_SUMMARIES_GINDEX_ELECTRA)]

# HistoricalSummary object is defined in consensus specs:
# https://github.com/ethereum/consensus-specs/blob/dev/specs/capella/beacon-chain.md#historicalsummary.

HistoricalSummariesWithProofCapella = Container(
    epoch: uint64,
    historical_summaries: List(HistoricalSummary, limit=HISTORICAL_ROOTS_LIMIT),
    proof: HistoricalSummariesProofCapella
)

HistoricalSummariesWithProof = Container(
    epoch: uint64,
    historical_summaries: List(HistoricalSummary, limit=HISTORICAL_ROOTS_LIMIT),
    proof: HistoricalSummariesProof
)

# For Capella + Deneb (to be deprecated after the Electra fork):
historical_summaries_with_proof = HistoricalSummariesWithProofCapella(...)

# For Electra and onwards:
historical_summaries_with_proof = HistoricalSummariesWithProof(...)

historical_summaries_key   = Container(epoch: uint64)
selector                   = 0x14

content                    = ForkDigest + SSZ.serialize(historical_summaries_with_proof)
content_key                = selector + SSZ.serialize(historical_summaries_key)
```

> A node SHOULD return the latest `HistoricalSummariesWithProof` object it has in response to a `FindContent` request.
> If a node cannot provide the requested or newer `HistoricalSummariesWithProof` object, it MUST NOT reply with any content.

### Algorithms

#### Random Gossip

We use the term *random gossip* to refer to the process through which content is disseminated to a random set DHT nodes.

The process works as follows:
- A DHT node is offered piece of content that is specified to be gossiped via
random gossip.
- The node selects a random node from a random bucket and does this for `n` nodes.
- The node offers the content to the `n` selected nodes.

#### Validation

##### LightClientBootstrap

While still light client syncing a node SHOULD only allow to store an offered `LightClientBootstrap` that it knows to be canonical.
That is, a bootstrap which it can verify as it maps to a known trusted-block-root.
E.g. trusted-block-root(s) provided through client config or pre-loaded in the client.

Once a node is light client synced, it can verify a new `LightClientBootstrap` and then store and re-gossip it on successful verification.

##### LightClientUpdate

While still light client syncing a node SHOULD NOT store any offered `LightClientUpdate`. It SHOULD retrieve the updates required to sync and store those when verified.

Once a node is light client synced, it can verify a new `LightClientUpdate` and then store and re-gossip it on successful verification.

##### LightClientFinalityUpdate & LightClientOptimisticUpdate

Validating `LightClientFinalityUpdate` and `LightClientOptimisticUpdate` follows the gossip domain(gossipsub) [consensus specs](https://github.com/ethereum/consensus-specs/blob/dev/specs/altair/light-client/p2p-interface.md#the-gossip-domain-gossipsub).
