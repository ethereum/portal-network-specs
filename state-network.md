# Portal Network: State Network

This document is the specification for the "State" portion of the portal network.

## Definition of "State"

We define the Ethereum "State" to be the collection of:

- The set of all accounts from the main account trie referenced by `Header.state_root`
- The set of all contract storage values from all contracts
- The set of all contract bytecodes
- Any information required to prove inclusion of the above data in the state.

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

The identifier `portal-state` will be used as the `protocol_id` for TALKREQ and TALKRESP messages from the base discovery v5 protocol.

Nodes **must** support the `utp` Discovery v5 sub-protocol to facilitate transmission of merkle proofs which will in most cases exceed the UDP packet size.

We use a custom distance function defined below.

We use the same routing table structure as the core protocol.  The routing table must use the custom distance function defined below.

A separate instance of the routing table must be maintained for the state network, independent of the base routing table managed by the base discovery v5 protocol, only containing nodes that support the `portal-state` sub-protocol.  We refer to this as the *"overlay routing table"*.

We use custom PING/PONG/FINDNODES/NODES messages which are transmitted over the TALKREQ/TALKRESP messages from the base discovery v5 protocol.

We use the same PING/PONG/FINDNODES/NODES rules from base discovery v5 protocol for management of the overlay routing table.

### Content Keys and Content IDs

Content keys are used to request a specific package of data from a peer. Content IDs are used to identify the location in the network where the content is located.

The network supports the following schemes for addressing different types of content.

All content keys are the concatenation of a 1-byte `content_type` and a serialized SSZ `Container` object.  The `content_type` indicate which type of content key the payload represents.  The SSZ `Container` sedes defines how the payload can be decoded.

We define a custom SSZ sedes alias `Nibbles` to mean `List[uint8, max_length=64]` where each individual value **must** be constrained to a valid "nibbles" value of `0 - 15`.

> TODO: we may want to use a more efficient definition for the `Nibbles` encoding.  Current approach incurs 2x overhead.

#### Account Trie Node (0x00)

An individual trie node from the main account trie.

> TODO: consult on best way to define trie paths
```
content_key := 0x00 | Container(path: Nibbles, node_hash: bytes32, state_root: bytes32)

content_id  := sha256(path | node_hash)
node_hash   := bytes32
state_root  := bytes32
path        := TODO
```

#### Contract Storage Trie Node

An individual trie node from a contract storage trie.

```
content_key := 0x01 | Container(address: bytes20, path: Nibbles, node_hash: bytes32, state_root: bytes32)

content_id  := sha256(address | path | node_hash)
address     := bytes20
node_hash   := bytes32
path        := TODO
```


#### Account Trie Proof

A leaf node from the main account trie and accompanying merkle proof against a recent `Header.state_root`

```
content_key := 0x02 | Container(address: bytes20, state_root: bytes32)

content_id  := keccak(address)
address     := bytes20
state_root  := bytes32
```


#### Contract Storage Trie Proof

A leaf node from a contract storage trie and accompanying merkle proof against the `Account.storage_root`.

```
content_key := 0x03 | Container(address: bytes20, slot: uint256, state_root: bytes32)

content_id  := (keccak(address) + keccak(slot)) % 2**256
address     := bytes20
slot        := uint256
state_root  := bytes32
```

#### Contract Bytecode

The bytecode for a specific contract as referenced by `Account.code_hash`

```
content_key := 0x04 | Container(address: bytes20, code_hash: bytes32)
address     := bytes20
code_hash   := bytes32
content_id  := sha256(address | code_hash)
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
    if node_id > content_id:
        diff = node_id - content_id
    else:
        diff = content_id - node_id

    if diff > MID:
        return MODULO - diff
    else:
        return diff

```

This distance function is designed to preserve locality of leaf data within main account trie and the individual contract storage tries.  The term "locality" in this context means that two trie nodes which are adjacent to each other in the trie will also be adjacent to each other in the DHT.


#### Radius

Nodes on the network will be responsible for tracking and publishing a `radius` value to their peers.  This value serves as both a signal about what data a node should be interested in storing, as well as what data a node can be expected to have.  The `radius` is a 256 bit integer.  We define `MAX_RADIUS = 2**256 - 1`

A node is said to be *"interested"* in a piece of content if `distance(node_id, content_id) <= radius`.  Nodes are expected to store content they are "interested" in.


### Wire Protocol

The [Portal wire protocol](./portal-wire-protocol.md) is used as wire protocol for the state network.

