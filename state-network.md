# Execution State Network

This document is the specification for the sub-protocol that supports on-demand availability of state data from the execution chain.

> 🚧 THE SPEC IS IN A STATE OF FLUX AND SHOULD BE CONSIDERED UNSTABLE 🚧
> 🚧 12/12/23 🚧 WIP: STATE_NETWORK_SPEC v2 🚧 NEW_STATENETWORK_BOOGIE 🚧

## Overview

The execution state network is a [Kademlia](https://pdos.csail.mit.edu/~petar/papers/maymounkov-kademlia-lncs.pdf) DHT that uses the [Portal Wire Protocol](./portal-wire-protocol.md) to establish an overlay network on top of the [Discovery v5](https://github.com/ethereum/devp2p/blob/master/discv5/discv5-wire.md) protocol.

State data from the execution chain consists of all account data from the main storage trie, all contract storage data from all of the individual contract storage tries, and the individul bytecodes for all contracts.

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

The derivation function for Content Id values are defined separately for each data type.

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


#### Component Data Elements

#### Merkle Patricia Trie (MPT) Proofs

Merkle Patricia Trie (MPT) proofs consist of a list of witness nodes that correspond to each trie node that consists of various data elements depending on the type of node (e.g.blank, branch, extension, leaf).  When serialized, each witness node is represented as an RLP serialized list of the component elements with the largest possible node type being the branch node which when serialized is a list of up to sixteen hashes in `Bytes32` (representing the hashes of each of the 16 nodes in that branch and level of the tree) plus the 4 elements of the node's value (balance, nonce, codehash, storageroot) represented as `Bytes32`.  When combined with the RLP prefixes, this yields a possible maximum length of 667 bytes.  We specify 1024 as the maximum length due to constraints in the SSZ spec for list lengths being a power of 2 (for easier merkleization.)

> TODO: Define proof such that there is one canonical representation of a witness that is streamable and minimal??
> Specs should specify order of proof nodes, and disallow inclusion of superflous nodes.

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

#### Helper Functions

We define these helper functions.

##### `combine_path_and_node_hash(path: Nibbles, node_hash: Bytes32) -> Bytes32`

This function is designed to combine the "nibbles" which define the path of a
node in the hexary merkle trie with the `node_hash` of that node in the trie
into a 32 byte content-id value.  This function is designed such that the trie
path occupies the *highest* bits of the content-id and the remaining bits are
sourced from the `node_hash`.  The result of this is that trie nodes which are
close to eacch other in the trie will be statistically likely to also be close
to each other when compared using the XOR distance metric in the DHT.

One thing to notice about this scheme is that for intermediate trie nodes, the
`path` component will often be short, or even empty in the case of the state
root.  However, for leaf nodes, the path component passed into this function
MUST be the full 32 byte path in the trie where the account leaf lives.  This
ensures that the content key and id for a leaf node of the trie doesn't change
as the trie around it changes.

```
# The maximum number of bytes in the resulting content-id that may be sourced
# from the trie path
MAX_PATH_BYTES = 8

# The allowed values for a 'nibble'
NIBBLES_VALUES = {
    0x00, 0x01, 0x02, 0x03,
    0x04, 0x05, 0x06, 0x07,
    0x08, 0x09, 0x0a, 0x0b,
    0x0c, 0x0d, 0x0e, 0x0f,
}

def tightly_pack_nibbles(path: Nibbles) -> bytes:
    """
    Take an even length bytestring of loosely packed nibbles values and return
    them tightly packed as a byte string

    >>> pack_nibbles(b'\x0a\x01\x03\x0f')
    b'\xa1\x3f'
    """
    assert len(path) % 2 == 0
    ipath = iter(path)
    packed_values = []
    for _ in range(len(path) // 2):
        high, low = next(ipath), next(ipath)
        packed = high << 4 | low
        packed_values.append(packed)

    return bytes(packed_values)

def construct_trie_node_content_id(path: Nibbles, node_hash: Bytes32) -> Bytes32:
    # `node_hash` must be a 32 byte value
    assert len(node_hash) == 32
    # `path` may not exceed 64 nibbles which is maximum possible trie depth
    assert len(path) <= 64
    # `path` must be valid `nibbles` values
    assert set(path).issubset(NIBBLES_VALUES)

    trimmed_path = path[:2 * MAX_PATH_BYTES]

    if len(trimmed_path) % 2 == 0:  # path length is "even"
        #
        # path       = (0xa, 0xb, 0xc, 0x1, 0x2, 0x3)
        # node_hash  = 0xdeadbeefdeadbeef....
        # content_id = 0xabc123efdeadbeef....
        #
        # +============+======+======+======+======+======+=====+
        # |   byte #   | #0   | #1   | #2   | #3   | #4   | ... |
        # +============+======+======+======+======+======+=====+
        # | path       | 0xab | 0xc1 | 0x23 |      |      |     |
        # +------------+------+------+------+------+------+-----+
        # | content_id |   ^^ |      |   ^^ |      |      |     |
        # | content_id | 0xab | 0xc1 | 0x23 | 0xef | 0xde | ... |
        # | content_id |      |      |      |   vv |   vv |     |
        # +------------+------+------+------+------+------+-----+
        # | node_hash  | 0xde | 0xad | 0xbe | 0xef | 0xde | ... |
        # +------------+------+------+------+------+------+-----+
        #
        packed_path = tightly_pack_nibbles(trimmed_path)
        node_hash_low_part = node_hash[len(packed_path):]
        return packed_path + node_hash_low_part
    else:  # path length is "odd"
        #
        # path       = (0xa, 0xb, 0xc, 0x1, 0x2)
        # node_hash  = 0xdeadbeefdeadbeef....
        # content_id = 0xabc12eefdeadbeef....
        #
        # +============+======+======+======+======+======+=====+
        # |   byte #   | #0   | #1   | #2   | #3   | #4   | ... |
        # +============+======+======+======+======+======+=====+
        # | path       | 0xab | 0xc1 | 0x2  |      |      |     |
        # +------------+------+------+------+------+------+-----+
        # | content_id |   ^^ |      |   ^  |      |      |     |
        # | content_id | 0xab | 0xc1 | 0x2e | 0xef | 0xde | ... |
        # | content_id |      |      |    v |   vv |   vv |     |
        # +------------+------+------+------+------+------+-----+
        # | node_hash  | 0xde | 0xad | 0xbe | 0xef | 0xde | ... |
        # +------------+------+------+------+------+------+-----+
        #
        packed_path_high_part = tightly_pack_nibbles(trimmed_path[:-1])

        # Since the nibbles value in this case is odd length, then we must
        # combine the last nibble with the lower 4 bits of the byte in that
        # position from the node_hash value.
        middle_high_part = trimmed_path[-1] << 4
        middle_low_part = node_hash[len(packed_path_high_part)] & 0x0f
        middle_byte = middle_high_part | middle_low_part

        node_hash_low_part = node_hash[len(packed_path_high_part) + 1:]

        return packed_path_high_part + bytes((middle_byte,)) + node_hash_low_part
```

#### `rotate(address: Bytes20, location: Bytes32) -> Bytes32`

This function is used to rotate the content-id values of contract storage trie
nodes in the DHT space, in order to ensure that contract storage tries are
evenly distributed accross the DHT key space.


```python
U256_MAX = 2**256 - 1

def rotate(address: Bytes20, location: Bytes32) -> Bytes32:
    """
    Location is a 32-byte value representation a location in the DHT key space.
    """
    rotation_amount = keccak256(address)
    rotated_location = rotation_amount + location

    # The modulo here ensures that the resulting location is constrained
    # appropriately to the 32-byte DHT key space.
    return rotated_location % U256_MAX
```

#### Account Trie Node


```
account_trie_node_key  := Container(path: Nibbles, node_hash: Bytes32)
selector               := 0x20

content_for_offer      := Container(proof: MPTWitness, block_hash: Bytes32)
content_for_retrieval  := Container(node: WitnessNode)
content_id             := construct_trie_node_content_id(path: Nibbles, node_hash: Bytes32)
content_key            := selector + SSZ.serialize(account_trie_node_key)
```

#### Contract Trie Node *


```
storage_trie_node_key  := Container(address: Address, path: Nibbles, node_hash: Bytes32)
selector               := 0x21

content_for_offer      :=  Container(account_proof: MPTWitness, storage_proof: MPTWitness, block_hash: Bytes32)
content_for_retrieval  :=  Container(node: WitnessNode)
content_id             :=  rotate(storage_trie_node_key.address: Address, construct_trie_node_content_id(storage_trie_node_key.path, storage_trie_node_key.node_hash))
content_key            :=  selector + SSZ.serialize(storage_trie_node_key)
```


#### Contract Code *

> NOTE: Because CREATE2 opcode allows for redeployment of new code at an existing address, we MUST randomly distribute contract code storage across the DHT keyspace to avoid hotspots developing in the network for any contract that has had many different code deployments.  Were we to use the path based *high-bits* approach for computing the content-id, it would be possible for a single location in the network to accumulate a large number of contract code objects that all live in roughly the same space.
Problematic!

```
contract_code_key      := Container(address: Address, code_hash: Bytes32)
selector               := 0x22

content_for_offer      := Container(code: ByteList, account_proof: MPTWitness, block_hash: Bytes32)
content_for_retrieval  := Container(code: ByteList)
content_id             := sha256(contract_code_key.address + contract_code_key.code_hash)
content_key            := selector + SSZ.serialize(contract_code_key)
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

