# The Portal Network

## Through the DevP2P lens

Existing Ethereum clients like Geth are built on top of the DevP2P protocol.
The protocol is primarily designed to facilitate the transfer of data between
full nodes.

- Nodes on this network **must** be full nodes.
- The network fundamentally assumes that all nodes have all data.

The design of this network ends up dictating client design.  

- Clients must fully sync the state and history.
- Clients must build their own indices for looking up transactions by hash or blocks by number.

This imposes significant limits on client design.

## Through a different lens.

If we ignore the limitations of the DevP2P network, and instead think about
what clients could look like, here are a few things that come to mind.

- Execution of blocks could be optional.
- State database might only house portions of the state.
- Elimination of sync times and only fetch data lazily as it is needed.
- Reduced CPU/HDD/bandwidth usage

Many of these things aren't feasible or realistic within the context of the
DevP2P network.  They would require fundamental changes to the network design,
many of which would likely reduce the overall security guarantees that the
network provides and that client teams have chosen to prioritize.

## So what is the Portal Network

The Portal Network aims to build the networks that allow us to have a more
diverse set of functionality in our choices for Ethereum clients.  The goal is
not to replace the DevP2P network, but to provide supplimental networks that
enable new functionality that isn't possible within the confines of the DevP2P
network.

- Special purpose networks that "do one thing well".
  - Separate networks for history, state, mempool, etc.
- Move the complexity out of the clients and into the network.
  - Transaction index
  - Block number index
  - Mempool transaction validation
- Ensure that network design is friendly towards resource constrained devices.
  - No assumption of "full nodes"
  - Data Radius mechanic allows nodes to tune their responsibility to match
    their hardware resources.

DevP2P can remain a simple and secure core component of Ethereum
infrastructure, primarily used by clients that are focused on serving the
protocol.  The Portal Network can then focus on delivering functionality that
is focused on use cases of the users of Ethereum.

## What happened to the original JSON-RPC API based Portal Network use case?

The original pitch for the Portal Network was focused on delivering a network
that allowed clients to the network to serve JSON-RPC requests by fetching data
on-demand from the Portal Network.  Recently we've come to understand that this
use case is likely to be difficult based on network latencies, which has forced
us to re-evaluate our roadmap.

## Dogfooding

The JSON-RPC based roadmap and this new roadmap direction are still roughly
equivalent in the designs of our networks, however, they differ in terms of the
client functionality we intend to deliver.  The JSON-RPC based roadmap was a
way to ensure that we were "dogfooding" the network functionality that we were
building. We now need a new approach to dogfooding.

I propose we shift our development focus to the following units of functionality.

- Tracking of the chain head of both consensus and execution chains
- Syncing of recent and full history data (headers/bodies/receipts)
- Syncing and retrieval of the Ethereum state
- Looking up transactions by their hash
- Broadcasting transactions
- EVM execution