The `protocol-id` in the `TALKREQ` message is defined as "portal-state".

The state network supports the following protocol messages:
- `Ping` (0x01) - `Pong` (0x02)
- `Find Nodes` (0x03) - `Nodes` (0x04)
- `Find Content` (0x05) - `Found Content` (0x06)
- `Offer` (0x07) - `Accept` (0x08)

## Gossip

The state network will use a multi stage mechanism to store new and updated state data.

### Overview

The state data is stored in the network in two formats.

- A: Trie nodes
    - Individual leaf and intermediate trie nodes.
    - Gossiped with a proof against a recent state root
    - Optionally stored without a proof not anchored to a specific state root
- B: Leaf proofs
    - Contiguous sections of leaf data
    - Gossiped and stored with a proof against a specific state root
    - Proof is continually updated to latest state root

The state data first enters the network as trie nodes which are then used to populate and update the leaf proofs.

### Terminology

We define the following terms when referring to state data.  

> The diagrams below use a binary trie for visual simplicity. The same
> definitions naturally extend to the hexary patricia trie.


```
0:                           X
                            / \
                          /     \
                        /         \
                      /             \
                    /                 \
                  /                     \
                /                         \
1:             0                           1
             /   \                       /   \
           /       \                   /       \
         /           \               /           \
2:      0             1             0             1
       / \           / \           / \           / \
      /   \         /   \         /   \         /   \
3:   0     1       0     1       0     1       0     1
    / \   / \     / \   / \     / \   / \     / \   / \
4: 0   1 0   1   0   1 0   1   0   1 0   1   0   1 0   1
```


#### *"state root"*
    
The node labeled `X` in the diagram.

#### *"trie node"*

Any of the individual nodes in the trie.

#### *"intermediate node"*

Any of the nodes in the trie which are computed from other nodes in the trie.  The nodes in the diagram at levels 0, 1, 2, and 3 are all intermediate.

#### *"leaf node"*

Any node in the trie that represents a value stored in the trie.  The nodes in the diagram at level 4 are leaf nodes.

#### *"leaf proof"*

The merkle proof which contains a leaf node and the intermediate trie nodes necessary to compute the state root of the trie.

### Neighborhood Gossip

We use the term *neighborhood gossip* to refer to the process through which content is disseminated to all of the DHT nodes *near* the location in the DHT where the content is located.

The process works as follows.

- A DHT node receives a piece of content that they are interested in storing.
- The DHT node checks their routing table for nearby DHT nodes that should also be interested in the content.
- A random subset of the nearby interested nodes is selected and the content is offered to them.

The process above should quickly saturate the area of the DHT where the content is located and naturally terminate as more nodes become aware of the content.

### Stages

The gossip mechanism is divided up into individual stages which are designed to
ensure that each individual piece of data is properly disseminated to the DHT
nodes responsible for storing it, as well as spreading the responsibility as
evenly as possible across the DHT.

The stages are:

- Stage 1:
    - Bridge node generates a proof of all new and updated state data from the most recent block and initiates gossip of the individual trie nodes.
- Stage 2:
    - DHT nodes receiving trie nodes perform *neighborhood gossip* to spread the data to nearby interested DHT nodes.
    - DHT nodes receiving trie nodes extract the trie nodes from the anchor proof to perform *recursive gossip* (defined below).
    - DHT nodes receiving "leaf" nodes initiate gossip of the leaf proofs (for stage 3)
- Stage 3:
    - DHT nodes receiving leaf proofs perform *neighborhood gossip* to spread the data to nearby interested DHT nodes.


```
    +-------------------------+
    | Stage 1: data ingress   |
    +-------------------------+
    |                         |
    | Bridge node initializes |
    | trie node gossip        |
    |                         |
    +-------------------------+
            |
            v
    +---------------------------+
    | Stage 2: trie nodes       |
    +---------------------------+
    |                           |
    | A: neighborhood gossip of |
    |    trie node and proof    |
    |                           |
    | B: initialization of      |
    |    gossip for proof trie  |
    |    nodes.                 |
    |                           |
    | C: initialization of      |
    |    leaf proof gossip      |
    |                           |
    +---------------------------+
            |
            v
    +----------------------------+
    | Stage 3: leaf proofs       |
    +----------------------------+
    |                            |
    | neighborhood gossip of     |
    | leaf proofs                |
    |                            |
    +----------------------------+

```

The phrase "initialization of XXX gossip" refers to finding the DHT nodes that
are responsible for XXX and offering the data to them.


