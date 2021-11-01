## DHT Overview
A client has a trusted beacon state root, and it wants to access some parts of the state. Each of the access request corresponds to some leave nodes of the beacon state. The request is a content lookup on a DHT. The response is a Merkle proof. 

A Distributed Hash Table (DHT) allows network participants to have retrieve data on-demand based on a content key. A portal-network DHT is different than a traditional one in that each participant could selectively limit its workload by choosing a small <em>interest radius</em> `r`. A participants only process messages that are within its chosen radius boundary.

The beacon state DHT shares all the basic structures as other DHT networks, e.g. the [state network](state-network.md). A DHT uses the message types PING, PONG, FINDNODES, NODES, FINDCONTENT, and CONTENT. The message encodings are specified in the [portal wire protocol](../portal-wire-protocol.md).

This DHT is part of a [proposal](https://ethresear.ch/t/a-beacon-chain-light-client-proposal/11064) for a beacon chain light client.

The subprotocol id is: `0x501C`.


## Wire Protocol
For a subprotocol, we need to further define the following to be able to instantiate the wire format of each message type.
1. `content_key`
1. `content_id` 
1. `payload`

The content of the message is a Merkle proof contains multiple leave nodes for a [BeaconState](https://github.com/ethereum/consensus-specs/blob/dev/specs/altair/beacon-chain.md#beaconstate).

```python
class BeaconState(Container):
    """
    See: https://github.com/ethereum/consensus-specs/blob/dev/specs/altair/beacon-chain.md#beaconstate
    """
    pass

# Used to limit the size of the message. This could be modified to be higher if needed.
LEAVE_ITEM_LIMIT = 128

# The maximum number of proof nodes needed to complete a merkle proof
# Note that max_chuck_count() is recursively apply chunk_count() on all possible paths of the BeaconState.
HELPER_INDICES_LIMIT = LEAVE_ITEM_LIMIT * log(max_chuck_count(BeaconState))  

class BeaconStateProof(Container):
    """
    See: https://github.com/ethereum/consensus-specs/blob/dev/ssz/merkle-proofs.md#merkle-multiproofs
    """
    root: Bytes323
    leave_indices: List[unit64, LEAVE_ITEM_LIMIT]  # GeneralizedIndex is represented by unit64
    leaves: List[Bytes32, LEAVE_ITEM_LIMIT]
    proof_nodes: List[Bytes32, HELPER_INDICES_LIMIT]
```

Finally, we define the necessary encodings. A light client only knows the root of the beacon state. The client wants to know the details of some leave nodes. The client has to be able to construct the `content_key` only knowing the root and which leave nodes it wants see. The `content_key` is the ssz serialization of the paths. The paths represent the part of the beacon state that one wants to know about. The paths are represented by generalized indices. Note that `hash_tree_root` and `serialize` are the same as those defined in [sync-gossip](sync-gossip.md). 

```python
class BeaconStateProofKey(Container):
    root: Bytes323
    leave_indices: List[unit64, LEAVE_ITEM_LIMIT]  # GeneralizedIndex is represented by unit64


def get_generalized_index(typ: SSZType, path: Sequence[Union[int, SSZVariableName]]) -> GeneralizedIndex:
    """
    Converts a path (eg. `[7, "foo", 3]` for `x[7].foo[3]`, `[12, "bar", "__len__"]` for
    `len(x[12].bar)`) into the generalized index representing its position in the Merkle tree.

    See: https://github.com/ethereum/consensus-specs/blob/dev/ssz/merkle-proofs.md#ssz-object-to-index
    """
    pass


def get_content_key(root: Bytes323, paths: Sequence[Sequence[[Union[int, SSZVariableName]]]) -> bytes:
    indices = [get_generalized_index(BeaconSate, path) for path in paths]
    proof_key = BeaconStateProofKey()
    proof_key.root = root
    proof_key.leave_indices = indices
    return serialize(BeaconStateProofKey, proof_key)


content_key = get_content_key(root, paths)
content_id = hash_tree_root(BeaconStateProof, beacon_state_proof)
payload = serialize(BeaconStateProof, beacon_state_proof)
```


## TODOs
- Determine if the message type `BeaconStateProof` needs to be gossiped as well.
- The DHT algorithm for `FINDCONTENT` might not reach large radius node, and hence it would fail to find some available contents. See the [discussion](https://github.com/ethereum/portal-network-specs/issues/91)

