# Execution State Network

This document is the specification for the sub-protocol that supports on-demand availability of state data from the execution chain.

> 🚧 THE SPEC IS IN A STATE OF FLUX AND SHOULD BE CONSIDERED UNSTABLE 🚧

## Overview

The execution state network is a [Kademlia](https://pdos.csail.mit.edu/~petar/papers/maymounkov-kademlia-lncs.pdf) DHT that uses the [Portal Wire Protocol](./portal-wire-protocol.md) to establish an overlay network on top of the [Discovery v5](https://github.com/ethereum/devp2p/blob/master/discv5/discv5-wire.md) protocol.

State data from the execution chain consists of all account data from the main storage trie, all contract storage data from all of the individual contract storage tries, and the individul bytecodes for all contracts.

### Data

All of the execution layer state data is stored in two different formats.

- Raw trie nodes
- Leaf data with merkle proof

#### Types

The network stores the full execution layer state which emcompases the following:

- Account leaf nodes with accompanying trie proof.
- Contract storage leaf nodes with accompanying trie proof.
- Contract bytecode


#### Retrieval

- Account trie leaf data by account address and state root.
- Contract storage leaf data by account address, state root, and slot number.
- Contract bytecode by address and code hash.

## Specification

<!-- This section is where the actual technical specification is written -->

### Distance Function

> TODO: COPY FROM HISTORY-NETWORK


### Content ID Derivation Function

The derivation function for Content ID values is defined separately for each data type.

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

* Content in **Offer/Accept** differs from content in **Find/Found**
* **OFFER** contains a proof
* **FIND** *does not* contain a proof

#### Component Data Elements

#### Proofs
Merkle Patricia Trie (MPT) proofs consist of a list of witness nodes that correspond to each trie node that consists of various data elements depending on the type of node (e.g.blank, branch, extension, leaf).  When serialized, each witness node is represented as an RLP serialized list of the component elements with the largest possible node type being the branch node which when serialized is a list of up to sixteen hashes in `Bytes32` (representing the hashes of each of the 16 nodes in that branch and level of the tree) plus the 4 elements of the node's value (balance, nonce, codehash, storageroot) represented as `Bytes32`.  When combined with the RLP prefixes, this yields a possible maximum length of 667 bytes.  We specify 1024 as the maximum length due to constraints in the SSZ spec for list lengths being a power of 2 (for easier merkleization.)
```
WitnessNode            := ByteList(1024)
MPTWitness             := List(witness: WitnessNode, max_length=32)
```

#### Paths (Nibbles)

We define nibbles as a sequence of single hex values
```
nibble := {0,1,2,3,4,5,6,7,8,9,a,b,c,d,e,f} // 16 possible values
NibblePair := Byte // 2 nibbles tightly packed into a single byte
Nibbles := Vector(NibblePair, length=8) // fixed path length of 8 bytes
```

#### Functions


The combine path and node has functions is designed to use bits from the path as the 'high bits' for computed content_id
Using the remaining bits from the node hash as the 'low bits' for the 32 Byte computed content_id
##### `combine_path_and_node_hash(path: Nibbles, node_hash: Bytes32) -> Bytes32`
> TODO: Write a valid function
> TODO: Nibbles MUST occupy *8* bytes
> TODO: Define nibble function (pack_nibbles)
> TODO: Test vectors
> TODO: Explore attack vectors (mine a collision - same path and same node_hash bytes)
```python
def combine_path_and_node_hash(path: Nibbles, node_hash: Bytes32) -> Bytes32:
        return pack_nibbles(path) + node_hash[8:]
```



```python
# location = address in DHT
U256_MAX = 2**256 - 1
def rotate(address: Bytes20, location: Bytes32) -> Bytes32:
  base_location = keccak256(address)
  rotated_location = base_location + location
  # rotated_location can exceed u256_max, so we mod it
  return rotated_location % U256_MAX
```

#### Account Trie Node *

```
account_trie_node_key := Container(path: Nibbles, node_hash: Bytes32)
selector               := 0x20

content_for_offer       := Container(proof: MPTWitness)
content_for_retrieval   := Container(node: WitnessNode)
content_id             := combine_path_and_node_hash(path: Nibbles, node_hash: Bytes32)
content_key            := selector + SSZ.serialize(account_trie_node_key)
```

#### Contract Trie Node *


```
storage_trie_node_key := Container(address: Address, path: Nibbles, node_hash: Bytes32)
selector               := 0x21

content_for_offer      :=  Container(account_proof: MPTWitness, storage_proof: MPTWitness)
content_for_retrieval  :=  Container(node: WitnessNode)
content_id             :=  rotate(addresss: Address, combine_path_and_node_hash(path: Nibbles, node_hash: Bytes32))
content_key            :=  selector + SSZ.serialize(storage_trie_node_key)
```



## Gossip

### Overview

A bridge node composes proofs for altered (i.e. created/modified/deleted) state data based on the latest block.
These proofs are tied to the latest block by the state root.
The bridge node gossips each proof to some (bounded-size) subset of its peers who are closest to the data based on the distance metric.

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

### Gossip 

Each time a new block is added to their view of the chain, a set of merkle proofs which are all anchored to `Header.state_root` is generated which contains:

- Account trie Data:
    - All of the intermediate and leaf trie nodes from the account trie necessary to prove new and modified accounts.
- Contract Storage trie data:
    - All of the intermediate and leaf trie nodes from each contract storage trie necessary to prove new and modified storage slots.
- All contract bytecode for newly created contracts

> TODO: Figure out language for defining which trie nodes from this proof the bridge node must initialize gossip.

> TODO: Determine mechanism for contract code.

The receiving DHT node will propagate the data to nearby nodes from their routing table.

