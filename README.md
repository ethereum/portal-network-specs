# The Portal Network

>  This specification is a work-in-progress and should be considered preliminary.

## Introduction

The Portal Network is an in progress effort to enable lightweight protocol access by resource constrained devices.  The term *"portal"* is used to indicate that these networks provide a *view* into the protocol but are not critical to the operation of the core Ethereum protocol.

The Portal Network is comprised of multiple peer-to-peer networks which together provide the data and functionality necessary to expose the standard [JSON-RPC API](https://eth.wiki/json-rpc/API).  These networks are specially designed to ensure that clients participating in these networks can do so with minimal expenditure of networking bandwidth, CPU, RAM, and HDD resources.

The term 'Portal Client' describes a piece of software which participates in these networks. Portal Clients typically expose the standard JSON-RPC API.


## Motivation

The Portal Network is focused on delivering reliable, lightweight, and decentralized access to the Ethereum protocol.

### Prior Work on the "Light Ethereum Subprotocol" (LES)

The term "light client" has historically referred to a client of the existing [DevP2P](https://github.com/ethereum/devp2p/blob/master/rlpx.md) based [LES](https://github.com/ethereum/devp2p/blob/master/caps/les.md) network.  This network is designed using a client/server architecture.  The LES network has a total capacity dictated by the number of "servers" on the network.  In order for this network to scale, the "server" capacity has to increase.  This also means that at any point in time the network has some total capacity which if exceeded will cause service degradation across the network.  Because of this the LES network is unreliable when operating near capacity.


## Architecture

The Portal Network is built upon the [Discover V5 protocol](https://github.com/ethereum/devp2p/blob/master/discv5/discv5.md) and operates over the UDP transport.

The Discovery v5 protocol allows building custom sub-protocols via the use of the built in TALKREQ and TALKRESP message. All sub-protocols use the [Portal Wire Protocol](./portal-wire-protocol.md) which uses the TALKREQ and TALKRESP messages as transport. This wire protocol allows for quick development of the network layer of any new sub-protocol.

The Portal Network is divided into the following sub-protocols.

- Execution Head-MPT State Network
- Execution State Network
- Execution Legacy History Network
- Beacon Chain Network
- Execution Canonical Transaction Index Network (preliminary)
- Execution Verkle State Network (preliminary)
- Execution Transaction Gossip Network (preliminary)

Each of these sub-protocols is designed to deliver a specific unit of functionality.  Most Portal clients will participate in all of these sub-protocols in order to deliver the full JSON-RPC API.  Each sub-protocol however is designed to be independent of the others, allowing clients the option of only participating in a subset of them if they wish.

All of the sub-protocols in the Portal Network establish their own overlay DHT that is managed independent of the base Discovery V5 DHT.


## Terminology

The term "sub-protocol" is used to denote an individual protocol within the Portal Network.

The term "network" is used contextually to refer to **either** the overall set of multiple protocols that comprise the Portal Network or an individual sub-protocol within the Portal Network.



## Design Principles

Each of the Portal Network sub-protocols follows these design principles.

1. Isolation
  - Participation in one network should not require participation in another network.
2. Distribution of Responsibility
  - Normal operation of the network should result in a roughly even spread of responsibility across the individual nodes in the network.
3. Tunable Resource Requirements
  - Individual nodes should be able to control the amount of machine resources (HDD/CPU/RAM) they provide to the network

These design principles are aimed at ensuring that participation in the Portal Network is feasible even on resource constrained devices.

## The JSON-RPC API

The following JSON-RPC API endpoints are directly supported by the Portal Network and exposed by Portal clients.

- `eth_getBlockByHash`
- `eth_getBlockByNumber`
- `eth_getBlockTransactionCountByHash`
- `eth_getBlockTransactionCountByNumber`
- `eth_getUncleCountByBlockHash`
- `eth_getUncleCountByBlockNumber`
- `eth_blockNumber`
- `eth_call`
- `eth_estimateGas`
- `eth_getBalance`
- `eth_getStorageAt`
- `eth_getTransactionCount`
- `eth_getCode`
- `eth_sendRawTransaction`
- `eth_getTransactionByHash`
- `eth_getTransactionByBlockHashAndIndex`
- `eth_getTransactionByBlockNumberAndIndex`
- `eth_getTransactionReceipt`

In addition to these endpoints, the following endpoints can be exposed by Portal clients through the data available through the Portal Network.

- `eth_syncing`

The following endpoints can be exposed by Portal clients as they require no access to execution layer data.

- `eth_protocolVersion`
- `eth_chainId`
- `eth_coinbase`
- `eth_accounts`
- `eth_gasPrice`
- `eth_feeHistory`
- `eth_newFilter`
  - TODO: explain complexity.
- `eth_newBlockFilter`
- `eth_newPendingTransactionFilter`
- `eth_uninstallFilter`
- `eth_getFilterChanges`
- `eth_getFilterLogs`
- `eth_getLogs`
  - TODO: explain complexity
- `eth_mining`
- `eth_hashrate`
- `eth_getWork`
- `eth_submitWork`
- `eth_submitHashrate`
- `eth_sign`
- `eth_signTransaction`

[JSON-RPC Specs](https://playground.open-rpc.org/?schemaUrl=https://raw.githubusercontent.com/ethereum/portal-network-specs/assembled-spec/jsonrpc/openrpc.json&uiSchema%5BappBar%5D%5Bui:splitView%5D=false&uiSchema%5BappBar%5D%5Bui:input%5D=false&uiSchema%5BappBar%5D%5Bui:examplesDropdown%5D=false)

## Bridge Nodes

The term "bridge node" refers to Portal clients which, in addition to participating in the sub-protocols, also inject data into the Portal Network. Any client with valid data may participate as a bridge node. From the perspective of the protocols underlying the Portal Network there is nothing special about bridge nodes.

The planned architecture for bridge nodes is to pull data from the standard JSON-RPC API of a Full Node and "push" this data into their respective networks within the Portal Network.

## Network Functionality

### State Network: Accounts and Contract Storage

The State Network facilitates on-demand retrieval of the Ethereum "state" data.  This includes:

- Reading account balances or nonce values
- Retrieving contract code
- Reading contract storage values

The responsibility for storing the underlying "state" data should be evenly distributed across the nodes in the network.  Nodes must be able to choose how much state they want to store.  The data is distributed in a manner that allows nodes to determine the appropriate nodes to query for any individual piece of state data.  When retrieving state data, a node should be able to validate the response using a recent header from the header chain.

The network will be dependent on receiving new and updated state for new blocks. Full "bridge" nodes acting as benevolent state providers are responsible for bringing in this data from the main network. The network should be able to remain healthy even with a small number of bridge nodes.  As new data enters the network, nodes are able to validate the data using a recent header from the header chain.

Querying and reading data from the network should be fast enough for human-driven wallet operations, like estimating the gas for a transaction or reading state from a contract.

### Legacy History Network: Headers, Blocks, and Receipts

The Legacy History Network facilitates on-demand retrieval of the history of the Ethereum chain.  This includes:

- Headers
- Block bodies
- Receipts

The responsibility for storing this data should be evenly distributed across the nodes in the network.  Nodes must be able to choose how much history data they want to store.  The data is distributed in a manner that allows nodes to determine the appropriate nodes to query for any individual piece of history data.  

Participants in this network are assumed to have access to the canonical header chain.

All data retrieved from the history network is addressed by block hash.  Headers retrieved from this network can be validated to match the requested block hash.  Block Bodies and Receipts retrieved from this network can be validated against the corresponding header fields.

All data retrieved from the history network can be immediately verified by the requesting node. For block headers, the requesting node always knows the expected hash of the requested data and can reject responses with an incorrect hash.  For block bodies and receipts, the requesting node is expected to have the corresponding header and can reject responses that do not validate against the corresponding header fields.


### Canonical Transaction Index Network: Transactions by Hash

The Canonical Transaction Index Network facilitates retrieval of individual transactions by their hash.

The responsibility for storing the records that make up this should be evenly distributed across the nodes in the network.  Nodes must be able to choose how many records from this index they wish to store.  The records must be distributed across the network in a manner that allows nodes to determine the appropriate nodes to query for an individual record.

Transaction information returned from this network includes a merkle proof against the `Header.transactions_trie` for validation purposes.


### Transaction Gossip Network: Sending Transactions

The Transaction Gossip Network facilitates broadcasting new transactions for inclusion in a future block.

Nodes in this network must be able to limit how much of the transaction pool they wish to process and gossip.

The goal of the transaction gossip network is to make sure nodes can broadcast transaction such that they are made available to miners for inclusion in a future block.

Transactions which are part of this network's gossip are able to be validated without access to the Ethereum state. This is accomplished by bundling a proof which includes the account balance and nonce for the transaction sender.  This validation is required to prevent DOS attacks.

This network is a pure gossip network and does not implement any form of content lookup or retrieval.


## Network Specifications

- [Portal Wire Protocol](./portal-wire-protocol.md)
- [uTP over DiscoveryV5](./utp/discv5-utp.md)
- [State Network](./legacy/state/state-network.md)
    - Prior work: https://ethresear.ch/t/scalable-gossip-for-state-network/8958/4
- [Legacy History Network](./legacy/history/history-network.md)
    - Prior work: https://notes.ethereum.org/oUJE4ZX2Q6eMOgEMiQPkpQ?view
    - Prior Python proof-of-concept: https://github.com/ethereum/ddht/tree/341e84e9163338556cd48dd2fcfda9eedec3eb45
        - This POC should NOT be considered representative of the end goal.  It incorporates mechanisms that aren't likely to be apart of the actual implementation, specifically the "advertisement" system which proved to be a big bottleneck, as well as the SSZ merkle root system which was a workaround for large data transfer which we now intend to solve with uTP.
- [Beacon Chain Network](./legacy/beacon-chain/beacon-network.md)
- [Canonical Transaction Index Network](./legacy/canonical-transaction-index/canonical-transaction-index-network.md)
    - Spec is preliminary.
    - Network design borrows heavily from history network
- [Transaction Gossip Network](./legacy/transaction-gossip/transaction-gossip.md)
    - Spec is preliminary
    - Prior work: https://ethresear.ch/t/scalable-transaction-gossip/8660
- [Verkle State Network](./legacy/verkle/verkle-state-network.md)
    - Spec is preliminary
    - Prior work: https://ethresear.ch/t/portal-network-verkle/19339
