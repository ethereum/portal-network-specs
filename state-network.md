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
    
    
We solve A with a standard Kademlia DHT using the "recursive find" algorithm.

We solve B with a gossip network and merkle proofs.

We ignore C because it can be handled via a combination of POKE and the solution for D

We solve D without any modification to the protocol, by simply having a daemon that searches for missing state and injects it into the network using standard gossip mechanics


## DHT Network

Our DHT will be an overlay network on the existing [Discovery V5](https://github.com/ethereum/devp2p/blob/master/discv5/discv5.md) network.

The identifier `0xTODO` will be used as the `protocol_id` for TALKREQ and TALKRESP messages.

Nodes **must** support the `utp` Discovery v5 protocol.

We use the same distance function as the core protocol.

We use the same routing table structure as the core protocol.

We use the same PING/PONG/FINDNODES/NODES messaging rules as the core protocol.

### Content

All content on the network has a key and a value.  The keys are referred to as `content_key`.  The value is referred to using the variable `content`. Each piece of content has a `content_id` which is derived from the `content_key` as `hash(content_key)`.

> TODO: define `hash` function (probably sha256)

> TODO: define serialization for content keys

The data stored in the network is referred to as "content".  The network houses three different types of content.

- Account trie data
- Contract storage trie data
- Contract bytecode

> TODO: encoding scheme for trie paths that accounts for nibbles: https://github.com/ethereum/py-trie/blob/6da013af84f5448b30abe81a6e7ada07400b7a55/trie/utils/nibbles.py


#### Account Trie Data

```
content_key  := network_id | content_type | trie_path | node_hash
network_id   := uint16
content_type := 0x01
trie_path    := nibbles (TODO)
node_hash    := hash(content)
```

The SSZ sedes used for encoding/decoding

```
Container(network_id: uint16, content_type: uint8, trie_path: byte_list, node_hash: bytes32)
```


#### Contract Storage Trie Data

```
content_key  := network_id | content_type | address | trie_path | node_hash
network_id   := uint16
content_type := 0x02
address      := bytes20
trie_path    := nibbles (TODO)
node_hash    := hash(content)
```

The SSZ sedes used for encoding/decoding

```
Container(network_id: uint16, content_type: uint8, address: bytes20, trie_path: byte_list, node_hash: bytes32)
```


#### Contract Bytecode

```
content_key  := network_id | content_type | address | code_hash
network_id   := uint16
content_type := 0x03
address      := bytes20
code_hash    := keccak(content)
```

The SSZ sedes used for encoding/decoding

```
Container(network_id: uint16, content_type: uint8, address: bytes20, code_hash: bytes32)
```

### Radius

Nodes on the network broadcast a `radius` value which is used to advertise how much of the overall trie data a node stores.  `radius` is a 256 bit integer.  We define `MAX_RADIUS = 2**256 - 1`

A node is expected to be *interested* in a piece of content if `distance(node_id, content_id) <= radius`.

Nodes are expected to track the radius of other nodes on the network.


### Gossip

Nodes in the network should use the following rules for gossip.

TODO: outline the process of receiving a proof and: 1) extracting the parent proofs, and re-advertising them to the nodes in the network they expect to be interested in them as well as 2) relaying the base proof to neighbor nodes that should be interested.

### POKE

The standard process of looking up content is a depth first traversal of the trie towards the desired path, iteratively building a "proof".

At each stage, a node is likely to encounter nodes who are "interested" in the content, but who did not have it.

Once the content has been required, nodes are encouraged to POKE the assembled proof back to these nodes.  This would use the same gossip mechanisms.

This POKE mechanic actively spreads propular content through the network.


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
    
> A response with an empty `payload` and empty `enrs` indicates that the node is not aware of any closer nodes, *nor* does the node have the requested content.


#### Advertise (0x07)

Advertise a set of content keys that this node has proofs available for.

```
message_id := 7
type       := request
sedes      := List[byte_list, max_length=32]
```

The payload of this message is a list of encoded `content_key` entries.


#### RequestProofs (0x08)

Response message to Advertise (0x07).

Request the proofs for a piece of content.

> Despite the name of this message having the name "Request" in it, this is a response message.

```
message_id := 8
type       := response
sedes      := Container(connection_id: bytes4, content_keys: List[byte_list, max_length=32]]
```

* `connection_id`: ConnectionID to be used for a uTP stream
    * ConnectionID values should be randomly generated.
* `content_keys`: The set of encoded content keys that should be sent.
    * Only content keys from the corresponding Advertise message are valid.

Upon *sending* this message, the requesting node should *listen* for an incoming uTP stream with the generated `connection_id`.

Upon *receiving* this message, the serving node should initiate a uTP stream.

Proofs sent across the stream should be framed with a 4-byte length prefix.

```
message_frame := length_prefix | message
length_prefix := bytes4
message       := encode(proof)
proof         := TBD
```

> The exact semantics of how we encode proofs are under active development and subject to major changes.

We encode proofs as a stream of `(path, node)` pairs which have been sorted in preorder traversal ordering.  We can save some bytes by de-duplicating the `path` components since each path will tend to have a common prefix with the previous path.

We also validate that proofs are "minimal", only containing the minimal set of trie nodes necessary for the proven piece of data.
