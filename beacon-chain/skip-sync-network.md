## Status
>  This specification is a work-in-progress and should be considered preliminary.


## DHT Overview
A client uses `LightClientSkipSyncUpdate` to skip sync from a known header to a recent header. A client with a trusted but outdated header cannot use the messages in the gossip channel `bc-light-client-update` to update. The client's sync-committee in the stored snapshot is too old and not connected to any update messages. The client look for the appropriate `LightClientSkipSyncUpdate` to skip sync its header.

The subprotocol id is: `0x501A`.


## Wire Protocol
The wire protocol](../portal-wire-protocol.md) specifies the generic wire formats of each of message type: PING, PONG, FINDNODES, FOUNDNODES, OFFER, ACCEPT, FINDCONTENT, and CONTENT. Defining the following functions allow the client to construct the wire formats of the message type `LightClientSkipSyncUpdate`.

1. `content_key`
1. `content_id` 
1. `payload`


```python
class LightClientSkipSyncUpdate(Container):
    # Update beacon block header
    header: BeaconBlockHeader
    # Current sync committee corresponding to the header
    current_sync_committee: SyncCommittee
    current_sync_committee_branch: Vector[Bytes32, floorlog2(NEXT_SYNC_COMMITTEE_INDEX)]
    # Next sync committee corresponding to the header
    next_sync_committee: SyncCommittee
    next_sync_committee_branch: Vector[Bytes32, floorlog2(NEXT_SYNC_COMMITTEE_INDEX)]
    # Sync committee aggregate signature
    sync_committee_bits: Bitvector[SYNC_COMMITTEE_SIZE]
    sync_committee_signature: BLSSignature
    # Fork version for the aggregate signature
    fork_version: Version

class SkipSyncUpdateKey(Container):
    epoch: Epoch
    next_sync_committee: SyncCommittee
    fork_version: Version

def get_content_key(epoch: Epoch, next_sync_committee SyncCommittee, fork_version Version) -> bytes:
    indices = [get_generalized_index(BeaconSate, path) for path in paths]
    key = SkipSyncUpdateKey()
    key.epoch = epoch
    key.next_sync_committee = next_sync_committee
    key.fork_version = fork_version

    return serialize(SkipSyncUpdateKey, key)

content_key = get_content_key(epoch, current_sync_committee, next_sync_committee)
content_id = hash_tree_root(SkipSyncUpdateKey, skip_sync_update_key)
payload = serialize(LightClientSkipSyncUpdate, LightClientSkipSyncUpdate)
```

