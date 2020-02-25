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

### Lag

It can take longer than a block time to collect all the state needed for a block. So as new blocks arrive,
the currently executing block can fall further and further behind the tip. Clients typically
only serve state for recent blocks, configured differently for different clients. A
common number is ~100 blocks of state retained. If you fall behind this, then missing state
may no longer be available to you. This can leave you indefinitely stuck, so when we
lag far enough behind, we pivot.

### Pivoting

Pivoting skips executing the current blocks, and chooses the tip block again. It will
typically add to the missing data that must be backfilled. It is quite likely that
v0 will require a few pivots before BEam Sync exits, though as more and more data is collected it gets less likely.
v1 and v2 should be fast enough that pivoting is just a failsafe against "attack blocks" with
intentionally gigantic witnesses.

### Optimizations

TODO, roughly:
- Collect state up front for key addresses: transaction recipients, senders, and coinbase
- Collect state for key addresses in parallel
- Preview transaction execution and key addresses for "future" blocks (that have arrived, but are not yet executing).
- Split transactions into sender batches to run preview execution in parallel, but avoid nonce rejections

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
