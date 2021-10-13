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

## Content Keys and Content IDs

Content keys are used to request or offer specific content data. As such the content key and content data can be represented as a key:value pair.

Content keys are passed as byte strings to the messages defined in the Portal wire protocol. How they are encoded is defined per content network specification.

Content IDs are derived from the content keys and are used to identify where the content is located in the network. The derivation is defined per content network specification.

## Messages

All messages in the protocol are transmitted using the `TALKREQ` and `TALKRESP` messages from the base [Node Discovery Protocol](https://github.com/ethereum/devp2p/blob/master/discv5/discv5-wire.md#talkreq-request-0x05).

All Portal wire protocol messages have a `message_id` and `encoded_message` that are concatenated to form the payload for either the request field for the `TALKREQ` message or the response field of `TALKRESP` message.

```
payload         := message_id | encoded_message
message_id      := uint8
encoded_message := bytes
```

The `encoded_message` component is the [SSZ](https://github.com/ethereum/consensus-specs/blob/dev/ssz/simple-serialize.md) encoded payload for the message as is indicated by its `message_id`. Each message has its own `sedes` which dictates how it is encoded and decoded.

The SSZ sedes `ByteList` is used to alias `List[uint8, max_length=2048]`.

All messages have a `type` which is either `request` or `response`.

* `request` messages **MUST** be sent using a `TALKREQ`
* `response` messages **MUST** be sent using a `TALKRESP`

### Ping (0x01)

Request message to check if a node is reachable, communicate basic information about our node, and request basic information about the recipient node.

```
message_id := 0x01
type       := request
sedes      := Container(enr_seq: uint64, custom_payload: ByteList)
```

* `enr_seq`: The node's current sequence number of their ENR record.
* `custom_payload`: Custom payload specified per the network.

### Pong (0x02)

Response message to Ping(0x01)

```
message_id := 0x02
type       := response
sedes      := Container(enr_seq: uint64, custom_payload: ByteList)
```

* `enr_seq`: The node's current sequence number of their ENR record.
* `custom_payload`: Custom payload specified per the network.

### Find Nodes (0x03)

Request nodes from the peer's routing table at the given logarithmic distances.  The distance of `0` indicates a request for the peer's own ENR record.

```
message_id := 0x03
type       := request
sedes      := Container(distances: List[uint16, max_length=256])
```

* `distances`: a list of distances for which the node is requesting ENR records for.
    * Each distance **MUST** be within the inclusive range `[0, 256]`
    * Each distance in the list **MUST** be unique.

### Nodes (0x04)

Response message to FindNodes(0x03).

```
message_id := 0x04
type       := response
sedes      := Container(total: uint8, enrs: List[ByteList, max_length=32])
```

* `total`: The total number of `Nodes` response messages being sent.
* `enrs`: List of byte strings, each of which is an RLP encoded ENR record.
    * Individual ENR records **MUST** correspond to one of the requested distances.
    * It is invalid to return multiple ENR records for the same `node_id`.

> Note: If the number of ENR records cannot be encoded into a single message, then they should be sent back using multiple messages, with the `total` field representing the total number of messages that are being sent.

### Find Content (0x05)

Request either the data payload for a specific piece of content on the network, **or** ENR records of nodes that are closer to the requested content.

```
message_id := 0x05
type       := request
sedes      := Container(content_key: ByteList)
```

* `content_key`: The key for the content being requested. The encoding of `content_key` is dependant on the network.

### Found Content (0x06)

Response message to Find Content (0x05).

This message can contain either a uTP connection ID, a list of ENRs or the
requested content.

```
message_id := 0x06
type       := response
sedes      := Union[connection-id: Bytes2, content: ByteList, enrs: List[ByteList, 32]]
```

* `connection_id`: Connection ID to set up a uTP stream to transmit the requested data.
    * Connection ID values **SHOULD** be randomly generated.
* `enrs`: List of byte strings, each of which is an RLP encoded ENR record.
    * Individual ENR records **MUST** be closer to the requested content than the responding node.
    * The set of derived `node_id` values from the ENR records **MUST** be unique.
* `content`: byte string of the requested content.
    * This field **MUST** be used when the requested data can fit in this single response.

If the node does not hold the requested content, and the node does not know of any nodes with eligible ENR values, then the node **MUST** return `enrs` as an empty list.

### Offer (0x07)

Offer a set of content keys that this node has content available for.

```
message_id := 0x07
type       := request
sedes      := Container(content_keys: List[ByteList, max_length=64])
```

* `content_keys`: A list of encoded `content_key` entries. The encoding of each `content_key` is dependant on the network.

### Accept (0x08)

Response message to Offer (0x07).

Signals interest in receiving the offered data from the corresponding Offer message.

```
message_id := 8
type       := response
sedes      := Container(connection_id: Bytes2, content_keys: BitList[max_length=64]]
```

* `connection_id`: Connection ID to set up a uTP stream to transmit the requested data.
    * ConnectionID values **SHOULD** be randomly generated.
* `content_keys`: Signals which content keys are desired.
    * A bit-list corresponding to the offered keys with the bits in the positions of the desired keys set to `1`.

Upon *sending* this message, the requesting node **SHOULD** *listen* for an incoming uTP stream with the generated `connection_id`.

Upon *receiving* this message, the serving node **SHOULD** *initiate* a uTP stream with the received `connection_id`.
