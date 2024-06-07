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

#### POKE Mechanism

The [POKE Mechanism](./portal-wire-protocol#poke-mechanism) MUST be disabled for the state network. As `content_for_retrieval` is different from `content_for_offer` the POKE mechanism cannot offer content that is verifiable.

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

The data payloads for many content types in the state network differ between OFFER/ACCEPT and FINDCONTENT/FOUNDCONTENT.

The OFFER/ACCEPT payloads need to be provable by their recipients.  These proofs are useful during OFFER/ACCEPT because they verify that the offered data is indeed part of the canonical chain.

The FINDCONTENT/FOUNDCONTENT payloads do not contain proofs because a piece of state can exist under many different state roots.  All payloads can still be proved to be the correct requested data, however, it is the responsibility of the requesting party to anchor the returned data as canonical chain state data.


#### Helper Data Types

##### Paths (Nibbles)

A naive approach to storage of trie nodes would be to simply use the `node_hash` value of the trie node for storage.  This scheme however results in stored data not being tied in any direct way to it's location in the trie.  In a situation where a participant in the DHT wished to re-gossip data that they have stored, they would need to reconstruct a valid trie proof for that data in order to construct the appropriate OFFER/ACCEPT payload.  We include the `path` metadata in state network content keys so that it is possible to reconstruct this proof.

We define path as a sequences of "nibbles" which represent the path through the merkle patritia trie (MPT) to reach the trie node.

```
nibble     := {0, 1, 2, 3, 4, 5, 6, 7, 8, 9, a, b, c, d, e, f}
Nibbles    := ByteList(33)
```

Because each nibble can be expressed using 4 bits, we pack two nibbles in one byte. Leading nibble will occupy higher bits and following nibble will occupy lower bits.

This encoding can introduce ambiguity (e.g. it's not possible to distinguish between single nibble `[1]` and nibbles `[0, 1]`, because both are expressed as `0x01`). To prevent this, we are going to use highest 4 bits of the first byte to specify whether length is even or odd:

- bits `0000` - Number of nibbles is even. The 4 lowest bits of the first byte MUST be set to `0` (resulting that the value of the first byte is `0x00`).
- bits `0001` - Number of nibbles is odd. The first nibble MUST be stored in the 4 lowest bits of the first byte.

All remaining nibbles are packed in pairs of two and added to the first byte.

Examples:

```
[]              -> [0x00]
[0]             -> [0x10]
[1]             -> [0x11]
[0, 1]          -> [0x00, 0x01]
[1, 2, a, b]    -> [0x00, 0x12, 0xab]
[1, 2, a, b, c] -> [0x11, 0x2a, 0xbc]
```

##### Merkle Patricia Trie (MPT) Proofs

Merkle Patricia Trie (MPT) proofs consist of a list of `TrieNode` objects that correspond to
individual trie nodes from the MPT. Each node can be one of the different node types from the MPT
(e.g. branch, extension, leaf).  When serialized, each `TrieNode` is represented as an RLP
serialized list of the component elements. The largest possible node type is the branch node, which
should be up to 532 bytes (16 child nodes of `Bytes32` with extra encoding info), but we specify
1024 bytes to be on the safe side.

Note that `blank` (or `nil`) trie node will never be useful in our context because we don't want to
store it and it can't be part of the trie proof.

```
TrieNode   := ByteList(1024)
TrieProof  := List(TrieNode, max_length=65)
```

The `TrieProof` type is used for both Account Trie and Contract Storage trie.

All `TrieProof` objects are subject to the following validity requirements.

- A: Lexical Ordering
- B: No Extraneous Nodes

###### A: Lexical Ordering

The sequence of nodes in the proof MUST represent the unbroken path in a trie, starting from the
root node and each node being the child of its predecesor. This results in the state root node
always occuring first and node being proven last in the list of trie nodes.

> This validity condition is to ensure that verifcation of the proof can be done
in a single pass.

###### B: No Extraneous Nodes

A proof MUST NOT contain any nodes that are not part of the set needed for proving.

> This validity condition is to protect against malicious or erroneous bloating of proof payloads.


#### Account Trie Node

These data types represent a node from the main state trie.

```
account_trie_node_key  := Container(path: Nibbles, node_hash: Bytes32)
selector               := 0x20

content_key            := selector + SSZ.serialize(account_trie_node_key)
```

If node is an extension or leaf node (not branch node), than the `path` field MUST NOT include the
same nibbles that are stored inside that node.

##### Account Trie Node: OFFER/ACCEPT

This type MUST be used when content offered via OFFER/ACCEPT.

```
content_for_offer      := Container(proof: TrieProof, block_hash: Bytes32)
```

The `proof` field MUST contain the proof for the trie node whose position in the trie and hash are
specified in the `content-key`. The proof MUST be anchored to the block specified by the
`block_hash` field.

##### Account Trie Node: FINDCONTENT/FOUNDCONTENT

This type MUST be used when content retrieved from another node via FINDCONTENT/FOUNDCONTENT.

```
content_for_retrieval := Container(node: TrieNode)
```


#### Contract Trie Node

These data types represent a node from an individual contract storage trie.

```
storage_trie_node_key  := Container(address: Address, path: Nibbles, node_hash: Bytes32)
selector               := 0x21

content_key            := selector + SSZ.serialize(storage_trie_node_key)
```

If node is an extension or leaf node (not branch node), than the `path` field MUST NOT include the
same nibbles that are stored inside that node.

##### Contract Trie Node: OFFER/ACCEPT

This type MUST be used when content offered via OFFER/ACCEPT.

```
content_for_offer      := Container(storage_proof: TrieProof, account_proof: TrieProof, block_hash: Bytes32)
```

The `account_proof` field MUST contain the proof for the account state specified by the `address`
field in the key and it MUST be anchored to the block specified by the `block_hash` field.

The `storage_proof` field MUST contain the proof for the trie node whose position in the trie and
hash are specified in the key and it MUST be anchored to the trie specified by the account state.

##### Contract Trie Node: FINDCONTENT/FOUNDCONTENT

This type MUST be used when content retrieved from another node via FINDCONTENT/FOUNDCONTENT.

```
content_for_retrieval  := Container(node: TrieNode)
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
content_for_offer      := Container(code: ByteList(32768), account_proof: TrieProof, block_hash: Bytes32)
```

The `account_proof` field MUST contain the proof for the account state specified by the `address`
field in the key and it MUST be anchored to the block specified by the `block_hash` field.

##### Contract Code: FINDCONTENT/FOUNDCONTENT

This type MUST be used when content retrieved from another node via FINDCONTENT/FOUNDCONTENT.

```
content_for_retrieval  := Container(code: ByteList(32768))
```


## Gossip

As each new block is added to the chain, the updated state from that block must be gossiped into
the network. In short, every trie node that is created or modified MUST be gossiped into the network,
together with its proof.

### Terminology

The Merkle Patricia Trie (MPT) has three types of nodes: *"branch"*, *"extension"* and *"leaf"*.
The MPT also specifies the `nil` node, but it will never be sent or stored over network, so we will
ignore it for this spec.

Similarly to other tree structure, the `leaf` node is the lowest node on a certain path and it's
where value is stored in the tree (strictly speaking, MPT allows value to be stored in `branch`
nodes as well, but Ethreum storage doesn't use this functionality). The `branch` and `extension`
nodes can be called `intermediate` nodes because there will always be a node that can only be
reached by passing through them.

A *"merkle proof"* or *"proof"* is a collection of nodes from the trie sufficient to recompute the
state root and prove that *"target"* node is part of the trie defined by that state root. A proof is:

- *"ordered"*
    - the order of the nodes in the proof have to represent the path from root node to the target node
        - first node must be the root node, followed by zero or more intermediate nodes, ending
        with a target node
        - it should be provable that any non-first node is part of the preceding node
    - if root node is the target node, then the proof will only contain the root node
    - the target node can be of any type (branch, extension or leaf)
- *"minimal"*
    - it contains only the nodes from on a path from the root node to the target node

### Overview

At each block, the bridge is responsible for creating and gossiping all following data and their proofs:

- account trie data:
    - all of the new and modified trie nodes from the state trie
- contract storage trie data:
    - all of the new and modified trie nodes from each modified contract storage trie
    - proof has to include the proof for the account trie that corresponds to the same contract
- all contract bytecode for newly created contracts
    - proof has to include the proof for the account trie that corresponds to the same contract

A bridge should compute the content-id values for all content key/value pairs. These content-ids
should be sorted by proximity to its own node-id. Beginning with the content that is *closest* to its
own node-id it should proceed to GOSSIP each individual content to nodes *interested* in that content.

#### Special case to consider

It should be highlighted that it's possible for a trie node to be modified even if it is not in the
path of any value that was modified in the block. Consider following example:

Let's assume that trie contains two key/value pairs: `(0x0123, A)` and `(0x1234, B)`. Trie would look
something like this (numbers next to branches indicate the index in the branch node):

```
         branch (root)
       /0             \1 
prefix: 123            prefix: 234
value:  A              value:  B
```

New key/value `(0x0246, C)` is inserted in the next block, resulting in the new trie:

```
                   branch (root)
                /0              \1
          branch                 prefix: 234
        /1      \2               value:  B
prefix: 23       prefix: 46
value:  A        value:  C
```

Note that trie node that stores value `A` changed because its prefix changed, not its value.
