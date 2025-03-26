# Execution Head-MPT State Network

This document is the specification for the Portal Network that supports on-demand availability of
close to the head of the chain, Merkle Patricia Trie State data from the execution chain.

While similar to the [Execution State network](state-network.md), it has some unique features:

- It supports direct lookup of the account state, contract's code and contract's storage
- It only stores state that is present in any of the latest 256 blocks
- Nodes are responsible for storing subtree of the entire state trie

## Overview

The Execution Head-MPT State Network is a
[Kademlia](https://pdos.csail.mit.edu/~petar/papers/maymounkov-kademlia-lncs.pdf) DHT that uses the
[Portal Wire Protocol](../portal-wire-protocol.md) to establish an overlay network on top of the
[Discovery v5](https://github.com/ethereum/devp2p/blob/master/discv5/discv5-wire.md) protocol.

Nodes are expected to have access to the latest 256 block headers, which they will use to validate
content and handle re-orgs. This [History](../history/history-network.md) and
[Beacon](../beacon-chain/beacon-network.md) networks can be used for this purpose, but
implementations can use other out-of-protocol solutions as well.

### Data

The network stores full execution layer state, which encompases the following:

- Account trie
- All contract bytecode
- All contract storage tries

The network stores only state that is present in any of the latest 256 blocks.

#### Types

Available content types are:

- Account trie nodes, identifiable by block hash and account trie path
- Contract's bytecode, identifiable by block hash and account's address
- Contract's storage trie, identifiable by block hash, contract's address, and storate trie path

#### Retrieval

Every content type is retrievable, using its identifiers. This means that account state (balance,
nonce, bytecode, state root) and contract's storage is retrievable using single content lookup.

## Specification

<!-- This section is where the actual technical specification is written -->

### Distance Function

The network uses standard XOR distance metric, defined in the
[portal wire protocol](../portal-wire-protocol.md#xor-distance-function) specification.

The only difference is that elements can have less than 256 bits, but they must have the same
length.

### Content ID Derivation Function

TODO: Consider chaning name to Content Path

The content id is derived only from content's trie path (and contract's address in the case of the
contracts's trie node). It's primary use case is in figuring out which nodes on the network should
store the content.

The content id has following properties are:

- It has variable length, between 0 and 256 bits (only multiplies of 4), representing trie path
- It's not unique, meaning different content will have the same content id
- The trie path of the contract's storage trie node is modified using contract's address

The derivation function is slightly different for different types and is defined below.

### Wire Protocol

#### Protocol Identifier

As specified in the [Protocol identifiers](../portal-wire-protocol.md#protocol-identifiers) section
of the Portal wire protocol, the `protocol` field in the `TALKREQ` message **MUST** contain the
value of `0x5009`.

#### Supported Message Types

The network supports the following protocol messages:

- `Ping` - `Pong`
- `Find Nodes` - `Nodes`
- `Find Content` - `Found Content`
- `Offer` - `Accept`

#### `Ping.payload` & `Pong.payload`

The pyload type of the first `Ping` message between nodes MUST be
[Type 0: Client Info, Radius, and Capabilities Payload](../ping-extensions/extensions/type-0.md).
Nodes then upgrade to the latest payload type supported by both of the clients.

List of currently supported payloads, by latest to oldest.
-  [Type 1 Basic Radius Payload](../ping-extensions/extensions/type-1.md)

### Routing Table 

The network uses the standard routing table structure from the Portal Wire Protocol.

### Node State

#### Data Radius

The network includes one additional piece of node state that should be tracked: `data_radius`. This
value is a 256 bit integer and represents the data that a node is "interested" in. The value may
fluctuate as the contents of local key-value store changes.

A node should track their own radius value and provide this value in all `Ping` or `Pong`
messages it sends to other nodes. A node is expected to maintain `data_radius` information for each
node in its local routing table.

We define the following function to determine whether node in the network should be interested in a
piece of content.

```
interested(node, content) :=
    bits = content.id.length
    return distance(node.id[..bits], content.id) <= node.radius[..bits]
```

TODO: revisit if this is correct for non-leaf nodes

TODO: maybe adjust this for contract's storage trie

### Data Types

<!--

This section should contain individual sections defining each type of content
supported by this network.  Each content type defined should have a definition
which includes how the content is encoded and the encoding for the
corresponding Content Key

-->

### Algorithms

<!-- This section should contain definitions of any protocol specific algorithms -->
