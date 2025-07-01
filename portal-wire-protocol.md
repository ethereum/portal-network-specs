# Portal Wire Protocol

The Portal wire protocol is the default peer-to-peer protocol by which Portal nodes communicate.

The Portal wire protocol enables nodes to communicate over the [Node Discovery Protocol v5](https://github.com/ethereum/devp2p/blob/56a498ee34ee0fb69ffd33dda026d632af4c4048/discv5/discv5-wire.md#talkreq-request-0x05) layer using the `TALKREQ` and `TALKRESP` messages.

Sub-protocols using the Portal wire protocol **MUST** choose a byte string to serve as the protocol identifier. Messages are differentiated between different sub-protocol by this protocol identifier which is set in the `TALKREQ` message.

Sub-protocol using the wire protocol **MAY** choose to exclude certain message types and **MUST** specify which messages are supported.

Unsupported messages **SHOULD** receive a `TALKRESP` message with an empty payload.

## Protocol Version

The portal wire protocol is versioned using unsigned integers.  The current version is `1`.

Support for protocol versions is signaled through the ENR record under the key `pv`.  The value should be a serialized SSZ object with the schema `List[uint8, limit=8]` whos value are the list of supported protocol versions.  If this field is missing from the ENR it should be assumed that the client only supports version `0` of the protocol.

Clients should communicate with each other using the highest mutually supported protocol version.  Exchange of ENR records for negotiating protocol version is done using the base DiscoverV5 protocol.

Changes to the protocol that increment the version number should be recorded in the [Changelog](./protocol-version-changelog.md)

## Protocol identifiers

All protocol identifiers consist of two bytes. The first byte is "`P`" (`0x50`), to indicate "the Portal network", the second byte is a specific network identifier.

### Mainnet identifiers

Currently defined mainnet protocol identifiers:

- Inclusive range of `0x5000` - `0x5008`: Reserved for future networks or network upgrades
- `0x5009`: Execution Head-MPT State Network
- `0x500A`: Execution State Network
- `0x500B`: Execution Legacy History Network
- `0x500C`: Beacon Chain Network
- `0x500D`: Execution Canonical Transaction Index Network (planned but not implemented)
- `0x500E`: Execution Verkle State Network (planned but not implemented)
- `0x500F`: Execution Transaction Gossip Network (planned but not implemented)

### Angelfood identifiers (testnet)

> Angelfood is the name for our current test network.

Currently defined `angelfood` protocol identifiers:

- `0x5049`: Execution Head-MPT State Network
- `0x504A`: Execution State Network
- `0x504B`: Execution Legacy History Network
- `0x504C`: Beacon Chain Network
- `0x504D`: Execution Canonical Transaction Index Network (planned but not implemented)
- `0x504E`: Execution Verkle State Network (planned but not implemented)
- `0x504F`: Execution Transaction Gossip Network (planned but not implemented)

### Sepolia identifiers (testnet)

Currently defined `sepolia` protocol identifiers:

- `0x505A`: Execution State Network
- `0x505B`: Execution Legacy History Network
- `0x505C`: Beacon Chain Network
- `0x505D`: Execution Canonical Transaction Index Network (planned but not implemented)
- `0x505E`: Execution Verkle State Network (planned but not implemented)
- `0x505F`: Execution Transaction Gossip Network (planned but not implemented)

## Nodes and Node IDs

Nodes in the portal network are represented by their [EIP-778 Ethereum Node Record (ENR)](https://github.com/ethereum/EIPs/blob/master/EIPS/eip-778.md) from the Discovery v5 network. A node's `node-id` is derived according to the node's identity scheme, which is specified in the node's ENR. A node's `node-id` represents its address in the DHT.  Node IDs are interchangeable between 32 byte identifiers and 256 bit integers.


## Content Keys and Content IDs

Content keys are used to request or offer specific content data. As such the content key and content data can be thought of as a key-value pair with nodes in the network storing the content data and the content key being the identifier used to request and retrieve the data.

Each sub-protocol defines the set of supported content keys and the corresponding data payloads for each content key.  The encoding of content keys is defined at the sub-protocol level.

Content keys are passed in their encoded format as byte strings to the messages defined in the Portal wire protocol.

Content IDs are derived from the content key.  The Content ID can be represented interchangeably as either a 32 byte value or a 256 bit integer.  The Content ID defines the address of the content in the DHT.  The function for deriving the Content ID from a content key is defined at the sub-protocol level.

### SHA256 Content ID Derivation Function

The SHA256 Content ID derivation function is defined here for convenience as it is the most commonly used:

```
content_id = sha256(encoded_content_key)
```

## Transmission of data that exceeds the UDP packet limit

The transmission of data that is too large to fit a single packet is done using [uTP](../assets/eip-7718/bep_0029-rst_post.pdf).

> The Portal wire protocol currently implements uTP over the `TALKREQ/TALKRESP` messages.  Future plans are to move to the [sub-protocol data transmission](https://github.com/ethereum/devp2p/issues/229) in order to use a protocol native mechanism for establishing packet streams between clients.


## Request - Response Messages

The messages in the protocol are transmitted using the `TALKREQ` and `TALKRESP` messages from the base [Node Discovery Protocol](https://github.com/ethereum/devp2p/blob/56a498ee34ee0fb69ffd33dda026d632af4c4048/discv5/discv5-wire.md#talkreq-request-0x05).

All messages in the protocol have a request-response interaction:

- Request messages **MUST** be sent using a `TALKREQ` message.
- Response messages **MUST** be sent using the corresponding `TALKRESP` message.

All messages are encoded as an [SSZ Union](https://github.com/ethereum/consensus-specs/blob/04f5ec595d78c0e3e43794fb7644c18f2584770d/ssz/simple-serialize.md#union) type.

```
message = Union[ping, pong, find_nodes, nodes, find_content, content, offer, accept]
serialized_message = SSZ.serialize(message)
```

The `serialized_message` is the payload passed to the `request` field of the `TALKREQ` message or the `response` field of the `TALKRESP` message.

The type values for the `Union` are the SSZ Containers specified per message type.

The transmission of `content` data that is too large to fit a single packet is done over [uTP](./utp/discv5-utp.md).

### Message Types

#### Ping (0x00)

Request message to check if a node is reachable, communicate basic information about our node, and request basic information about the recipient node.  Additionally sub-protocol can define a schema for the `payload` field to exchange additional information.

```
selector     = 0x00
ping         = Container(enr_seq: uint64, payload_type: uint16, payload: ByteList[1100])
```

- `enr_seq`: The node's current sequence number of their ENR record.
- `payload_type`: Custom payload type identifier as defined in [Ping Custom Payload Extensions](./ping-extensions/README.md).
- `payload`: Custom SSZ payload as defined in [Ping Custom Payload Extensions](./ping-extensions/README.md).

#### Pong (0x01)

Response message to Ping(0x00)

```
selector     = 0x01
pong         = Container(enr_seq: uint64, payload_type: uint16, payload: ByteList[1100])
```

- `enr_seq`: The node's current sequence number of their ENR record.
- `payload_type`: Custom payload type identifier as defined in [Ping Custom Payload Extensions](./ping-extensions/README.md).
- `payload`: Custom SSZ payload as defined in [Ping Custom Payload Extensions](./ping-extensions/README.md).

#### Find Nodes (0x02)

Request message to get ENR records from the recipient's routing table at the given logarithmic distances. The distance of `0` indicates a request for the recipient's own ENR record.

```
selector     = 0x02
find_nodes   = Container(distances: List[uint16, limit=256])
```

- `distances`: a sorted list of distances for which the node is requesting ENR records for.
    - Each distance **MUST** be within the inclusive range `[0, 256]`
    - Each distance in the list **MUST** be unique.

#### Nodes (0x03)

Response message to FindNodes(0x02).

```
selector     = 0x03
nodes        = Container(total: uint8, enrs: List[ByteList[2048], limit=32])
```

- `total`: The total number of `Nodes` response messages being sent. Currently fixed to only 1 response message.
- `enrs`: List of byte strings, each of which is an RLP encoded ENR record.
    * Individual ENR records **MUST** correspond to one of the requested distances.
    * It is invalid to return multiple ENR records for the same `node_id`.
    * The ENR record of the requesting node **SHOULD** be filtered out of the list.

#### Find Content (0x04)

Request message to get the `content` with `content_key`. In case the recipient does not have the data, a list of ENR records of nodes that are closest to the requested content.

```
selector     = 0x04
find_content = Container(content_key: ByteList[2048])
```

- `content_key`: The encoded content key for the content being requested.

#### Content (0x05)

Response message to Find Content (0x04).

This message can contain any of 

- a uTP connection ID
- the requested content
- a list of ENRs

```
selector     = 0x05
content      = Union[connection_id: Bytes2, content: ByteList[2048], enrs: List[ByteList[2048], 32]]
```

- `connection_id`: Connection ID to set up a uTP stream to transmit the requested data.
    - Connection ID values **SHOULD** be randomly generated.
- `content`: byte string of the requested content.
    - This field **MUST** be used when the requested data can fit in this single response.
- `enrs`: List of byte strings, each of which is an RLP encoded ENR record.
    - The list of ENR records **MUST** be closest nodes to the requested content that the responding node has stored.
    - The set of derived `node_id` values from the ENR records **MUST** be unique.
    - The ENR record of the requesting & responding node **SHOULD** be filtered out of the list.

If the node does not hold the requested content, and the node does not know of any nodes with eligible ENR values, then the node **MUST** return `enrs` as an empty list.

Upon *sending* this message with a `connection_id`, the sending node **SHOULD** *listen* for an incoming uTP stream with the generated `connection_id`.

Upon *receiving* this message with a `connection_id`, the receiving node **SHOULD** *initiate* a uTP stream with the received `connection_id`.

##### `content` Union Definition

The `Union` defined in the `content` field of the `Content (0x05)` message is defined as below:

**`connection_id`**

```
selector = 0x00
ssz-type = Bytes2
```

**`content`**

```
selector = 0x01
ssz-type = ByteList[2048]
```

**`enrs`**

```
selector = 0x02
ssz-type = List[ByteList[2048], 32]
```


##### Length prefixing for uTP transfers

In the case that the content item is send over uTP, it MUST be prefixed with a variable length unsigned integer (varint). The varint MUST hold the size, in bytes, of the consecutive content item.

The varint encoding used is Unsigned LEB128.
The maximum size allowed for this application is limited to `uint32`.

> The encoding of the content itself is specified by the content type being transferred.

The encoded data of the content item to be send over the stream can be formalized as:

```py
utp_payload = varint(len(content)) + content
```

#### Offer (0x06)

Request message to offer a set of `content_keys` that this node has `content` available for.

```
selector     = 0x06
offer        = Container(content_keys: List[ByteList[2048], limit=64])
```

- `content_keys`: A list of encoded `content_key` entries.

#### Accept (0x07)

Response message to Offer (0x06).

Signals interest in receiving the offered data from the corresponding Offer message.

```
selector     = 0x07
accept       = Container(connection_id: Bytes2, content_keys: ByteList[64])
```

- `connection_id`: Connection ID to set up a uTP stream to transmit the requested data.
    - ConnectionID values **SHOULD** be randomly generated.
- `content_keys`: Signals which content keys are desired.
    - A byte-list corresponding to the offered keys with the byte in the positions of the desired keys set to `0`.
      - 0: Accept the content
      - 1: Generic decline, catch all if their is no specified case
      - 2: Declined, content already stored
      - 3: Declined, content not within node's radius
      - 4: Declined, rate limit reached. Node can't handle anymore connections
      - 5: Declined, inbound rate limit reached for accepting a specific content_id, used to protect against thundering herds
      - 6: Declined, content key not verifiable
      - 7 to 255: Unspecified decline, this shouldn't be used, but if it is received should just be treated the same as any other decline

Upon *sending* this message, the requesting node **SHOULD** *listen* for an incoming uTP stream with the generated `connection_id`.

Upon *receiving* this message, the serving node **SHOULD** *initiate* a uTP stream with the received `connection_id`.

##### Content Encoding

Up to 64 content items can be sent over the uTP stream after an `Offer` request and `Accept` response.

In order to be able to discern these different content items, a variable length unsigned integer (varint) MUST be prefixed to each content item.
The varint MUST hold the size, in bytes, of the consecutive content item.

The varint encoding used is Unsigned LEB128.
The maximum size allowed for this application is limited to `uint32`.

The content item itself MUST be encoded as is defined for each specific network and content type.

The encoded data of n encoded content items to be send over the stream can be formalized as:

```py
# n encoded content items to be send over the stream, with n <= 64
encoded_content_list = [content_0, content_1, ..., content_n]

# encoded data to be send over the stream
encoded_data = varint(len(content_0)) + content_0 + varint(len(content_1)) + content_1 + ... + varint(len(content_n)) + content_n
```

### Distance Function

Each sub protocol must specify a distance function for computing the distance
between either two nodes in the network or a node and a piece of content.

#### XOR Distance Function

The XOR `distance` function is defined as:

```
distance(a: uint256, b: uint256) = a XOR b
```

Similarly, we define a `logdistance` function identically to the Discovery v5 network.

```
logdistance(a: uint256, b: uint256) = log2(distance(a, b))
```

### Test Vectors

A collection of test vectors for this specification can be found in the [Portal wire test vectors](./portal-wire-test-vectors.md) document.


## Routing Table

Sub-networks that use the Portal Wire Protocol will form an independent overlay DHT which requires nodes to maintain a separate routing table from the one used in the base Discv5 protocol.

### Standard Routing Table

We define the "standard" routing table as follows:

We adapt the node state from the Discovery v5 protocol. Assume identical definitions for the replication parameter `k` and a node's k-bucket table. Also assume that the routing table follows the structure and evolution described in section 2.4 of the Kademlia paper.

Nodes keep information about other nodes in a routing table of k-buckets. This routing table is specific to a sub protocol and is distinct from the node's underlying Discovery v5 routing table or the routing table of any other sub protocols.

A node should regularly refresh the information it keeps about its neighbors. We follow section 4.1 of the Kademlia paper to improve efficiency of these refreshes. A node delays `Ping` checks until it has a useful message to send to its neighbor.

When a node discovers some previously unknown node, and the corresponding k-bucket is full, the newly discovered node is put into a replacement cache sorted by time last seen. If a node in the k-bucket fails a liveness check, and the replacement cache for that bucket is non-empty, then that node is replaced by the most recently seen node in the replacement cache.

Consider a node in some k-bucket to be "stale" if it fails to respond to β messages in a row, where β is a system parameter. β may be a function of the number of previous successful liveness checks or of the age of the neighbor. If the k-bucket is not full, and the corresponding replacement cache is empty, then stale nodes should only be flagged and not removed. This ensures that a node who goes offline temporarily does not void its k-buckets.

## Node State

Most networks that use the Portal Wire Protocol will track some additional state about nodes in the network.

### Base Node State

Nodes in the network are expected to maintain a database of information with the following information:

```
node-entry := (node-id, ip, port)
node-id    := uint256
ip         := IPv4 or IPv6 address
port       := UDP port number
```

### Protocol Specific Node State

Sub protocols may define additional node state information which should be tracked in the node state database.  This information will typically be transmitted in the `Ping.payload` and `Pong.payload` fields.


## Algorithms

Here we define a collection of generic algorithms which can be applied to a sub-protocol implementing the wire protocol.


### Lookup

The term lookup refers to the lookup algorithm described in section 2.3 of the Kademlia paper.

A node lookup is the execution of the algorithm to find the `k` closest nodes to some `node-id`.

A content lookup is the execution of the algorithm to find the content with `content-id` or the `k` closest nodes to `content-id`.

A `FindNode` request is used for a node lookup, and a `FindContent` request for a content lookup.

### Joining the Network

We follow the join procedure described in the Kademlia paper.

In order to join the network, a node `u` must know some node `v` who is already participating in the network. Node `u` inserts `v` into the appropriate k-bucket and then sends a `FindNode` request to `v` in order to discover more nodes in the network. Then, node `u` refreshes all k-buckets with distances further than its closest neighbor. To refresh a bucket, a node selects a random node ID in the bucket's range and performs a `FindNode` request with a distance that maps to that ID.

### Finding Nodes

A node's routing table is initially populated by the `FindNode` messages that the node sends when it joins the network.

Following the join phase, a node's k-buckets are generally kept fresh by network traffic. When a node learns of a new contact (through node lookups), it attempts to insert the contact into the appropriate k-bucket. A node keeps track of the last node lookup it performed for each k-bucket, and it will regularly refresh any k-buckets with no recent lookups.

### Finding Content

To find a piece of content for `content-id`, a node performs a content lookup via `FindContent`.

### Storing Content

The concept of content storage is only applicable to sub-protocols that implement persistent storage of data.

Content will get stored by a node when:
- the node receives the content through the `Offer` - `Accept` message flow and the content falls within the node's radius
- the node requests content through the `FindContent` - `Content` message flow and the content falls within the node's radius

The network cannot make guarantees about the storage of particular content. A lazy node may ignore all `Offer` messages. A malicious node may send `Accept` messages and ignore the data transmissions. The `Offer` - `Accept` mechanism is in place to require that nodes explicitly accept some data before another node attempts to transmit that data. The mechanism prevents the unnecessary consumption of bandwidth in the presence of lazy nodes. However, it does not defend against malicious nodes who accept offers for data with no intent to store it.

### Neighborhood Gossip

We use the term *neighborhood gossip* to refer to the process through which content is disseminated to all of the DHT nodes *near* the location in the DHT where the content is located.

The process works as follows:

- A DHT node is offered and receives a piece of content that it is interested in.
- This DHT node checks their routing table for `k` nearby DHT nodes that should also be interested in the content. Those `k` nodes **SHOULD** not include the node that originally provided aforementioned content.
- If the DHT node finds `n` or more DHT nodes interested it selects `n` of these nodes and offers the content to them.
- If fewer than `n` interested nodes are found, it offers the content to as many of them as possible.

The process above should quickly saturate the area of the DHT where the content is located and naturally terminate as more nodes become aware of the content.

The node can use ACCEPT codes received in past responses to make more efficient choices on which neighbors to gossip to.

#### Random Gossip

We use the term *random gossip* to refer to the process through which content is disseminated to a random set DHT nodes.

The process works as follows:
- A DHT node is offered piece of content that is specified to be gossiped via
random gossip.
- The node selects a random node from a random bucket and does this for `n` nodes.
- The node offers the content to the `n` selected nodes.

### POKE Mechanism

When a node in the network is doing a content lookup, it will practically perform a recursive find using the `FindContent` and `Content` messages.
During the course of this recursive find, it may encounter nodes along the search path which do not have the content but for which the `content-id` does fall within their announced radius. These are nodes that should be interested in storing this content unless their radius was recently changed.

If the node doing the lookup successfully retrieves the content from another node, it should send an `Offer` message for that content to those interested nodes. This mechanism is designed to help spread content to nodes that may not yet be aware of it.
