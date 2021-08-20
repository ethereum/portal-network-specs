# State Availability Network

This document is intended to serve as a preliminary specification for the networking protocols needed to support on-demand availability of the Ethereum "State".

## Definition of "State"

We define the Ethereum "State" to be the collection of:

- Accounts and intermediate trie data from the main account trie referenced by `Header.state_root`
- The set of all contract storage values and intermediate trie data referenced by `Account.state_root`
- The set of all contract bytecodes referenced by `Account.code_hash`

## Overview

The network(s) that support "on-demand" availability of the Ethereum state must do the following things.

- Retrieval:
    - A: Mechanism for finding and retrieving recent "state" data.  This must also include proof of exclusion for non-existent data.
- Storage:
    - B: Mechanism for state data to be distributed to *interested* nodes in a provable manner.
    
    
We solve A by mapping "state" data onto the Kademlia DHT such that nodes can determine the location in the network where a particular piece of state should be stored.  With a standard Kademlia DHT using the "recursive find" algorithm any node in the network can quickly find nodes that should be storing the data they are interested in.

We solve B with a structured gossip algorithm that distributes the individual trie node data across the nodes in the DHT.  As the chain progresses, a witness of the new and updated state data will be generated at each new `Header.state_root`.  The individual trie nodes from this witness would then be distributed to the appropriate DHT nodes.


## DHT Network

