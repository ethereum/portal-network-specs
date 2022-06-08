# Portal Wire Protocol

The Portal wire protocol is the default p2p protocol by which Portal nodes communicate.

The different sub-protocols within the Portal network **MAY** use this wire protocol, but they **MUST** remain separated per network.

This is done at the [Node Discovery Protocol v5](https://github.com/ethereum/devp2p/blob/master/discv5/discv5-wire.md#talkreq-request-0x05) layer, by providing a different protocol byte string, per protocol, in the `TALKREQ` message.

The value for the protocol byte string in the `TALKREQ` message is specified as protocol identifier per network.

Each network using the wire protocol **MUST** specify which messages are supported.

Unsupported messages **SHOULD** receive a `TALKRESP` message with an empty payload.

## Protocol identifiers

All protocol identifiers consist of two bytes. The first byte is "`P`" (`0x50`), to indicate "the Portal network", the second byte is a specific network identifier.

Currently defined protocol identifiers:
- Inclusive range of `0x5000` - `0x5009`: Reserved for future networks or network upgrades
- `0x500A`: Execution State Network
- `0x500B`: Execution History Network
- `0x500C`: Transaction Gossip Network
- `0x500D`: Execution Header Gossip Network
- `0x500E`: Execution Canonical Indices Network
- `0x501A`: gossip channel: bc-light-client-snapshot
- `0x501B`: gossip channel: bc-light-client-update
- `0x501C`: DHT network: beacon-state

## Content Keys and Content IDs

Content keys are used to request or offer specific content data. As such the content key and content data can be represented as a key:value pair.

Content keys are passed as byte strings to the messages defined in the Portal wire protocol. How they are encoded is defined per content network specification.

Content IDs are derived from the content keys and are used to identify where the content is located in the network. The derivation is defined per content network specification.

## Request - Response Messages

The messages in the protocol are transmitted using the `TALKREQ` and `TALKRESP` messages from the base [Node Discovery Protocol](https://github.com/ethereum/devp2p/blob/master/discv5/discv5-wire.md#talkreq-request-0x05).

All messages in the protocol have a request-response interaction:
* Request messages **MUST** be sent using a `TALKREQ` message.
* Response messages **MUST** be sent using the corresponding `TALKRESP` message.

All messages are encoded as an [SSZ Union](https://github.com/ethereum/consensus-specs/blob/dev/ssz/simple-serialize.md#union) type.

```
message = Union[ping, pong, find_nodes, nodes, find_content, content, offer, accept]
serialized_message = serialize(message)
```

The `serialized_message` is the payload passed to the `request` field of the `TALKREQ` message or the `reponse` field of the `TALKRESP` message.

The type values for the `Union` are the SSZ Containers specified per message type.

The transmission of `content` data that is too large to fit a single packet is done over [uTP](./discv5-utp.md).

### Aliases

For convenience we alias:
- `ByteList` to `List[uint8, max_length=2048]`

### Message Types

#### Ping (0x00)

Request message to check if a node is reachable, communicate basic information about our node, and request basic information about the recipient node.

```
selector     = 0x00
ping         = Container(enr_seq: uint64, custom_payload: ByteList)
```

* `enr_seq`: The node's current sequence number of their ENR record.
* `custom_payload`: Custom payload specified per the network.

#### Pong (0x01)

Response message to Ping(0x00)

```
selector     = 0x01
pong         = Container(enr_seq: uint64, custom_payload: ByteList)
```

* `enr_seq`: The node's current sequence number of their ENR record.
* `custom_payload`: Custom payload specified per the network.

#### Find Nodes (0x02)

Request message to get ENR records from the recipient's routing table at the given logarithmic distances. The distance of `0` indicates a request for the recipient's own ENR record.

```
selector     = 0x02
find_nodes   = Container(distances: List[uint16, max_length=256])
```

* `distances`: a list of distances for which the node is requesting ENR records for.
    * Each distance **MUST** be within the inclusive range `[0, 256]`
    * Each distance in the list **MUST** be unique.

#### Nodes (0x03)

Response message to FindNodes(0x02).

```
selector     = 0x03
nodes        = Container(total: uint8, enrs: List[ByteList, max_length=32])
```

* `total`: The total number of `Nodes` response messages being sent.
* `enrs`: List of byte strings, each of which is an RLP encoded ENR record.
    * Individual ENR records **MUST** correspond to one of the requested distances.
    * It is invalid to return multiple ENR records for the same `node_id`.

> Note: If the number of ENR records cannot be encoded into a single message, then they should be sent back using multiple messages, with the `total` field representing the total number of messages that are being sent.

#### Find Content (0x04)

Request message to get the `content` with `content_key`, **or**, in case the recipient does not have the data, a list of ENR records of nodes that are closer than the recipient is to the requested content.

```
selector     = 0x04
find_content = Container(content_key: ByteList)
```

* `content_key`: The key for the content being requested. The encoding of `content_key` is specified per the network.

#### Content (0x05)

Response message to Find Content (0x04).

This message can contain either a uTP connection ID, a list of ENRs or the
requested content.

```
selector     = 0x05
content      = Union[connection_id: Bytes2, content: ByteList, enrs: List[ByteList, 32]]
```

* `connection_id`: Connection ID to set up a uTP stream to transmit the requested data.
    * Connection ID values **SHOULD** be randomly generated.
*  `content`: byte string of the requested content.
    * This field **MUST** be used when the requested data can fit in this single response.
* `enrs`: List of byte strings, each of which is an RLP encoded ENR record.
    * Individual ENR records **MUST** be closer to the requested content than the responding node.
    * The set of derived `node_id` values from the ENR records **MUST** be unique.

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
ssz-type = ByteList
```

**`enrs`**
```
selector = 0x02
ssz-type = List[ByteList, 32]
```

#### Offer (0x06)

Request message to offer a set of `content_keys` that this node has `content` available for.

```
selector     = 0x06
offer        = Container(content_keys: List[ByteList, max_length=64])
```

* `content_keys`: A list of encoded `content_key` entries. The encoding of each `content_key` is specified per the network.

#### Accept (0x07)

Response message to Offer (0x06).

Signals interest in receiving the offered data from the corresponding Offer message.

```
selector     = 0x07
accept       = Container(connection_id: Bytes2, content_keys: BitList[max_length=64]]
```

* `connection_id`: Connection ID to set up a uTP stream to transmit the requested data.
    * ConnectionID values **SHOULD** be randomly generated.
* `content_keys`: Signals which content keys are desired.
    * A bit-list corresponding to the offered keys with the bits in the positions of the desired keys set to `1`.

Upon *sending* this message, the requesting node **SHOULD** *listen* for an incoming uTP stream with the generated `connection_id`.

Upon *receiving* this message, the serving node **SHOULD** *initiate* a uTP stream with the received `connection_id`.

### Test Vectors

A collection of test vectors for this specification can be found in the
[Portal wire test vectors](./portal-wire-test-vectors.md) document.

## Algorithms

Here we define a collection of generic algorithms which can be applied to sub-protocol implementing the wire protocol.


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

The concept of content storage is only applicable to sub-protocols that implement persistant storage of data.

Content will get stored by a node when:
- the node receives the content through the `Offer` - `Accept` message flow and the content falls within the node's radius
- the node requests content through the `FindContent` - `Content` message flow and the content falls within the node's radius

The network cannot make guarantees about the storage of particular content. A lazy node may ignore all `Offer` messages. A malicious node may send `Accept` messages and ignore the data transmissions. The `Offer` - `Accept` mechanism is in place to require that nodes explicitly accept some data before another node attempts to transmit that data. The mechanism prevents the unnecessary consumption of bandwidth in the presence of lazy nodes. However, it does not defend against malicious nodes who accept offers for data with no intent to store it.

### Neighborhood Gossip

We use the term *neighborhood gossip* to refer to the process through which content is disseminated to all of the DHT nodes *near* the location in the DHT where the content is located.

The process works as follows:

- A DHT node is offered and receives a piece of content that it is interested in.
- This DHT node checks their routing table for `k` nearby DHT nodes that should also be interested in the content.
- If the DHT node finds `n` or more DHT nodes interested it selects `n` of these nodes and offers the content to them.
- If the DHT node finds less than `n` DHT nodes interested, it launches a node lookup with target `content-id` and it
offers the content to maximum `n` of the newly discovered nodes.

The process above should quickly saturate the area of the DHT where the content is located and naturally terminate as more nodes become aware of the content.

### POKE Mechanism

When a node in the network is doing a content lookup, it will practically perform a recursive find using the `FindContent` and `Content` messages.
During the course of this recursive find, it may encounter nodes along the search path which do not have the content but for which the `content-id` does fall within their announced radius. These are nodes that should be interested in storing this content unless their radius was recently changed.

If the node doing the lookup successfully retrieves the content from another node, it should send an `Offer` message for that content to those interested nodes. This mechanism is designed to help spread content to nodes that may not yet be aware of it.
