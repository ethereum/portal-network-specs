# Beam Sync

## Intro

Beam Sync is a new strategy to transition from an empty client node to a full-state, fully-validating
node on the network. It borrows heavily from the current "Fast Sync" approach.

#### Fast Sync

This writeup assumes familiarity with Fast Sync and supporting devp2p protocols like `GetNodeData`.

#### Beam Sync Benefits

Beam Sync provides several important benefits, to both the syncing node, and the broader network health.
For example:

- The "Fast" syncing experience is very slow, taking days before any queries
  or validation can be done on the new node. Beam Sync has the promise of syncing to a useable node in minutes.
- Fast Sync nodes are pure leechers on the network. Beam Sync nodes are very effective at seeding
  data to other Beam-syncing nodes.
- Fast Sync gets more likely to fault as total state size grows. Beam Sync gets more likely to fault
  as state reads per block grows.

#### Beam Sync Approach

Roughly, the idea is for a client to skip to the head of the chain (like Fast Sync). Unlike
Fast Sync, the block starts executing immediately, collecting *only* the state data needed
to execute & verify the block. Crucially, a background process collects data that is not
being read by any block. When this background process is complete, then all of Beam Sync is
complete, and the node transitions to Full Sync.

## How to Beam Sync

There are many possible approaches to Beam Sync. The plan is to evolve Beam Sync through three stages:

- v0: Use existing Fast Sync protocols; works on mainnet today
- v1: Add new devp2p protocols, to optionally accelerate Beam Sync
- v2: Add consensus-sensitive witness proofs to block headers, to enable validation of witnesses, and enforce generation

This document will focus on v0.

### Overview

See the path from starting with an empty node to transitioning to a Full Sync:

![Flow chart](https://i.postimg.cc/3x2qtnGL/Flow-chart-v0-2.png)

### Data Faults

When executing the EVM and collecting data just-in-time (JIT-data), the client can detect that some data is either 1) proven to belong to the state root of the previous header, or 2) created during a local execution of the block. If neither of those is true, then a data fault is generated. The fault must describe the hash of the trie node that's missing. The fault can optionally contain the account, storage, or bytecode lookup that triggered the fault. (This will be useful in v1+ of Beam Sync)

### State Retrieval Performance

Naively, when handling a data fault, each `GetNodeData` request can only contain a single trie node. Starting from the empty trie, you can download the root node, but you can't download any other nodes on the path to the account you care about yet, because they are all hash-indexed. The hash of the child is in the body of the parent. So, proving the balance of a single account with an empty trie takes as many requests as there are levels to the trie (say ~7 in mainnet, currently). 

So performance is highly sensitive to latency: round-trip time to your best peer is the dominating factor of how quickly you can execute the EVM with JIT data.

### Lag

It can take longer than a block time to collect all the state needed for a block. So as new blocks arrive,
the currently executing block can fall further and further behind the tip. Clients typically
only serve state for recent blocks, configured differently for different clients. A
common number is ~100 blocks of state retained. If you fall behind this, then missing state
may no longer be available to you. This can leave you indefinitely stuck, so when we
lag far enough behind, we pivot.

### Pivoting

Pivoting skips executing the current blocks, and chooses the tip block again. It will
typically increase the missing state that must be backfilled. It is quite likely that Beam Sync
v0 will require a few pivots before it exits. As it progresses, and stores more state, pivoting gets less likely.
v1 and v2 should be fast enough that pivoting is just a failsafe against "attack blocks" with
intentionally gigantic witnesses.

### Optimizations

A naive implementation of Beam Sync, given that there are on the order of 4k trie nodes read per mainnet block, and a good round-trip time is ~100ms, it would take 400s to collect all the required data to execute a single block. With ~15-second block times, this is clearly a problem.

So while optimizations are not *technically* required, they are necessary in practice to avoid getting stuck in a loop of pivots. A pivot loop would mean never catching up to complete Full Sync.

Below are some optimizations that Trinity has found effective. You may notice the theme that they all provide ways to look up more data in parallel. We would much rather be limited by total peer bandwidth across all connected peers, rather than limited by the round-trip latency of a single peer.

#### Optimization 1: Address Batching

Before starting EVM execution, we can identify several key addresses that will be needed during the block: transaction recipients, transaction senders, and the header's coinbase.

Critically, the trie nodes for these addresses can be collected in parallel. Rather than requesting a single trie node at a time, you can walk down one layer of the trie for all the addresses at once. Say you have ~200 addresses to collect, your `GetNodeData` might include up to 200 trie nodes at once on the final layer. This is a dramatic improvement, lessening the sensitivity to peer latency.

#### Optimization 2: Parallel Execution

The flow diagram above shows block imports as serial, so that child blocks aren't executed until the parent is complete. We want to improve on that with Parallel Execution. We start executing child blocks before the parent has completed executing. Some implications:

- The JIT-data limit of only requesting one trie node at a time applies per-block, so they can be requested in parallel across all pending blocks.
- The block count lag determines how many pending blocks are available. If you are right at the tip, parallelism drops to 1. The benefit of previewing grows as you lag and shrinks as you catch up. It is great to catch up faster, the further you are behind, but it can make Beam Sync feel a bit "stutter-y".
- Parallel execution "unnecessarily" retrieves state for child blocks, if the parent block writes that state. The data would have been available locally, if the client had waited for the parent to finish. This adds strain to the network. In practice, though, many blocks are largely independent in state access, so the waste is small.

#### Optimization 3: Speculative Execution

