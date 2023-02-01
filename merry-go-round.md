# Merry-Go-Round State Syncing

This document proposes an experimental design for using the state network
component of the Portal Network to deliver an efficient mechanism for syncing
the Ethereum state.

## Storage Network

We build off of the current preliminary design of the state network, focusing
on the following elements.

### 1. Preservation of locality

All leaf data is mapped onto the DHT in a manner that preserves locality.  This
means that nodes store contiguous sections of trie data and two nodes that are
*close* to each other in the DHT will store similar data.

> Note that this matters primarily for the main account trie, and for large
> contract storage tries.  For tries that do not contain very much data, that
> data will be spread very thinly around the DHT and thus nodes are unlikely to
> store more than a single leaf node of data.

### 2. Keeping data up-to-date with gossiped proofs

At each block, the state network's gossip mechanism will disseminate proofs at
each new state root that allow individual nodes to update their state data from
previous state roots to newer state roots.  These updates are done as merkle
proofs to ensure they can be verified against the newer state root and don't
require trust.

## Basic Design of the Merry-Go-Round Sync

### Naive/Simplistic Sync

The high level design of the "merry go round" is that a node wishing to sync
the state would iterate through all of the nodes in the network, requesting the
proofs they are storing about the state, and merging them into a single
wholistic view of the entire trie.  In an environment where the Ethereum state
was static, and didn't change, this approach would result in having a full
copy of all of the state data after a node had fully traversed the DHT and
recieved all of the individual state proofs.

The Ethereum state is however, constantly changing as each new block is added
to the chain.  The result is that as a node walks through the network
requesting state data, the first proofs they receive will be anchored to some
state root that we'll call `S_n` and at some point, the proofs they receive will
be anchored to some subsequent root that we'll call `S_n+1`.

### Dealing with updates to the state

* Problem: As the Ethereum state changes, nodes that are syncing the state must
  be able to *update* the data they have already received to newer and newer
  state roots.

To address this, we will introduce two changes to how nodes in the network
handle state.

First, we introduce a concept of epoch boundaries.  Nodes in the network will
store proof of the segment of the state that they are storing for the network
at the most recent state root from the most recent epoch boundary.  The result
of this is that within a single epoch, all requests for state data from
different nodes will be anchored to the same state root.

Under this model we still assume that all updates to the state are being
gossiped as each block is added to the chain.  Nodes that are storing data
would accumulate a state diff from these proofs during the course of an epoch,
and at the end of the epoch, they can apply this state diff to their stored
state data to update their stored state to the new state root at the new epoch
boundary.

Research should be done to determine optimal epoch lengths.  The epoch length
must be short enough that a node can fully traverse the full DHT within a
single epoch.  We suggest 256 (51 minutes) as a starting point.

## Specification

### Storage

Nodes in the network store two things.

* proofs about the state *near* their position in the DHT anchored at the most
  recent epoch boundary
* diffs about the state accumulated from gossip that allow updating the state
  from the most recent epoch boundary to the newest state root.

> Note, that nodes will likely need to store at least the most recent two
> epochs of state data to account for the points in time where we are
> transitioning between epochs.  Nodes should continue to be able to retrieve
> data from the previous epoch to allow them the necessary time to fully obtain
> the necessary proof data to update their view of the state to the newest
> epoch.

### Gossip

The network provides a gossip mechanism that disseminates new state data from
each block to the nodes in the network that would store that data.

### Retrieval

The network exposes request/response primatives for:

* retrieving a node's proof of the state at a recent epoch boundary, likely bounded by a range of keys within the trie.
* retrieving a a node's proof diff that allows you to update their state proof to either a newer state root or the latest epoch boundary.


### Syncing

The process for syncing then becomes the following.

1. Let `P` be our proof against the state at the most recent epoch boundary.  The initial value of `P` is an empty proof.
2. Let `L` be the lowest key within the trie that we are missing leaf data for.  The initial value of `L` would be the `0x0` key.
3. Repeat the following until the head of the chain passes an epoch boundary.
    A. Find a node that is close to `L` and request it's proof data which will be anchored to the most recent epoch boundary.
    B. Merge the received proof data with `P`.
    C. Update `L` based on the updated proof `P` to point at the next largest missing key.
4. Once the chain passes the next epoch boundary, step 3 should be continued while also performing the following.
    A. Let `P_start` and `P_end` represent the start and end keys of the accumulated proof `P` that is anchored to the most recent epoch boundary.
    B. Let `D` be the state diff that would allow us to update `P` to the next epoch boundary.  The initial value of `D` is an empty proof.
    C. Let `L` be the largest key between `P_start and `P_end` for which we do not yet have a state diff within `D`
    D. Repeat the following until `D` is complete.
        1. Find a node that is close to `L` and request it's state diff.
        2. Merge the received diff with `D`
        3. Update `L` based on the updated diff `D` to point at the next largest missing key from the diff.
    E. Once `D` is complete, apply it to `P` to update the proof to now be anchored to the next and latest epoch boundary.
5. Repeat these processes until the network has been fully traversed, after which the client should have the complete state.

Syncing can then be described as the process of fetching proof data for the
most recent epoch until the next epoch boundary occurs.  At that point, we then
fetch the necessary proof diffs to update our accumulated proof data to the
latest epoch boundary, while continuing to fetch new state proofs for the new
epoch boundary, merging the two once the previous epoch data has been updated
to the latest epoch.  Once the full network has been traversed, a client should
have accumulated a complete and up-to-date copy of the ethereum state.
