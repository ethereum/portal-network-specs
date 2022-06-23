# Execution Header Gossip Network

This document is the specification for the sub-protocol that facilitates transmission of new headers from the tip of the chain to all nodes in the network.

## Design Requirements

The header gossip network functionality has been designed around the following requirements.

- A DHT node can reliably receive the headers for new blocks via the gossip mechanism in a timely manner.

## Wire Protocol

The [Portal wire protocol](./portal-wire-protocol.md) is used as wire protocol for the transaction gossip network.

As specified in the [Protocol identifiers](./portal-wire-protocol.md#protocol-identifiers) section of the Portal wire protocol, the `protocol` field in the `TALKREQ` message **MUST** contain the value of `0x500D`.

The network uses the PING/PONG/FINDNODES/FOUNDNODES/FINDCONTENT/FOUNDCONTENT/OFFER/ACCEPT messages from the [Portal Wire Protocol](./portal-wire-protocol.md).

### Distance Function

The network uses the standard XOR distance function.

### PING payload

```
Ping.custom_payload := ssz_serialize(custom_data)
custom_data         := Container(fork_id: Bytes32, head_hash: Bytes32, head_td: uint256)
```

### PONG payload

```
Pong.custom_payload := ssz_serialize(custom_data)
custom_data         := Container(fork_id: Bytes32, head_hash: Bytes32, head_td: uint256)
```

## Content Keys

### New Block Header


```
content_key  := Container(content_type: uint8, block_hash: Bytes32, block_number: uint256)
content_type := 0x00
content_id   := block_hash
```

TODO: block validation and wire serialization

## Gossip

The gossip protocol for the header network is designed to quickly spread new headers around to all nodes in the network.

Upon receiving a new block header via OFFER/ACCEPT a node should first check the validity of the header.

Headers that pass the validity check should be propagated to `LOG2(num_entries_in_routing_table)` random nodes from the routing table via OFFER/ACCEPT.
