# Execution Head-MPT State Network

| 🚧 THE SPEC IS IN A STATE OF FLUX AND SHOULD BE CONSIDERED UNSTABLE 🚧 <br> _Clients should implement Account Trie first and reevaluate poposed approach for Storage Tries_ |
|-|

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

Nodes are responsible for storing fixed state subtree, across all 256 recent blocks.

Nodes are expected to have access to the latest 256 block headers, which they will use to validate
content and handle re-orgs. The [History](../history/history-network.md) and
[Beacon](../beacon-chain/beacon-network.md) networks can be used for this purpose, but
implementations can use other out-of-protocol solutions as well.

Content is gossiped as block's trie-diff subtries. This provides very efficient way to keep node's
subtrie updated as the chain progresses.

### Data

The network stores execution layer state content, which encompases the following data from the
latest 256 blocks:

- Block trie-diffs
- Account trie
- All contract bytecode
- All contract storage tries

#### Types

Available content types are:

- Block trie-diff, identifiable by block hash and subtrie path
- Account trie nodes, identifiable by block hash and account trie path
- Contract's bytecode, identifiable by block hash and account's address
- Contract's storage trie, identifiable by block hash, contract's address, and storate trie path

#### Retrieval

Every content type is retrievable, using its identifiers. This means that account state (balance,
nonce, bytecode, state root) and contract's storage is retrievable using single content lookup.

## Specification

### Distance Function

The network uses standard XOR distance metric, defined in the
[portal wire protocol](../portal-wire-protocol.md#xor-distance-function) specification.

The only difference is that arguments can have less than 256 bits, but both arguments must have the
same length.

### Content ID Derivation Function

> 🚧 **TODO**: Consider changing name to Content Path

The content id is derived only from content's trie path (and contract's address in the case of the
contracts's trie node). Its primary use case is in determining which nodes on the network should
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

> 🚧 **TODO**: consider making radius power of two

A node should track their own radius value and provide this value in all `Ping` or `Pong`
messages it sends to other nodes. A node is expected to maintain `data_radius` information for each
node in its local routing table.

We define the following function to determine whether node in the network should be interested in a
piece of content.

```py
def interested(node, content):
    bits = content.id.length
    return distance(node.id[:bits], content.id) <= node.radius[:bits]
```

> 🚧 **TODO**: revisit if this is correct for non-leaf nodes

> 🚧 **TODO**: maybe adjust for contract's storage trie

### Data Types

#### Helper Data Types

The helper types `Nibbles`, `AddressHash`, `TrieNode`, and `TrieProof` are defined the same way as
in [Execution State Network](state-network.md#helper-data-types).

##### TrieDiff

The Trie-Diff represents the minimal structure that represents how MPT changed from one block to
another. Observe that this is not enough in order to execute block (as data that is only read is not
present).

In order for node to verify that provided trie-diff is complete and minimal, we need both previous
and new value of every changed trie node.

```py
TrieNodeList        = List[TrieNode, limit=65536]
TrieDiff            = Container(before: TrieNodeList, after: TrieNodeList)
```

One should be able to construct two partial views of the Merkle Patricia Trie before and after
associated block. The present part of both partial views should match (and the same for missing
part). The trie nodes are ordered as if they are visited using
[pre-order Depth First Search](https://en.wikipedia.org/wiki/Tree_traversal#Pre-order,_NLR)
traversal algorithm.

The actual usage on this type is slightly different. We use subtrie (at depth 2) of the whole
Trie-Diff. To acocomodate this, we don't have to change the type. Instead, it's enough to allow
first two layers to omit parts that are different (except the subtrie that is specified by content
key).

#### Account Trie-Diff

This data type represent a subtrie of block's Trie-Diff. The entire Trie-Diff is split into
subtries at depth 2 (2 nibbles or 8 bits). This was chosen arbitrary
as a good estimate for not making subtrie-diffs too small or too big.

```py
selector            = 0x30
account_trie_diff   = Container(path: u8, block_hash: Bytes32)

content_key         = selector + SSZ.serialize(account_trie_diff)
content_value       = Container(subtrie_diff: TrieDiff)

def content_id(account_trie_diff):
    return account_trie_diff.path
```

The `subtrie_diff` field of the content value includes first 2 layers of the trie as well (as first
two elements).

#### Account Trie Node

This data type represent a node from the account trie.

```py
selector            = 0x31
account_trie_node   = Container(path: Nibbles, block_hash: Bytes32)

content_key         = selector + SSZ.serialize(account_trie_node)
content_value       = Container(proof: TrieProof)

def content_id(account_trie_node):
    return account_trie_node.path
```

The last trie node in the `proof` MUST correspond to the trie path from the content key.

#### Contract Trie-Diff

This data type represent a subtrie of contract's Trie-Diff at the specific block. The entire
Trie-Diff is split into subtries at depth 2. This was chosen arbitrary as a good estimate for not
making subtrie-diffs too small or too big.

```py
selector            = 0x32
contract_trie_diff  = Container(path: u8, address_hash: AddressHash, block_hash: Bytes32)

content_key         = selector + SSZ.serialize(contract_trie_diff)
content_value       = Container(subtrie_diff: TrieDiff, account_proof: TrieProof)

def content_id(contract_trie_diff):
    return contract_trie_node.path XOR contract_trie_diff.address_hash[:2]
```

#### Contract Trie Node

This data type represent a node from the contracts's storage trie.

```py
selector            = 0x33
contract_trie_node  = Container(path: Nibbles, address_hash: AddressHash, block_hash: Bytes32)

content_key         = selector + SSZ.serialize(contract_trie_node)
content_value       = Container(storage_proof: TrieProof, account_proof: TrieProof)

def content_id(contract_trie_node):
    bits = contract_trie_node.path.length
    return contract_trie_node.path XOR contract_trie_node.address_hash[:bits]
```

The last trie node in the `storage_proof` MUST correspond to the trie path from the content key,
inside contract's storage trie.

#### Contract Bytecode

> 🚧 **TODO**: Evaluate if needed

> 🚧 **TODO**: Write spec (should be similar to [Execution State Network](state-network.md)).

### Algorithms

#### Gossip

Only the Trie-Diffs will be gossiped between nodes. This is done as efficient mechanism for nodes
to keep up-to-date with the chain, as they can easily update the subtrie they are responsible for.

#### Storage layout

Clients MUST store entire subtree that is "close" to their node.id. They MUST also keep track of
all trie nodes from the root of the trie to the root of their respective subtree.

One way of storing data is to combine trie nodes that correspond to the same trie path, and keep
track of the latest version and series of reversed diffs (block number at which trie node changed,
and its previous value)

Trie Diff content type can be used for determining which trie nodes contain reverse diff that go
out of "most recent 256" window and can be purged.
