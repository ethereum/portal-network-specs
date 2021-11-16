## Status
>  This specification is a work-in-progress and should be considered preliminary.


## DHT Overview
A client uses `SkipSyncUpdate` to skip sync from a known header to a recent header. A client with a trusted but outdated header cannot use the messages in the gossip channel `bc-light-client-update` to update. The client's sync-committee in the stored snapshot is too old and not connected to any update messages. The client look for the appropriate `SkipSyncUpdate` to skip sync its header.

The subprotocol id is: `0x501A`.


## Wire Protocol
The wire protocol](../portal-wire-protocol.md) specifies the generic wire formats of each of message type: PING, PONG, FINDNODES, FOUNDNODES, OFFER, ACCEPT, FINDCONTENT, and CONTENT. Defining the following functions allow the client to construct the wire formats of the message type `SkipSyncUpdate`.

1. `content_key`
1. `content_id` 
1. `payload`


```python
class SkipSyncUpdate(Container):
    # Update beacon block header
    header: BeaconBlockHeader
    # Next sync committee corresponding to the header
    next_sync_committee: SyncCommittee
    next_sync_committee_branch: Vector[Bytes32, floorlog2(NEXT_SYNC_COMMITTEE_INDEX)]
    # Finality proof for the update header
    finality_header: BeaconBlockHeader
    finality_branch: Vector[Bytes32, floorlog2(FINALIZED_ROOT_INDEX)]
    # Sync committee aggregate signature
    sync_committee: SyncCommittee
    sync_committee_bits: Bitvector[SYNC_COMMITTEE_SIZE]
    sync_committee_signature: BLSSignature
    # Fork version for the aggregate signature
    fork_version: Version

class SkipSyncUpdateKey(Container):
    sync_committee: SyncCommittee

def get_content_key(epoch: Epoch, sync_committee SyncCommittee) -> bytes:
    key = SkipSyncUpdateKey()
    key.sync_committee = sync_committee

    return hash_tree_root(SkipSyncUpdateKey, key)

content_key = get_content_key(epoch, sync_committee)
content_id = hash_tree_root(SkipSyncUpdateKey, skip_sync_update_key)
payload = serialize(SkipSyncUpdate, skip_sync_update)
```

## Notes
- A node maintains a database of historical `SkipSyncUpdate`. It keeps one update per sync period. These updates are keyed by the `skip_sync_update_key`, effectively by the hash of sync-committee.
- The rule for picking the update within a sync period is as followed:
    1. The finalized update with the highest participation
    2. The update with highest participation
    3. Prefer the most recent update
- Clients do not need to retrieve the exact same `skip_sync_update` while making requests with the same `skip_sync_update_key`. They only need to receive a valid `skip_sync_update` that allows them to advance their head to the next sync committee.
- `SkipSyncUpdate` is different from `LightClientUpdate` in that `sync_committee` is present in the skip sync update message. This inclusion allows portal network nodes to validate the message without any external dependencies. The original data lookup requester has the sync-committee, but network nodes are not required to keep the database of historical `SkipSyncUpdate`. If a portal network node does not validate `SkipSyncUpdate` messages before propagating, the DHT could be easily polluted with key-value pair (`skip_sync_update_key`, `skip_sync_update`) that are not internally consistent. Even a small number of bad messages could amplify to be the dominant answers of a data lookup if those bad messages were the first messages to enter the DHT.
