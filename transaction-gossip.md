# Portal Network: Transaction Gossip Network

This document is the specifcation for the "Transaction Gossip" portion of the portal network.  The network is designed to enable participants to broadcast transactions which can be picked up by miners for inclusion in future blocks.

## Unresolved Issues

### Content Key and Content ID

At present, the `content-id` derivation for a transaction is simply its transaction hash. One option we may want to consider is inclusion of the `proof_state_root` in the derivation of `content-id` which would mean that the same transaction could shift locations around the network as its proof is updated.  This increases the DOS vector since someone could publish many copies of the same transaction anchored to different state roots and all of them would be valid.

The *benefit* of such a scheme is that the location of a transaction would shift as its proof gets updated.  This would be a natural mechanism to address the issue of reliable delivery of transactions to full width nodes.  Each time the proof gets updated, the transaction will land in a new part of the DHT and have another chance to be picked up by a full width node.

### DOS Mitigation

One DOS vector that results from allowing nodes to only process a portion of the transaction pool is that nodes lose some ability to remove duplicate transactions from the overall pool.  In ideal situations, two transactions from the same sender with the same `nonce` should result in one of those transactions being discarded.  However, since some of our nodes will only process a portion of the pool, if there are two such transactions and a node only has visibility into one of them, they will not have enough information to properly discard one of the duplicates.

As transactions flow towards nodes with higher radius values, these duplicates will eventually be discarded as they reach nodes with broader visibility into the full transaction pool.

The ideal solution would be a mechanism through which low radius nodes would be able to assist with mitigating this type of DOS attack.

### Reliable Delivery to Full Radius Nodes

The current gossip design does not provide reliable guarantees that transactions broadcast by low radius nodes will successfully be gossiped to full radius nodes.

## Design

The transaction gossip network is designed with the following requirements.

- Participants who are interested in observing the full transaction pool are able to gain visibility into the full set of valid pending transactions
- Participants are not required to process the full pool and can control the total percentage of the transaction pool they wish to process
- Participants can check transaction validity without access to the full ethereum state.


## Wire Protocol

The transaction gossip network uses the PING/PONG/FINDNODES/FOUNDNODES/OFFER/ACCEPT messages from the generic [overlay protocol](./TODO).

### Distance Function

TODO

### PING payload

TODO: radius

### PONG payload

TODO: radius

## Content Keys

### Pending Transaction

```
content_key  := Container(content_type: uint8, transaction_hash: Bytes32, proof_state_root: Bytes32)
content_type := 0xTODO
content_id   := transaction_hash
```

The data payload for a transaction comes with an merkle proof of the `transaction.to` account.

```
payload     := Container(proof: Proof, transaction: ByteList)
proof       := TODO
transaction := TODO
```


## Gossip Algorithm

The gossip mechanism for transactions is designed to allow nodes to decide how much of the transaction pool they wish to process.

### Radius

All DHT nodes in the network will maintain a `radius` which communicates how much of the transaction pool they process.  This value is a 256 bit integer.  A DHT node is expected to process transactions for which `distance(node_id, content_id) <= radius`.

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

Nodes should OFFER transactions to the DHT nodes in their routing table.  A DHT node should only be offer'd a transaction that is inside of its radius.

### Proof Updating

A DHT Node which encounters a transaction with a proof that is outdated **may** update that proof.
