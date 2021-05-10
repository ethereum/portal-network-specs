# The Portal Network

## Introduction

The "Portal Network" is an in progess effort to enable lightweight protocol access to resource constrained devices.  The term *"portal"* is used to indicate that these networks provide a *view* into the protocol but are not critical to the operation of the core Ethereum protocol.


The Portal Network will be comprised of one or more decentralized peer-to-peer networks which together provide the data and functionality necessary to expose the standard JSON-RPC API.  These networks are being specially designed to ensure that clients participating in these networks can do so with minimal expendature of networking bandwidth, CPU, RAM, and HDD resources.

The term "Portal Client" is used to describe a piece of software that participates in these networks and exposes the standard JSON-RPC API

## Motivation

This effort is motivated by two overlapping goals.

### Full Functionality for Stateless Clients

The core Ethereum protocol is moving towards a "stateless" model of block verification.  Under this model a client will be able to fully verify the execution of a block using a witness.  Such a client would no longer need to keep or maintain any of the Ethereum "state" data.  Such a client is very valuable in the context of the core protocol, as it facilitates a cleaner merge of the Eth1 and Eth2 chains.  

> Additional reading on why stateless is so important to the Eth1/Eth2 merge: https://dankradfeist.de/ethereum/2021/02/14/why-stateless.html)

What is easy to overlook is that such a "stateless" client will be unable to much else without additional infrastructure.  Specifically it would be unable to serve the vast majority of the JSON-RPC apis.  The Portal Network provides this additional infrastructure, allowing stateless clients to also expose the external APIs that support the web3 ecosystem.


### Scalable Lightweight Clients

The term "light client" tends to refer to a client of the existing DevP2P LES network.  This network is designed using a client/server architecture.  The LES network has a total capacity dictated by the number of "servers" on the network.  In order for this network to scale, the "server" capacity has to increase.  This also means that at any point in time the network has some total capacity which if exceeded will cause service degredation across the network.  Because of this the LES network is unreliable when operating near capacity.

The Portal Network aims to solve this problem by designing our networks so that each additional client that joints the network adds additional capacity to the network.  The end result *should* be a network which becomes more robust and powerful as more nodes join the network.

> Additional reading: https://snakecharmers.ethereum.org/the-winding-road-to-functional-light-clients/
> 
> Additional watching: https://www.youtube.com/watch?v=MZxqRs_tLNs


### JSON-RPC API

The following JSON-RPC API endpoints are intended to be supported by the portal network and exposed by portal clients.

TODO

## Network Functionality

### State: Accounts and Contract Storage

TODO

### Chain History: Headers, Blocks, and Receipts

In order to validate requested portal network data, a portal client needs to be able to request headers and validate their inclusion in the canonical header chain. Clients can use validated headers to further validate blocks, uncles, transactions, receipts, and state nodes.

Normal clients will download every block header to construct the canonical chain. This is unreasonable for a "stateless" client. The "double-batched merkle log accumulator" is the mechanism that enables portal clients to achieve this goal, without requiring them to download every canonical header.

When a portal client requests a certain header, the response includes two accumulator proofs. As long as the client maintains an up-to-date view of the chain tip (via the gossip network) it can use the proofs to validate a headers inclusion in the canonical chain. Then, the client can use the header to validate other data retrieved from the portal network.

### Canonical Indices: Transactions by Hash and Blocks by Number

To serve the `eth_getTransactionByHash` and `eth_getBlockByNumber` JSON-RPC API endpoints, clients typically build local indexes as they sync the entire chain. The portal network will need to mimic these indices. This can be acheived by generating unique mappings for transactions and blocks, and then pushing these into to portal network.

Since valid transactions can exist outside of the context of a particular block, we need a mechanism to prove that they were included in a certain block. Likewise, valid blocks can exist as uncles, without proof that they were included in the canonical chain at a certain number. So, a mechanism is required to validate that a given block is canonical at a certain level, and a transaction was included in a canonical block.

In the portal network, the canonical block index is built by mapping block numbers to their respective canonical block hash. The canonical transaction index is built by mapping transaction hashes to their respective canonical block hash and transaction index. These key-value pairs are then pushed into the portal network, similar to other data objects.

### Transaction Sending: Cooperative Transaction Gossip

TODO


## Network Specifications

- [uTP over DiscoveryV5](./discv5-utp.md)
- [State Network](./state-network.md)
    - Scalable gossip for new state data: https://ethresear.ch/t/scalable-gossip-for-state-network/8958/4
- Chain History Network
    - No current spec
    - Prior work: https://notes.ethereum.org/oUJE4ZX2Q6eMOgEMiQPkpQ?view
    - Prior Python proof-of-concept: https://github.com/ethereum/ddht/tree/341e84e9163338556cd48dd2fcfda9eedec3eb45
        - This POC shouldn't be considered representative of the end goal.  It incorperates mechanisms that aren't likely to be apart of the actual implementation, specifically the "advertisement" system which proved to be a big bottleneck, as well as the SSZ merkle root system which was a work-around for large data transfer which we now intend to solve with uTP.
- Transaction Gossip:
    - No current spec
    - Prior work: https://ethresear.ch/t/scalable-transaction-gossip/8660
