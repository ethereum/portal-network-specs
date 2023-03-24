## Understanding the Portal Network

One of the best framings for understanding the Portal Network is to focus on
the problems it aims to solve.

## Decentralization is important

One primary constraint that we choose to operate within is decentralization.  Most of the problems we will explore here could be solved in a much simpler manner with centralized solutions.  Centralization comes with inherant failure modes that we consider unnacceptable and thus, we have chosen to constrain our solution space to public and permissionless decentralized protocols.

The primary thing we want to avoid with centralization is single points of
failure.  We want a system that is difficult for even state level actors to
shut down and any point of centralization tends to also be a weak point.

## First Principles and Execution Clients

Execution clients in Ethereum are pieces of software that process new blocks as
they are added to the chain.  This involves executing the EVM which transitions
the state from the previous block's state root to the newly computed state root
that results after executing all of the transactions from that block.

The DevP2P network is the decentralized protocol that Execution clients operate
on.  This network is designed to facilitate the transfer of data between "full
nodes" as well as allowing new nodes that join the network to sync the chain
history and state to become a full node.

Syncing nodes impose a burden on the existing full nodes within the network,
downloading hundreds of gigabytes of history and state data to become a full
node.  The main functionality that DevP2P exposes to allow syncing is:

- Requesting batches of block headers by block number or hash
- Requesting batches of block bodies by block number or hash
- Requesting state data via the `SNAP` protocol to build a full recent snapshot of the state.

Once a node in this network has fully synced they become a full node.  As a
full node, the primary network functionality from DevP2P is:

- Gossip of latest block headers and bodies
- Gossip of transactions that are part of the global mempool.

In order for the DevP2P network to be "healthy" it must have a sufficient
number of "full nodes" that are serving this data.  The protocol has nothing to
actually provide any guarantees that nodes within the network are fulfilling
these requirements.  The primary security mechanism for the network is that it
is comprised primarily of `geth` nodes and the team that develops the Geth
client has written their client to behave responsibly within this network.

This means that one fundamental requirement of being part of the DevP2P network
as an Ethereum client is that you must be able to operate as a "full node".
This means the following functionality.

- Ability to sync full history
- Ability to sync full state
- Ability to remain online to keep history and state synced.
- Full chain history (headers, bodies, receipts)
- Full latest state
  - block execution required to keep state up-to-date
  - required by transaction pool for validation of pending transactions.

These requirements dictate hardware and network minimums that roughly work out to:

- 1 TB of bandwidth per month
- 8GB+ of RAM
- 1 TB of *fast* disk (SSD)
- Being consistently online

> these requirements grow over time with no formal bounds.

The result is that Ethereum nodes are prohibitivly hard to run and thus,
accessing Ethereum through an Ethereum node that you run yourself has a very
high barrier to entry.


## What do we want?

With an understanding of current Execution clients and the DevP2P network they
participate in, we get a clear picture of the current status quo and some of
the constraints that it places on client design.  We now want to look at what
kind of things we would like to change about this.

- Reduce bandwidth usage.
- Reduce HDD requirements.
- Reduce CPU requirements.
- Reduce RAM requirements.

All of these effectively fall into the same thing, which is reducing the
hardware and bandwidth requirements needed to run a client.


## Server/Client approach has failed.

The LES protocol has been a long standing attempt to provide lightweight
protocol access.  LES is a client/server oriented protocol, with all of the
lightweight nodes relying on the full nodes of the network to provide them with
data.  This design as not delivered results, due to there not being enough
nodes serving the data to adequately serve the set of clients requesting it.
The result is an unreliable experience for the lightweight nodes of this
network.

This failing of the client/server architecture is somewhat fundamental, and
will always happen in an enviroment where the number of clients exceeds the
capacity offered by the serving nodes.

One "solution" that might be posed here, is for all Ethereum nodes to be light
servers by default.  At present, serving light client data is an opt-in
process.  If it was instead shifted to be an opt-out process, there would
likely be a significant spike in capacity in this network.  However, this
capacity would still be limited by the number of full nodes in the network, and
it seems reasonable to expect the same outcome to eventually occur, with the
demand for data exceeding the serving capacity offered by the network.

## Towards a viable solution

Looking at the main `ETH` DevP2P protocol and the `LES` protocol, we can see
something that don't work.

- Client/Server fails when client demand outpaces server capacity.
- "Full Nodes only" fails because it imposes prohibitively high hardware and
  bandwidth minimums.

This means that we need a different solution and more specifically, we need to
have a clear definition of the problems we are solving.  At a high level, we
need to accomplish the following.


- No dependency on Full Nodes.
- Individually tunable resource requirements
- Support for known retrieval patterns


### Removing "Full Nodes"

We intentionally move away from the network requiring any individual node to be
a "full node".  Our design instead focuses on dividing the data up across the
nodes of the network such that individual nodes are only expected to store a
small portion of the data and such that individual nodes have control over how
much data they store.

Our networks are all Distributed Hash Tables which gives them the nice property
of having a "topology" onto which we can map the data.  Nodes in the network
are automatically evenly distributed across the 256 bit address space.  This
means that we can apply a similar mapping to the data to evenly map it to the
same address space, which then gives us a simple mechanism to distribute
responsibility for data storage evenly across the different nodes in the
network.