Many transactions included in the same block access independent parts of the state. So we can speculatively execute the transactions out-of-order. To speculatively execute, we treat each transaction as if it was the first & only transaction in the block. The transaction may fail, or execute on a different code path, in which case we get no benefit. But for the many state-independent transactions, we can correctly collect the required JIT-data for each transaction in parallel.

Note: if the same block includes multiple transactions from the same sender, then we group them together to run in serial. If you don't group them together, then the 2nd to nth transaction from the sender would always fail the nonce check, and provide no benefit.

There are probably other games you could play to predict transactions that depend on each other, and serialize them. But it hasn't been explored yet.

## Network Health

There are a few benefits to the health of the network.

One was already mentioned: Beam Syncing peers can serve data to other Beam Syncing peers. This means that a giant swarm of newly-connected nodes do not choke each other from joining the network.

Additionally, there is the cache-friendliness of the design. Storage I/O dominates the cost of serving trie nodes. Since peers are serving the same data that they just received, it should typically be in cache, whether that's at the application level, DB level, or OS level. In fact, since the trie nodes were already accessed for blocks that were recently executed, nodes that are unaware of Beam Sync might even have these trie nodes cached. This reduces the strain of serving state data.

(Fast Sync, by comparison, seems to be purpose-built to wreck the cache, by forcing a node to do a complete read out of all trie data from the database)

## Backfill coordination

Which brings us to the backfill strategy. The most naive implementation is to walk the trie, requesting all missing nodes. This is basically Fast Sync. Naively walking the trie, where each client picks its own scanning strategy, has a couple drawbacks:

- Beam-syncing peers can't assist each other in backfilling data
- It breaks the cache-friendliness of JIT-data collection

One approach to address these issues is to coordinate clients (implicitly) so that similar parts of the backfill are requested at similar times. Ultimately all data will have to be retrieved, but the hope is that we can minimize the costs to peers, and have Beam Syncing peers support each other more.

The proposal is to backfill in this pattern:
1. On the most recent block where `block.number % 100 == 0`, read the block hash and choose it as your backfill seed
2. Treat the backfill seed as if it were a hashed address
3. Use the seed to index into the trie, and start an upward scan of accounts and storage (collecting all storage for one account before moving to the next sibling account)
4. Request any missing accounts or storage slots as you encounter them
5. On receiving a new block where `block.number % 100 == 5`, stop the current scan, and restart at step 1.

In the final step, waiting until `block.number % 100 == 5` (instead of immediately when the mod is 0) is meant to reduce jitter. Otherwise, clients are more likely to start backfill on a block that would become uncled.

If a node is connected to exclusively other fresh Beam-Syncing peers, then the first backfill request will probably not succeed. But a node can re-request periodically with some optimism that the data will propagate to its peers eventually, from some peer that is itself connected to a full node.

One weakness of this approach is that the trie isn't evenly distrubuted, when you consider the storage tries "attached" at the bottom. This means that it might take longer than optimal to finish backfill. More practical testing is planned to determine how much of a problem this is (if any).

A naive implementation involves a lot of database scanning. It's not ideal to literally scan in this way, because of the heavy I/O load. Some optimizations are called for. For example, the client might store ranges of the trie that have already been filled, so that you don't have to re-walk it again the next time you index into the range.

## Security Considerations

### Invalid State Transitions

When skipping to the tip of the chain, your node does not re-validate all the state transitions prior to the tip. This is the same tradeoff as Fast Sync. A miner can arbitrarily change the state of a block if no one is revalidating. But any Full Syncing or Beam Syncing client would reject the block as invalid, so would not propagate the invalid block.

### Denial of Service

While a client is Beam Syncing, it's not too difficult to construct a block that reads so much state that the client will have to pivot. It's not clear this is a concern, since Beam Sync stores more and more data over time, the effectiveness of this DoS attack reduces over time for any particular node. This is more of a concern for stateless clients, which don't keep any data and can be perpetually knocked off the network over and over.

## FAQ

### What happens if a client doesn't backfill state data?

A sync implementation that doesn't backfill state data isn't Beam Sync, because it
never completes. That implementation would roughly be a light client that
does a bit more verification, and keeps a local data cache.

This is problematic for (at least) a couple reasons:

1. This kind of client can be DoS'd to make it skip verifying a target block by including
  a huge set of *cold* state reads. The client would have to pivot over the block, and skip verification.
1. This kind of client can't help other nodes finish Beam Sync to become full nodes.

Pairing these two together means that a swarm of light nodes can be knocked off
and not easily recover. They would have to go hunting for a full node to recover.
Transitioning from Beam Sync to full sync is what prevents this
attack on the nodes and network.

### How do we know that backfill eventually terminates?

At the first header that Beam Sync executes, enumerate all
trie nodes at the previous header's state root. This is the full set of trie
nodes that must be retrieved. They are either retrieved on-demand, or by backfill.
The only way that new nodes can enter the trie is by writing to the trie via
block execution, which is calculated locally as Beam Sync executes.

The set of nodes that need to be retrieved can only grow when you "pivot",
because your lag behind the main network has grown so large that peers are
no longer serving state data for the block at your historical level.

### Why is a full-state syncing strategy in a Stateless Ethereum Spec repo?

Although the end goal of syncing with Beam Sync is to be a full node, Beam Sync would be
much faster with new
network or consensus protocols that provide state witnesses. Those state witnesses are a
natural component of Stateless Ethereum. The intention is to propose new protocols
soon, and it makes a lot of sense for these protocols to be aligned
with other stateless client efforts.