#### Stage 1: Data Ingress


The first stage of gossip is performed by a bridge node. Each time a new block
is added to their view of the chain, a set of merkle proofs which are all
anchored to `Header.state_root` is generated which contains.

- Account trie Data:
    - All of the intermediate and leaf trie nodes from the account trie necessary to prove new and modified accounts.
    - All of the intermediate and leaf trie nodes from the account trie necessary for exclusion proofs for deleted accounts.
- Contract Storage trie data:
    - All of the intermediate and leaf trie nodes from each contract storage trie necessary to prove new and modified storage slots.
    - All of the intermediate and leaf trie nodes from each contract storage trie necessary for exclusion proofs for zero'd storage slots.
- All contract bytecode for newly created contracts

> TODO: Figure out language for defining which trie nodes from this proof the bridge node must initialize gossip.

> TODO: Determine mechanism for contract code.


#### Stage 2A: Neighborhood Trie Node Gossip


When individual trie nodes are gossiped they will be transmitted as both the trie node itself, and the additional proof nodes necessary to prove the trie node against a recent state root.

The receiving DHT node will perform *neighborhood* gossip to nearby nodes from their routing table.


#### Stage 2B: Recursive Trie Node Gossip

When individual trie nodes are gossiped, the receiving node is responsible for initializing gossip for other trie nodes contained in the accompanying proof.

This diagram illustrates the proof for the trie node under the path `0011`.  

```
0:                           X
                            / \
                          /     \
                        /         \
                      /             \
                    /                 \
                  /                     \
                /                         \
1:             0                           1
             /   \
           /       \
         /           \
2:      0             1
       / \
      /   \
3:   0     1
          / \
4:       0  (1)

```

Note that it also includes the intermediate trie nodes under the paths:

- `000`
- `001`
- `00`
- `01`
- `0`
- `1`
- `X`

The gossip payload for the trie node at `0011` will contain these trie nodes as a proof.  Upon receipt of this trie node and proof, the receiving DHT node will extract the proof for the intermediate node under the path `001` which is the direct parent of the main trie node currently being gossiped.  This proof would be visualized as follows:


```
0:                           X
                            / \
                          /     \
                        /         \
                      /             \
                    /                 \
                  /                     \
                /                         \
1:             0                           1
             /   \
           /       \
         /           \
2:      0             1
       / \
      /   \
3:   0    (1)

4:

```

The DHT node would then *initialize* gossip for the trie node under the path `001`, using this new slimmed down proof to anchor to the same state root.  This process continues until it reaches the state root where it naturally terminates.  We refer to this as *recursive trie node* gossip.

#### Stage 2C: Initialization Of Leaf Proof Gossip

When receiving an individual trie node which represents a "leaf" node in the trie, the combined leaf node and proof are equivalent to a *"leaf proof"*.  The DHT node receiving this data in the form of "trie node" data is responsible for *initializing gossip* for the same data as a *"leaf proof"*.

#### Stage 3: Neighborhood *"Leaf Proof"* Gossip

When receiving a *"leaf proof"* over gossip, a DHT node will perform *"neighborhood gossip"* to nearby nodes from their routing table.


### Updating cold Leaf Proofs

Anytime the state root changes for either the main account trie or a contract storage trie, every leaf proof under that root will need to be updated.  The primary gossip mechanism will ensure that leaf data that was added, modified, or removed will receive and updated proof.  However, we need a mechanism for updating the leaf proofs for "cold" data that has not been changed.

Each time a new block is added to the chain, the DHT nodes storing leaf proof data will need to perform a walk of the trie starting at the state root. This walk of the trie will be directed towards the slice of the trie dictated by the set of leaves that the node is storing. As the trie is walked it should be compared to the previous proof from the previous state root. This walk concludes once all of the in-range leaves can be proven with the new state root.


> TODO: reverse diffs and storing only the latest proof.

> TODO: gossiping proof updates to neighbors to reduce duplicate work.


### POKE: Actively disseminating data and replication of popular data

When a DHT node in the network is retrieving some piece of data they will perform a "recursive find" using the FINDCONTENT (0x05) and FOUNDCONTENT (0x06) messages.  During the course of this recursive find, they may encounter nodes along the search path which did not have the content but for which the content does fall within their radius.

When a DHT encounters this situation, and successfully retrieves the content from some other node, they should gossip the content to those nodes that should be interested.  This mechanism is designed to help spread content to nodes that may not yet be aware of it.