Our DHT will be an overlay network on the existing [Discovery V5](https://github.com/ethereum/devp2p/blob/master/discv5/discv5.md) network.

The identifier `0xTODO` will be used as the `protocol_id` for TALKREQ and TALKRESP messages.

Nodes **must** support the `utp` Discovery v5 protocol to facilitate transmission of merkle proofs which will in most cases exceed the UDP packet size.

We use a custom distance function defined below.

We use the same routing table structure as the core protocol.  The routing table must use the custom distance function defined below.

We use the same PING/PONG/FINDNODES/NODES messaging rules as the core protocol.

### Content Keys and Content IDs

The network supports the following schemes for addressing different types of content.

All content keys are the concatenation of a 1-byte `content_type` and a serialized SSZ `Container` object.  The `content_type` indicate which type of content key the payload represents.  The SSZ `Container` sedes defines how the payload can be decoded.

We define a custom SSZ sedes alias `Nibbles` to mean `List[uint8, max_length=64]` where each individual value **must** be constrained to a valid "nibbles" value of `0 - 15`.

#### Account Trie Nodes

> TODO: consult on best way to define trie paths
```
0x00 | Container(path: Nibbles, node_hash: bytes32, state_root: bytes32)

content_id := sha256(path | node_hash)

```

#### Contract Storage Trie Nodes

```
0x01 | Container(address: bytes20, path: Nibbles, node_hash: bytes32, state_root: bytes32)

content_id := sha256(address | path | node_hash)
```


#### Account Trie Leaves

```
0x02 | Container(address: bytes20, state_root: bytes32)

content_id := keccak(address)
```


#### Contract Storage Trie Leaves

```
0x03 | Container(address: bytes20, slot: uint256, state_root: bytes32)

content_id := (keccak(address) + keccak(slot)) % 2**256
```

#### Contract Bytecode

```
0x04 | Container(address: bytes20, code_hash: bytes32)

content_id := sha256(address | code_hash)
```


### Distance Function

The overlay DHT uses the following distance function for determining both:

* The distance between two DHT nodes in the network.
* The distance between a DHT node and a piece of content.

```python
MODULO = 2**256
MID = 2**255

def distance(node_id: int, content_id: int) -> int:
    """
    Source: https://stackoverflow.com/questions/28036652/finding-the-shortest-distance-between-two-angles
    
    A distance function for determining proximity between a node and content.
    
    Treats the keyspace as if it wraps around on both ends and 
    returns the minimum distance needed to traverse between two 
    different keys.
    
    Examples:

    >>> assert distance(10, 10) == 0
    >>> assert distance(5, 2**256 - 1) == 6
    >>> assert distance(2**256 - 1, 6) == 7
    >>> assert distance(5, 1) == 4
    >>> assert distance(1, 5) == 4
    >>> assert distance(0, 2**255) == 2**255
    >>> assert distance(0, 2**255 + 1) == 2**255 - 1
    """
    delta = (node_id - content_id + MID) % MODULO - MID
    if delta  < -MID:
        return abs(delta + MID)
    else:
        return abs(delta)

```

This distance function is designed to preserve locality of leaf data within main account trie and the individual contract storage tries.  The term "locality" in this context means that two trie nodes which are adjacent to each other in the trie will also be adjacent to each other in the DHT.


#### Radius

Nodes on the network will be responsible for tracking and publishing a `radius` value to their peers.  This value serves as both a signal about what data a node should be interested in storing, as well as what data a node can be expected to have.  The `radius` is a 256 bit integer.  We define `MAX_RADIUS = 2**256 - 1`

A node is said to be *"interested"* in a piece of content if `distance(node_id, content_id) <= radius`.  Nodes are expected to store content they are "interested" in.


### Wire Protocol

All messages in the protocol are transmitted using the `TALKREQ` and `TALKRESP` messages from the base protocol.

All messages have a `message_id` and `encoded_message` that are concatenated to form the `payload` for either a `TALKREQ` or `TALKRESP` message.

```
payload         := message_id | encoded_message
message_id      := uint8
encoded_message := bytes
```

The `encoded_message` component is the SSZ encoded payload for the message type as indicated by the `message_id`.  Each message has its own `sedes` which dictates how it should be encoded and decoded.

The SSZ sedes `byte_list` is used to alias `List[uint8, max_length=2048]`.

All messages have a `type` which is either `request` or `response`.

* `request` messages **MUST** be sent using a `TALKREQ`
* `response` messages **MUST** be sent using a `TALKRESP`


#### Ping (0x01)

Request message to check if a node is reachable, communicate basic information about our node, and request basic information about the other node.


```
message_id := 1
type       := request
sedes      := Container(enr_seq: uint64, data_radius: uint256)
```

* `enr_seq`: The node's current sequence number of their ENR record
* `data_radius`: The nodes current maximum radius for data stored by this node.


#### Pong (0x02)

Response message to Ping(0x01)

```
message_id := 2
type       := response
sedes      := Container(enr_seq: uint64, data_radius: uint256)
```

* `enr_seq`: The node's current sequence number of their ENR record
* `data_radius`: The nodes current maximum radius for data stored by this node.

#### Find Nodes (0x03)

Request nodes from the peer's routing table at the given logarithmic distances.  The distance of `0` indicates a request for the peer's own ENR record.

```
message_id := 3
type       := request
sedes      := Container(distances: List[uint16, max_length=256])
```

* `distances` is a list of distances for which the node is requesting ENR records for.
    * Each distance **MUST** be within the inclusive range `[0, 256]`
    * Each distance in the list **MUST** be unique.

#### Nodes (0x04)

Response message to FindNodes(0x03).

```
message_id := 4
type       := response
sedes      := Container(total: uint8, enrs: List[byte_list, max_length=32])
```

* `total`: The total number of `Nodes` response messages being sent.
* `enrs`: List of bytestrings, each of which is an RLP encoded ENR record.
    * Individual ENR records **MUST** correspond to one of the requested distances.
    * It is invalid to return multiple ENR records for the same `node_id`.

> Note: If the number of ENR records cannot be encoded into a single message, then they should be sent back using multiple messages, with the `total` field representing the total number of messages that are being sent.

#### Find Content (0x05)

Request either the data payload for a specific piece of content on the network, **or** ENR records of nodes that are closer to the requested content.

```
message_id := 5
type       := request
sedes      := Container(content_key: byte_list)
```

* `content_key` the pre-image key for the content being requested..


#### Found Content (0x06)

Response message to Find Content (0x05).

This message can contain **either** the data payload for the requested content *or* a list of ENR records that are closer to the content than the responding node.

```
message_id := 6
type       := response
sedes      := Container(enrs: List[byte_list, max_length=32], payload: byte_list)
```

* `enrs`: List of bytestrings, each of which is an RLP encoded ENR record.
    * Individual ENR records **MUST** be closer to the requested content than the responding node.
    * It is invalid to return multiple ENR records for the same `node_id`.
    * This field **must** be empty if `payload` is non-empty.
* `payload`: bytestring of the requested content.
    * This field **must** be empty if `enrs` is non-empty.
    
> A response with an empty `payload` and empty `enrs` indicates that the node is not aware of any closer nodes, *nor* does the node have the requested content.


#### Offer (0x07)

Offer a set of content keys that this node has proofs available for.

```
message_id := 7
type       := request
sedes      := List[byte_list, max_length=64]
```

The payload of this message is a list of encoded `content_key` entries.


#### Accept (0x08)

Response message to Offer (0x07).

Signals interest in receiving the offered data fro the corresponding Offer message.


```
message_id := 8
type       := response
sedes      := Container(connection_id: bytes4, content_keys: BitList[max_length=64]]
```

* `connection_id`: ConnectionID to be used for a uTP stream
    * ConnectionID values should be randomly generated.
* `content_keys`: Signals which content keys are desired
    * A bit-list corresponding to the offered keys with the bits in the positions of the desired keys set to `1`.

Upon *sending* this message, the requesting node should *listen* for an incoming uTP stream with the generated `connection_id`.

Upon *receiving* this message, the serving node should initiate a uTP stream.

> TODO: how does message framing across the stream work for individual messages.


### Gossip

The state network uses "structured" gossip to push new state data into the storage of individual DHT nodes.  We refer to the concept of a "bridge" node in the network to mean a node which is acting benevolently to bring new and updated state data into the network.

* At each block we define our witness to be:
    * The set of all accounts that were created or modified
    * The set of all contract storage slots that were created or modified
    * The set of all contract bytecodes that were created.
* A traditional "full" node with a fully synced state database will typically be used to construct this witness.
* The witness is then deconstructed into its individual trie nodes and their corresponding sub-proofs to anchor them in a provable manner to the `Header.state_root`
* For each individual trie node and its corresponding proof the bridge node will compute the corresponding `content_id`, seek out DHT nodes who's area of interest contains this `content_id`, and will offer those DHT nodes the data.

> TODO: 1: efficiency thing where bridge is only reasponsible for leaf data and nodes handle recursive sub-proof gossip.

> TODO: 2: bridge nodes need to do gossip for contract storage leaves.

> TODO: 3: bridge nodes need to do gossip for contract bytecodes

- bridge does *all* GetNodeData style gossip.
    - this could be reduced by only gossiping nodes from the edge of the proof, and delegating intermediate node gossip.
- bridge does all contract leaf gossip.
    - this *could* be done by the nodes that receive the contract storage leaves as GetNodeData style data.
- bridge does contract bytecodes gossip.



### POKE

> TODO: Discribe this mechanism


