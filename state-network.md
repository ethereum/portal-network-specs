# Execution State Network

This document is the specification for the sub-protocol that supports on-demand availability of state data from the execution chain.

## Overview

The execution state network is a [Kademlia](https://pdos.csail.mit.edu/~petar/papers/maymounkov-kademlia-lncs.pdf) DHT that uses the [Portal Wire Protocol](./portal-wire-protocol.md) to establish an overlay network on top of the [Discovery v5](https://github.com/ethereum/devp2p/blob/master/discv5/discv5-wire.md) protocol.

State data from the execution chain consists of all account data from the main storage trie, all contract storage data from all of the individual contract storage tries, and the individul bytecodes for all contracts across all historical state roots.  This is traditionally referred to as an "archive node".

### Data

The network stores the full execution layer state which emcompases the following:

- Account trie nodes
- Contract storage trie nodes
- Contract bytecode

The network is implemented as an "archive" node meaning that it stores all
tries for all historical blocks.


#### Retrieval

- Account trie nodes by their node hash.
- Contract storage trie nodes by their node hash.
- Contract bytecode by code hash.

## Specification

<!-- This section is where the actual technical specification is written -->

### Distance Function

The state network uses the stock XOR distance metric defined in the portal wire protocol specification.


### Content ID Derivation Function

The state network uses the SHA256 Content ID derivation function from the portal wire protocol specification.

### Wire Protocol

#### Protocol Identifier

As specified in the [Protocol identifiers](./portal-wire-protocol.md#protocol-identifiers) section of the Portal wire protocol, the `protocol` field in the `TALKREQ` message **MUST** contain the value of `0x500A`.

#### Supported Message Types

The execution state network supports the following protocol messages:

- `Ping` - `Pong`
- `Find Nodes` - `Nodes`
- `Find Content` - `Found Content`
- `Offer` - `Accept`

#### `Ping.custom_data` & `Pong.custom_data`

In the execution state network the `custom_payload` field of the `Ping` and `Pong` messages is the serialization of an SSZ Container specified as `custom_data`:

```
custom_data = Container(data_radius: uint256)
custom_payload = SSZ.serialize(custom_data)
```

### Routing Table 

The execution state network uses the standard routing table structure from the Portal Wire Protocol.

### Node State

#### Data Radius

The execution state network includes one additional piece of node state that should be tracked.  Nodes must track the `data_radius` from the Ping and Pong messages for other nodes in the network.  This value is a 256 bit integer and represents the data that a node is "interested" in.  We define the following function to determine whether node in the network should be interested in a piece of content.

```
interested(node, content) = distance(node.id, content.id) <= node.radius
```

A node is expected to maintain `radius` information for each node in its local node table. A node's `radius` value may fluctuate as the contents of its local key-value store change.

A node should track their own radius value and provide this value in all Ping or Pong messages it sends to other nodes.

### Data Types

#### OFFER/ACCEPT vs FINDCONTENT/FOUNDCONTENT payloads

The data payloads for many content types in the history network differ between OFFER/ACCEPT and FINDCONTENT/FOUNDCONTENT.

The OFFER/ACCEPT payloads need to be provable by their recipients.  These proofs are useful during OFFER/ACCEPT because they verify that the offered data is indeed part of the canonical chain.

The FINDCONTENT/FOUNDCONTENT payloads do not contain proofs because a piece of state can exist under many different state roots.  All payloads can still be proved to be the correct requested data, however, it is the responsibility of the requesting party to anchor the returned data as canonical chain state data.


#### Helper Data Types

##### Paths (Nibbles)

A naive approach to storage of trie nodes would be to simply use the `node_hash` value of the trie node for storage.  This scheme however results in stored data not being tied in any direct way to it's location in the trie.  In a situation where a participant in the DHT wished to re-gossip data that they have stored, they would need to reconstruct a valid trie proof for that data in order to construct the appropriate OFFER/ACCEPT payload.  We include the `path` metadata in state network content keys so that it is possible to reconstruct this proof.

We define path as a sequences of "nibbles" which represent the path through the merkle patritia trie (MPT) to reach the trie node.

```
nibble     := {0, 1, 2, 3, 4, 5, 6, 7, 8, 9, a, b, c, d, e, f}
NibblePair := Byte  # 2 nibbles tightly packed into a single byte
Nibbles    := Container(is_odd_length=bool, packed_nibbles=List(NibblePair, max_length=32))
```

`Nibbles.packed_nibbles` is a sequence of bytes with each byte containing two
nibbles.  When encoding an odd length sequence of nibbles the high bits of the
final byte should be left empty and `Nibbles.is_odd_length` boolean flag should be
set to `True`.


##### Merkle Patricia Trie (MPT) Proofs

Merkle Patricia Trie (MPT) proofs consist of a list of `WitnessNode` objects that correspond to individual trie nodes from the MPT. Each node can be one of the different node types from the MPT (e.g.blank, branch, extension, leaf).  When serialized, each `WitnessNode` is represented as an RLP serialized list of the component elements. The largest possible node type is the branch node which when serialized is a list of up to sixteen hashes in `Bytes32` (representing the hashes of each of the 16 nodes in that branch and level of the tree) plus the 4 elements of the node's value (balance, nonce, codehash, storageroot) represented as `Bytes32`.  When combined with the RLP prefixes, this yields a possible maximum length of 667 bytes.  We specify 1024 as the maximum length due to constraints in the SSZ spec for list lengths being a power of 2 (for easier merkleization.)

```
WitnessNode            := ByteList(1024)
Witness                := List(WitnessNode, max_length=1024)
StateWitness           := Container(key: Nibbles, proof: Witness)
StorageWitness         := Container(key: Nibbles, proof: Witness, state_witness: StateWitness)
```

The `StateWitness.key` denotes the path to the trie node that is proven by the `StateWitness.proof`.  The same applies to `StorageWitness.key/StorageWitness.proof`.

The `StorageWitness.state_witness` MUST be for a leaf node in the account trie.  The `StorageWitness.proof` MUST be anchored to the contract state root denoted by the account from the `StorageWitness.state_witness`.

All `Witness` objects are subject to the following validity requirements.

- A: Lexical Ordering
- B: No Extraneous Nodes
- C: No Redundant Nodes

###### A: Lexical Ordering

The sequence of nodes in the witness MUST be lexically ordered by their nibbles
path in the trie.  This results in the state root node always occuring first in
the list of trie nodes.

> This validity condition is to ensure that verifcation of the proof can be done
in a single pass.

###### B: No Extraneous Nodes

A witness MUST NOT contain any nodes that are not part of the set needed to for proving.  

> This validity condition is to protect against malicious or erroneous bloating of proof payloads.

###### C: No Redundant Nodes

A witness MUST NOT contain any nodes that can be computed from other nodes in
the proof.  For example, the inclusion of a parent node along with the
inclusion of all of that node's children since the parent node can be
reconstructed from the children.

> This validity condition is to protect against malicious or erroneous bloating
of proof payloads and to ensure that verification of proofs can be done in a
single pass.


#### Account Trie Node

These data types represent a node from the main state trie.

```
account_trie_node_key  := Container(path: Nibbles, node_hash: Bytes32)
selector               := 0x20

content_key            := selector + SSZ.serialize(account_trie_node_key)
```

##### Account Trie Node: OFFER/ACCEPT

This type MUST be used when content offered via OFFER/ACCEPT.

```
content_for_offer      := Container(proof: StateWitness, block_hash: Bytes32)
```


##### Account Trie Node: FINDCONTENT/FOUNDCONTENT

This type MUST be used when content retrieved from another node via FINDCONTENT/FOUNDCONTENT.

```
content_for_retrieval := Container(node: WitnessNode)
```


#### Contract Trie Node

These data types represent a node from an individual contract storage trie.

```
storage_trie_node_key  := Container(address: Address, path: Nibbles, node_hash: Bytes32)
selector               := 0x21

content_key            := selector + SSZ.serialize(storage_trie_node_key)
```


##### Contract Trie Node: OFFER/ACCEPT

This type MUST be used when content offered via OFFER/ACCEPT.

```
content_for_offer      := Container(proof: StorageWitness, block_hash: Bytes32)
```


##### Contract Trie Node: FINDCONTENT/FOUNDCONTENT

This type MUST be used when content retrieved from another node via FINDCONTENT/FOUNDCONTENT.

```
content_for_retrieval  := Container(node: WitnessNode)
```


#### Contract Code

These data types represent the bytecode for a contract.

> NOTE: Because CREATE2 opcode allows for redeployment of new code at an existing address, we MUST randomly distribute contract code storage across the DHT keyspace to avoid hotspots developing in the network for any contract that has had many different code deployments.  Were we to use the path based *high-bits* approach for computing the content-id, it would be possible for a single location in the network to accumulate a large number of contract code objects that all live in roughly the same space.
Problematic!

```
contract_code_key      := Container(address: Address, code_hash: Bytes32)
selector               := 0x22

content_key            := selector + SSZ.serialize(contract_code_key)
```


##### Contract Code: OFFER/ACCEPT

This types MUST be used when content offered via OFFER/ACCEPT.

```
content_for_offer      := Container(code: ByteList, account_proof: StateWitness, block_hash: Bytes32)
```


##### Contract Code: FINDCONTENT/FOUNDCONTENT

This type MUST be used when content retrieved from another node via FINDCONTENT/FOUNDCONTENT.

```
content_for_retrieval  := Container(code: ByteList)
```


## Gossip

As each new block is added to the chain, the state from that block must be gossiped into the network.  
The state network defines a specific gossip algorithm which is referred to as "Recursive Gossip".  This 
section of the specification defines how this gossip mechanism works.


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

The node labeled `X` in the diagram found at level 0 or the "root" of the trie.

#### *"trie node"*

Any of the individual nodes in the trie represented by either `X` for the state root node, or a `1` or `0` for trie nodes.

#### *"intermediate node"*

Any of the nodes in the trie which are computed from other nodes in the trie.  The nodes in the diagram at levels 0, 1, 2, and 3 are all intermediate.

#### *"leaf node"*

Any node in the trie that represents a value stored in the trie.  The nodes in the diagram at level 4 are leaf nodes.

#### *"merkle proof"* or *"proof"*

A collection of nodes from the trie sufficient to recompute the state root and prove that one or more nodes are part of the trie defined by that state root.

> A proof is considered to be "minimal" if it contains only the minimum set of trie nodes needed to recompute the state root.


### Overview

The goal of the "recursive gossip" mechanism is to reduce the burden of
responsibility placed on bridge nodes for injecting new state data into the
network while simultaniously spreading the responsibility for gossiping new
state data across the nodes in the network.

At each block we construct a proof against the new state root which contains
all of the state changes which occured within that block.  

This proof contains *explicitly* a mixed set of leaf and intermediate
nodes, as well as implicitly a set of intermediate nodes which can be
computed from the nodes that are part of the proof.

```
EXAMPLE: Recursive Gossip Inception

0:                           A*
                            / \
                          /     \
                        /         \
                      /             \
                    /                 \
                  /                     \
                /                         \
1:             B*                          C
             /   \
           /       \
         /           \
2:      D             E*
                     / \
                    /   \
3:                 F     G*
                        / \
4:                     H*  I

- "*" denotes trie node modified
```

In the example proof diagramed here we can see a *leaf* node `H` which
represents the only modified leaf state in this proof.  Note that all of the
nodes along the path leading to `H` are also modified.

The *minimal* proof would contain the nodes `[D, F, H, I, C]`

The bridge node would search the DHT for nodes that are *interested* in storing
the node `H` and gossip this proof to those nodes.

The recipients of this gossip are then responsible for gossiping the parent
intermediate node `G`.  To do so, they would strip off the `H` and `I` nodes
from this proof resulting in the following:

```
EXAMPLE: Recursive Gossip Round 1

0:                           A*
                            / \
                          /     \
                        /         \
                      /             \
                    /                 \
                  /                     \
                /                         \
1:             B*                          C
             /   \
           /       \
         /           \
2:      D             E*
                     / \
                    /   \
3:                 F     G*

4:
```

At this stage, the minimal proof for `G` would be `[D, F, G, C]`.  The nodes
which received the initial gossip message for `H` would construct this proof
by removing the un-necessary nodes, after which they would search the DHT for
nodes that are interested in `F` and gossip this proof to them..

The recipients of that gossip are then responsible for gossiping the parent
intermediate node `E`.  This process repeats until it terminates at the state
root, with the final round of gossip only containing the `[A]` which is the
state root node of the trie.


### Bridge Node Responsibilities

Each time a new block is added to their view of the chain, a set of merkle
proofs which are all anchored to `Header.state_root` is generated which
contains:

- Account trie Data:
    - All of the new and modified account nodes from the state trie.
    - All of the intermediate and leaf trie nodes from the account trie necessary to prove new and modified accounts.
- Contract Storage trie data:
    - All of the new and modified storage slots from each modified contract storage trie.
    - All of the intermediate and leaf trie nodes from each contract storage trie necessary to prove new and modified storage slots.
- All contract bytecode for newly created contracts

A bridge should compute the content-id values for all of this new state data
that should be part of the "inception" round of recursive gossip.  These pieces
of content should be sorted by proximity to its own node-id.  Beginning with
the content that is *closest* to its own node-id it should proceed to GOSSIP
each individual piece of content to nodes interested in that content.
