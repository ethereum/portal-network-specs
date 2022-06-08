## Status
>  This specification is a work-in-progress and should be considered preliminary.

## Overview
A beacon chain client could sync committee to perform [state updates](https://github.com/ethereum/consensus-specs/blob/dev/specs/altair/sync-protocol.md). The data object [LightClientSkipSyncUpdate](skip-sync-network) allows a client to quickly sync to a recent header with the appropriate sync committee. Once the client establishes a recent header, it could sync to other headers by processing [LightClientUpdates](https://github.com/ethereum/consensus-specs/blob/dev/specs/altair/sync-protocol.md#lightclientupdate). These two data types allow a client to stay up-to-date with the beacon chain.

These two data types are placed into separate sub-networks. A light client make find-content requests on `skip-sync-network` at start of the sync to get a header with the same `SyncCommittee` object as in the current sync period. The client uses messages in the gossip topic `bc-light-client-update` to advance its header.

The gossip topics described in this document is part of a [proposal](https://ethresear.ch/t/a-beacon-chain-light-client-proposal/11064) for a beacon chain light client.


## Gossip Network
A gossip network allows participants to receive regular updates on a particular data type. The key point of differentiation between a portal network gossip channel and a regular gossip channel, e.g. the gossip topic `beacon_block` used by regular beacon chain clients, is that a portal network participant could choose an <em>interest radius</em> `r`. A participants only process messages that are within its chosen radius boundary.

The gossip network shares all the basic structures as other gossip networks, e.g. the [transaction gossip](../transaction-gossip.md).

- Each gossip participant has a `node_id`. A `node_id` is a 256 bit unsigned integer, i.e. `0 <= node_id < 2**256`.
- Each message has a `content_id`. A `content_id` is a 256 bit unsigned integer.
- There is a distance function. It measures the distance between two `node_id`. It also measures the distance between `node_id` and `content_id`.
    ```python
    def distance(node_id: int, content_id: int) -> int:
        """See TODOs"""
        pass
    ```

## Wire Protocol
The [portal wire protocol](../portal-wire-protocol.md) specifies the generic wire formats of each of message type: PING, PONG, FINDNODES, FOUNDNODES, OFFER, and ACCEPT. For a subprotocol, we need to further define the following to be able to instantiate a type's byte contents.
1. `subprotocol id`
1. `content_key`
1. `content_id` 
1. `payload`

The following helper functions are defined in [ssz spec](https://github.com/ethereum/consensus-specs/blob/dev/ssz/). A SszObject is an object that is a valid [ssz typing](https://github.com/ethereum/consensus-specs/blob/dev/ssz/simple-serialize.md#typing).
```python
def serialize(typ: SszType, obj: SszObject) -> bytes
def hash_tree_root(typ: SszType, obj: SszObject) -> bytes
```

See [serialization](https://github.com/ethereum/consensus-specs/blob/dev/ssz/simple-serialize.md#serialization) and [merkleiation]((https://github.com/ethereum/consensus-specs/blob/dev/ssz/simple-serialize.md#merkleization)) for more details.

The subprotocol id is: `0x502A`.

The content of the message is the [update container](https://github.com/ethereum/consensus-specs/blob/dev/specs/altair/sync-protocol.md#lightclientupdate).
```python
class LightClientUpdate(Container):
    # Update beacon block header
    header: BeaconBlockHeader
    # Next sync committee corresponding to the header
    next_sync_committee: SyncCommittee
    next_sync_committee_branch: Vector[Bytes32, floorlog2(NEXT_SYNC_COMMITTEE_INDEX)]
    # Finality proof for the update header
    finality_header: BeaconBlockHeader
    finality_branch: Vector[Bytes32, floorlog2(FINALIZED_ROOT_INDEX)]
    # Sync committee aggregate signature
    sync_committee_bits: Bitvector[SYNC_COMMITTEE_SIZE]
    sync_committee_signature: BLSSignature
    # Fork version for the aggregate signature
    fork_version: Version
```

Finally, we define the necessary encodings.
```python
content_key = hash_tree_root(LightClientUpdate, light_client_update)
content_id = content_key
payload = serialize(LightClientUpdate, light_client_update)
```

## TODOs
- It makes sense that there should a single distance function that works for all portal network subnetworks. The proposed [distance function](https://github.com/ethereum/portal-network-specs/blob/master/state-network.md#distance-function) is defined to be the distance in a ring might not [work well](https://github.com/ethereum/portal-network-specs/issues/90) for a Kademlia DHT.

- Define the routing table algorithm. If the distance measure is XOR, the routing table should be maintained as Kademlia routing table. Otherwise, define how the routing table is maintained.

- Define the gossip algorithm. The portal network gossip channel uses radius `r` as an additional control to how messages are propagated. A node uses `r` to determine which messages to forward to which peers. See discussions in this [issue](https://github.com/ethereum/portal-network-specs/issues/89). Transaction-gossip is attempting to define an [algorithm](transaction-gossip.md#gossip-algorithm). There should be a generic gossip algorithm that works for all portal network gossip channels.
