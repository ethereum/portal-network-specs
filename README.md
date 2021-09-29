# The Portal Network

## Introduction

The Portal Network is an in progess effort to enable lightweight protocol access to resource constrained devices.  The term *"portal"* is used to indicate that these networks provide a *view* into the protocol but are not critical to the operation of the core Ethereum protocol.

The Portal Network is comprised of multiple peer-to-peer networks which together provide the data and functionality necessary to expose the standard JSON-RPC API.  These networks are specially designed to ensure that clients participating in these networks can do so with minimal expendature of networking bandwidth, CPU, RAM, and HDD resources.

The term "Portal Client" is used to describe a piece of software that participates in these networks and typically exposes the standard JSON-RPC API


## Motivation

The Portal Network is focused on delivering reliable, lightweight, and decentralized access to the Ethereum protocol.

### Prior Work on the "Light Ethereum Subprotocol" (LES)

The term "light client" has historically refered to a client of the existing DevP2P based LES network.  This network is designed using a client/server architecture.  The LES network has a total capacity dictated by the number of "servers" on the network.  In order for this network to scale, the "server" capacity has to increase.  This also means that at any point in time the network has some total capacity which if exceeded will cause service degredation across the network.  Because of this the LES network is unreliable when operating near capacity.


## Architecture

The Portal Network is built upon on the [Discover V5 protocol](https://github.com/ethereum/devp2p/blob/master/discv5/discv5.md) and operates over the UDP transport.

The Discovery v5 protocol allows building custom sub-protocols via the use of the built in TALKREQ and TALKRESP message.

The Portal Network is divided into the following sub-protocols.

- State Network
- History Network
- Transaction Gossip Network
- Header Gossip Network
- Canonical Indices Network

Each of these networks is designed to deliver a specific unit of functionality.  Most portal clients will participate in all of these networks in order to deliver the full JSON-RPC API.  Each network however is designed to be independent of the others, allowing clients the option of only participating in a subset of them if they wish.

All of the sub-protocols in the Portal Network establish their own Kademlia DHT network that is managed independent of the base Discovery V5 protocol Kademlia DHT.


## Design Principles

Each of the Portal Network sub-protocols follows these design principles.

1. Isolation
  - Each network should be able to be run independent of the other networks.  Participation in one network should not require participation in another network.
2. Distribution of Responsibility
  - Normal operation of the network should result in a roughly even spread of responsibility across the individual nodes in the network.
3. Tunable Resource Requirements
  - Individual nodes should be able to control the amount of machine resources (HDD/CPU/RAM) they must expend to be part of the network.

These design principles are aimed at ensuring that participation in the Portal Network is feasible even on resource constrained devices.

## The JSON-RPC API

The following JSON-RPC API endpoints are intended to be supported by the portal network and exposed by portal clients.

TODO

## Bridge Nodes

We use the term "bridge" node to refer to the process by which data enters the Portal Network.  A "bridge" node is a normal node in the Portal Network that is able to bring in new and missing data from some external source and inject it into the Portal Network.  These nodes would not be special in any way from the perspective of the Portal Network.

The planned architecture for bridge nodes is to pull data from the standard JSON-RPC API of a Full Node and "push" this data into their respective networks within the Portal Network.

## Network Functionality

### State Network: Accounts and Contract Storage

The State Network facilitates on-demand retrieval of the Ethereum "state" data.  This includes things like:

- Reading account balances or nonce values
- Retrieving contract code
- Reading contract storage values

The responsibility for storing the underlying "state" data should be evenly distributed across the nodes in the network.  Nodes must be able to choose how much state they want to store.  The data is distributed in a manner that allows nodes to determine the appropriate nodes to query for any individual piece of state data.  When retrieving state data, a node should be able to validate the response using a recent header from the header chain.

The network will be dependent on receiving new and updated state for new blocks. Full "bridge" nodes acting as benevolent state providers would be responsible for bringing in this data from the main network. The network should be able to remain healthy even with a small number of bridge nodes.  As new data enters the network, nodes must be able to validate the data using a recent header from the header chain.

Querying and reading data from the network should be fast enough for human-driven wallet operations, like estimating the gas for a transaction or reading state from a contract.


### History Network: Headers, Blocks, and Receipts

The History Network facilitates on-demand retrieval of the history of the Ethereum chain.  This includes:

- Headers
- Block bodies
- Receipts

The responsibility for storing this data should be evenly distributed across the nodes in the network.  Nodes must be able to choose how much history data they want to store.  The data is distributed in a manner that allows nodes to determine the appropriate nodes to query for any individual piece of history data.  

Participants to this network are assumed to have access to the canonical header chain.

All data retrieved from the history network is addressed by block hash.  Headers retrieved from this network can be validated to match the requested block hash.  Block Bodies and Receipts retrieved from this network can be validated against the corresponding header fields.


### Canonical Indices Network: Transactions by Hash and Blocks by Number

The Canonical Indices Network facilitates access to canonical information about transactions and blocks.  This includes:

- Determining the canonical block within which a transaction was included
- Determining the block hash of the canonical block at a given block number.

We refer to the data that backs these two lookups as "Canonical Indices" as they serve as a type of database index for fast retrieval of this information which would otherwise require prohibitively expensive scanning of all historical blocks.

The responsibility for storing the records that make up these two indices should be evently distributed across the nodes in the network.  Nodes must be able to choose how many records from these indices they wish to store.  The records must be distributed across the network in a manner that allows nodes to determine the appropriate nodes to query for an individual record.

Transaction information returned from this network will need to include a merkle proof against the `Header.transactions_trie` for validation purposes.

Block number information returned from this network will need to include a merkle proof against the header accumulator.


### Transaction Gossip Network: Sending Transactions

The Transaction Gossip Network facilitates broadcasting new transactions for inclusion in a future block.

Nodes in this network must be able to limit how much of the transaction pool they wish to process and gossip.

The goal of the transaction gossip network is to make sure nodes can broadcast transaction such that they are made available to miners for inclusion in a future block.

Transactions which are part of this network's gossip must be able to be validated without access to the Ethereum state. This is accomplished by bundling a proof which includes the account balance and nonce for the transaction sender.

This network is a pure gossip network and does not implement any form of content lookup or retrieval.


### Header Gossip Network: New Blocks

The Header Gossip Network faciliates tracking and following the canonical chain of block headers.

A [double batched merkle log accumulator](./https://ethresear.ch/t/double-batched-merkle-log-accumulator/571) is used to minimize storage overhead while still allowing nodes to verify the historical headers without requiring nodes to store the full history.  The network also exposes functionality to allow new nodes joining the network to acquire a copy of another node's accumulator.


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
- Header Gossip:
    - No current spec
