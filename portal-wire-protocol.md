# Portal Wire Protocol

The Portal wire protocol is the default p2p protocol by which Portal nodes communicate.

The different Portal networks **MAY** use this protocol, but they **MUST** remain separated per network.
This is done at the [Node Discovery Protocol v5](https://github.com/ethereum/devp2p/blob/master/discv5/discv5-wire.md#talkreq-request-0x05) layer, by providing a different protocol byte string, per network, in the `TALKREQ` message.

The value for the protocol byte string in the `TALKREQ` message is specified as protocol identifier per network.

Each network using the wire protocol **MUST** specify which messages are supported.

Unsupported messages **SHOULD** receive a `TALKRESP` message with an empty payload.

## Protocol identifiers

All protocol identifiers consist of two bytes. The first byte is "`P`" (`0x50`), to indicate "the Portal network", the second byte is a specific network identifier.

Currently defined protocol identifiers:
- Inclusive range of `0x5000` - `0x5009`: Reserved for future networks or network upgrades
- `0x500A`: State Network
- `0x500B`: History Network
- `0x500C`: Transaction Gossip Network
- `0x500D`: Header Gossip Network
- `0x500E`: Canonical Indices Network
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

#### Ping (0x01)

Request message to check if a node is reachable, communicate basic information about our node, and request basic information about the recipient node.

```
selector     = 0x01
ping         = Container(enr_seq: uint64, custom_payload: ByteList)
```

* `enr_seq`: The node's current sequence number of their ENR record.
* `custom_payload`: Custom payload specified per the network.

#### Pong (0x02)

Response message to Ping(0x01)

```
selector     = 0x02
pong         = Container(enr_seq: uint64, custom_payload: ByteList)
```

* `enr_seq`: The node's current sequence number of their ENR record.
* `custom_payload`: Custom payload specified per the network.

#### Find Nodes (0x03)

Request message to get ENR records from the recipient's routing table at the given logarithmic distances. The distance of `0` indicates a request for the recipient's own ENR record.

```
selector     = 0x03
find_nodes   = Container(distances: List[uint16, max_length=256])
```

* `distances`: a list of distances for which the node is requesting ENR records for.
    * Each distance **MUST** be within the inclusive range `[0, 256]`
    * Each distance in the list **MUST** be unique.

#### Nodes (0x04)

Response message to FindNodes(0x03).

```
selector     = 0x04
nodes        = Container(total: uint8, enrs: List[ByteList, max_length=32])
```

* `total`: The total number of `Nodes` response messages being sent.
* `enrs`: List of byte strings, each of which is an RLP encoded ENR record.
    * Individual ENR records **MUST** correspond to one of the requested distances.
    * It is invalid to return multiple ENR records for the same `node_id`.

> Note: If the number of ENR records cannot be encoded into a single message, then they should be sent back using multiple messages, with the `total` field representing the total number of messages that are being sent.

#### Find Content (0x05)

Request message to get the `content` with `content_key`, **or**, in case the recipient does not have the data, a list of ENR records of nodes that are closer than the recipient is to the requested content.

```
selector     = 0x05
find_content = Container(content_key: ByteList)
```

* `content_key`: The key for the content being requested. The encoding of `content_key` is specified per the network.

#### Content (0x06)

Response message to Find Content (0x05).

This message can contain either a uTP connection ID, a list of ENRs or the
requested content.

```
selector     = 0x06
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

The `Union` defined in the `content` field of the `Content (0x06)` message is defined as below:

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

#### Offer (0x07)

Request message to offer a set of `content_keys` that this node has `content` available for.

```
selector     = 0x07
offer        = Container(content_keys: List[ByteList, max_length=64])
```

* `content_keys`: A list of encoded `content_key` entries. The encoding of each `content_key` is specified per the network.

#### Accept (0x08)

Response message to Offer (0x07).

Signals interest in receiving the offered data from the corresponding Offer message.

```
selector     = 0x08
accept       = Container(connection_id: Bytes2, content_keys: BitList[max_length=64]]
```

* `connection_id`: Connection ID to set up a uTP stream to transmit the requested data.
    * ConnectionID values **SHOULD** be randomly generated.
* `content_keys`: Signals which content keys are desired.
    * A bit-list corresponding to the offered keys with the bits in the positions of the desired keys set to `1`.

Upon *sending* this message, the requesting node **SHOULD** *listen* for an incoming uTP stream with the generated `connection_id`.

Upon *receiving* this message, the serving node **SHOULD** *initiate* a uTP stream with the received `connection_id`.
