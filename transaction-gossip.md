# Portal Network: Transaction Gossip

> NOTE: This specification is a work in progress.

This document is the specification for the "Transaction Gossip" portion of the portal network.  The network is designed to enable participants to broadcast transactions which can be picked up by miners for inclusion in future blocks.


## Design Requirements

The transaction gossip network is designed with the following requirements.

- Transaction payloads that are being passed around the network are "self validating", meaning that they include both the transaction object and a proof against the ethereum state adequate to validate `sender.balance` and `sender.nonce` values.
- Under normal network conditions, nodes that are interested in observing the full transaction pool will reliably receive the full set of valid transactions currently being gossiped.
- Participants are not required to process the full pool and can control the total percentage of the transaction pool they wish to process.


## Wire Protocol

The Transaction Gossip Network uses the PING/PONG/FINDNODES/FOUNDNODES/OFFER/ACCEPT messages from the [Portal Wire Protocol](./portal-wire-protocol.md).

### Distance Function

The Transaction Gossip Network uses the standard XOR distance function.

### PING payload

```
Ping.custom_payload := ssz_serialize(custom_data)
custom_data         := Container(transaction_radius: uint256)
```

### PONG payload

```
Pong.custom_payload := ssz_serialize(custom_data)
custom_data         := Container(transaction_radius: uint256)
```

## Content Keys

### Pending Transaction

```
content_key  := Container(content_type: uint8, transaction_hash: Bytes32, proof_state_root: Bytes32)
content_type := 0x01
content_id   := transaction_hash
```

The data payload for a transaction comes with an merkle proof of the `transaction.to` account.

```
payload     := Container(proof: Proof, transaction: ByteList)
proof       := TODO
transaction := TODO
```

## Secondary Routing Table

Clients in the Transaction Gossip Network are expected to maintain both the standard routing table and a secondary routing table that is anchored to node radius values.

The secondary routing table is subject to all of the same maintenance and management rules as the primary table.  Any node that is added to the secondary routing table must also satisfy the following validity condition:

```
node.transaction_radius >= distance(node.node_id, self.node_id)
```

The additional validity rule aims to ensure that the table is populated with nodes will have shared interest in mostly the same transactions as us.


## Gossip Algorithm

The gossip mechanism for transactions is designed to allow DHT nodes to control what percentage of the transaction pool they wish to process.

### Radius

We use the term "radius" to refer to the mechanism through which a node may limit how much of the transaction pool they wish to process.  The `radius` is a 256 bit integer.  

A DHT node that wishes to process the full transaction pool would publis a radius value of `2**256-1`. We refer to such a DHT node as a "full radius node".

A DHT node is expected to process transactions that satisfy the condition: `distance(node_id, content_id) <= radius`

Each DHT node includes their current `radius` value in both PING and PONG messages.


### Validation

DHT nodes **should** drop transactions which do not pass the following validation rules


#### 2. Proof valid

The proof must be valid and against a *recent* state root. Individual implementations may choose the boundary for which a proof is considered stale.

> TODO: 8 blocks seems like a good simple starting point

#### 1. Balance and Nonce

The proof **must** show that:

- `transaction.sender.balance >= transaction.value`
- `transaction.sender.nonce >= transaction.nonce`

### Gossip Rules

A DHT node should only be offer'd a transaction that is inside of its radius.

A DHT node should OFFER transactions to all of the DHT nodes present in their secondary routing table (skipping any nodes for whom the transaction is outside of their radius).

A DHT node should only OFFER any individual transaction to a DHT node once.


### Proof Updating

A DHT Node which encounters a transaction with a proof that is outdated **may** update that proof.

Lightweight nodes are encouraged to allocate a small amount of processing power towards this altruistic proof updating as a way to help contribute to the overall health of the network.
