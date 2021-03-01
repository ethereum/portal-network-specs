# State Availability Network

This document is intended to serve as a preliminary specification for the networking protocols needed to support on-demand availability of the Ethereum "State".

## Definition of "State"

We define the Ethereum "State" to be the collection of:

- Accounts from the main account trie referenced by `Header.state_root`
- The set of all contract storage tries referenced by `Account.state_root`
- The set of all contract bytecodes referenced by `Account.code_hash`

## Overview

The network(s) that support "on-demand" availability of the Ethereum state must do the following things.

- Retrieval:
    - A: Mechanism for finding and retrieving "state" data.
- Storage:
    - B: Mechanism for *new* state data to be distributed to *interested* nodes in a provable manner.
    - C: Mechanism for *new* nodes joining the network to discover existing state data that is *interesting* to them.
    - D: Mechanism for *missing* state data to be distributed to *interested* nodes
    
    
We solve A with a standard Kademlia DHT.

We solve B with a gossip network and merkle proofs.

C & D are unsolved, though the POKE concept may be adequate to solve both.
    
    
## Gossip Network

> The exacp semantics of this network are only loosely defined. More research is needed to establish a more concrete specification.

The gossip network is designed to facilitate ingress of new state data into the network.  Nodes in this network establish long lived connections with other peers.  Nodes advertise available hashes to connected peers, and serve proofs for those hashes upon request.

Nodes in this network should not be required to process the full proof for every block. This requirement is in place to ensure that nodes are able to limit total resource requirements.

### Topology

> This is an area of active research.  There is still work to be done to validate whether this `radius` based network topology is appropriate.

The leading idea for this network is to have each node publish their `radius` and to have nodes prioritize connections with other nodes with intersecting areas of interest.  This could also be modeled as nodes maintaining connections loosely based on the same routing table rules used for the DHT, with a higher number of connections allocated towards *nearby* nodes and fewer connections to *far-away* nodes.

The resulting topology is one that can reliably gossip data to all interested nodes once the data reaches at least one node that is *close enough* as well as a few connections allowing data to be pushed to further away parts of the network. Within a specific region of the network data will spread between nodes until it saturates that region, dying out once the data spreads far enough away from it's center that nodes are no longer *interested*.

In order to get data into the appropriate region, we need a more targeted approach.  This mechanism is referred to as `POKE`.  The exact semantics of this are only loosely defined, but a node wishing to push data to a region of the network would lookup some number of nodes in that region, establish a connection with them, and push some number of proofs.  This *could* use the same transport messages as the generic gossip messages but research is needed to determine if this will be reliable enough.


### Transport

The lasted research suggests we need a network with long lived connections that allow streaming larger data payloads than are possible with single UDP packets.  This could be accomplished using libp2p or an implementation of [uTP](https://www.bittorrent.org/beps/bep_0029.html) over DiscV5.

### Messages

The network uses the following message triple for transmission of proof data.

#### AdvertiseProofs

A message containing a list of identifiers, probably `content_ids` that the node has proofs available for.

#### RetrieveProofs

A message requesting one of the proofs advertised via an `AdvertiseProofs` message.

#### Proofs

The response message containing the proofs requested by a `RetrieveProofs` message.


## DHT Network

Our DHT will be an overlay network on the existing [Discovery V5](https://github.com/ethereum/devp2p/blob/master/discv5/discv5.md) network.

We use the same distance function as the core protocol.

We use the same routing table structure as the core protocol.

We use the same PING/PONG/FINDNODES/NODES messaging rules as the core protocol.

### Content

All content on the network has a key and a value.  The keys are referred to as `content_key`.  The value is referred to using the variable `content`. Each piece of content has a `content_id` which is derived from the `content_key` as `hash(content_key)`.

> TODO: define `hash` function (probably sha256)

The data stored in the network is referred to as "content".  The network houses three different types of content.

- Account trie data
- Contract storage trie data
- Contract bytecode

#### Account Trie Data

```
content_key  := content_type | trie_path | node_hash
content_type := 0x01
trie_path    := nibbles + terminator (TODO)
node_hash    := hash(content)
```

#### Contract Storage Trie Data

```
content_key  := content_type | trie_path | node_hash
content_type := 0x02
trie_path    := nibbles + terminator (TODO)
node_hash    := hash(content)
```


#### Contract Bytecode

```
content_key  := content_type | code_hash
content_type := 0x03
code_hash    := keccak(content)
```

### Radius

Nodes on the network broadcast a `radius` value which is used to advertise how much of the overall trie data a node stores.  `radius` is a 256 bit integer.  We define `MAX_RADIUS = 2**256 - 1`

A node is expected to be *interested* in a piece of content if `distance(node_id, content_id) <= radius`.

Nodes are expected to track the radius of other nodes on the network.


### Wire Protocol

All messages in the protocol are transmitted using the `TALKREQ` and `TALKRESP` messages from the base protocol.

All messages have a `message_id` and `encoded_message` that are concatenated to form the `payload` for either a `TALKREQ` or `TALKRESP` message.

```
payload         := message_id | encoded_message
message_id      := uint8
encoded_message := bytes
```

The `encoded_payload` component is the SSZ encoded payload for the message type as indicated by the `message_id`.  Each message has its own `sedes` which dictates how it should be encoded and decoded.

The SSZ sedes `byte_list` is used to alias `List[uint8, max_length=2048]`.

All messages have a `type` which is either `request` or `response`.

* `request` messages **MUST** be sent using a `TALKREQ`
* `response` messages **MUST** be sent using a `TALKRESP`


#### Ping (0x01)

Request message to check if a node is reachable, communicate basic information about our node, and request basic information about the other node.


```
message_id := 1
type       := request
sedes      := Container(enr_seq: uint32, data_radius: uint256)
```

* `enr_seq`: The node's current sequence number of their ENR record
* `data_radius`: The nodes current maximum radius for data stored by this node.


#### Pong (0x02)

Response message to Ping(0x01)

```
message_id := 2
type       := response
sedes      := Container(enr_seq: uint32, data_radius: uint256)
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

* `total`: The total number of ENR records being returned.
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
    
> A response with an empty `payload` and empty `enrs` indicates that the node odes is not aware of any closer nodes, *nor* does the node have the requested content.
