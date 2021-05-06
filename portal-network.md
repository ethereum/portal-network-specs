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

The goal of the state network is to make pieces of the state available to light clients before the next block is mined.

Nodes should be able to choose how much state they want to store and share, and the network should provide a way to identify which nodes to query for a wanted portion of state.

Full "bridge" nodes acting as benevolent state providers could selectively push out proofs from the main network to interested light nodes, who could also request more data if needed. For example, a full node could only push leaf proofs and any interested light client would request intermediate leaf-to-root proofs and participate in broadcasting them.

Querying and reading data from the network should be fast, since wallet operations such as estimating needed gas for a transaction might need to retrieve a significant amount of state data and access contract storage (which is stored in a separate trie and inherently unbalanced), resulting in many requests for different pieces of state.

### Chain History: Headers, Blocks, and Receipts

TODO

### Canonical Indices: Transactions by Hash and Blocks by Hash

TODO

### Transaction Sending: Cooperative Transaction Gossip

The goal of the transaction gossip network is to make sure all new transactions are validated and broadcast to the miners so that they can be included in a block.

Stateless clients should be able to declare where they stand on the spectrum of "how many transactions do I want to process out of the whole mempool", based on the amount of resources they have and their role in the network, and the network should let clients filter and select destination nodes based on which transactions they are interested in.

Stateless transaction validation involves checking accounts' balances and nonces, so transactions should be broadcast with those proofs included.

Transaction broadcasting involves pushing new transactions to the "center" of the network, where the miners are.  Note how this is different from the needs of the state network, where pieces of the state need to be "pushed out" from the full nodes to the light ones who will store it so they can participate in achieving or strenghening consensus.  This means that the "lightest" clients would not have to know about all (or any) transactions, they just need to make sure their own transactions are validated and sent to the miners as quickly as possible.

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
