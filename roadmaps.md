We are currently talking about three roadmaps for Eth1x, and, specifically, for Stateless Ethereum.

## Problem statement
Preserve the resilience of Ethereum 1 network despite the state growth. By making it easier to join the network and stay on it, and therefore increasing number and diversity of nodes. The improvement in the User Experience is not in the scope.

## Tools roadmap
We recognise two main types of research - quantitative and speculative. Both are important. Quantitative research usually
requires some tools and equipment (in our case equipment is usually computers, but sometimes we need computers with certain
types of hardware, like NVMe, and fast network interfaces, to reduce the time of experiments). Speculative research requires
good fundamental understanding of issues at hand, and ability to make logical deductions and thought experiments even
in the absense of some information. Moreover, these two types of research reinforce each other. Speculative research
sets directions for initial experiments and quantitative research. Quantitative research results help reinforce or filter out
branches of the speculative research.

We recognise the lack of tools for our quantitative research. Here is a short list (when it becomes longer and more specific,
please take it into a separate document):

### 1. Simulators of peer to peer networks to validate hypotheses on data propagation
These simulators need to abstract away most of the implementation details, and only exhibit features required for the research tasks at hand. This is different from emulators where the real Ethereum implementations are used. Simulators need to be performant enough to explore long timelines and large networks. They also need to include means of generating network topologies that are either naturally occuring, or those that potentially break some desirable properties.
### 2. Benchmarks that compute suitable parameters for the p2p simulators (latency of propagation, processing times, etc.)
Various implementations (go-ethereum, parity, nethermind, besu, turbo-geth, etc.) have different performance characteristics when it comes to relaying blocks, transactions, and, in the future, block witnesses. These performance characteristics need to be taken into account when running network simulators.
### 3. Emulators of large state, reorgs, and various contract activity
In order to exercise functionality like block witnesses generation, witness propagation, transaction propagation, and others, without deploying implementations on the mainnet, emulators can be used. This could be programs that emulate peers and are capable of serving large states, and generating the blocks with various levels of activity. For example, these would be able to cause very large witnesses to be generated, or cause deep reorgs.

### 4. EVM semantics for producting formalised proposals on the gas pricing changes. Secondary benefits are white-box fuzzing of smart contracts, creation of high-coverage "super-tests"
It is expected that the gas schedule of EVM will need to be adjusted to account for the block witnesses. There are multiple possible ways of doing it. One of the current favourites is the charging of gas specifically for the witness, and not adding extra charges to opcodes like `SLOAD`, `BALANCE`, `CODECOPY`, etc. Such approach would need to deal with a lot of edge cases. These edge cases arise from the rules of gas forwarding set by instructions like `CALL`. Sometimes, invocation of another contract forwards the entire gas, and in this situation, charge for the witness size needs to be taken from the "forwarded gas pool". Sometimes, the invocation of another contract forwards limited amount of gas (though this needs to be discouraged), and in this situaton, charge for the witness size needs to be taken from the "remaining gas pool". Dealing with this edge cases one by one manually is an error prone approach and may result in a prevaling pessimism about such gas repricing change. Therefore, automatic exploration of all edge cases and checking certain invariants might be the only way to enact such change. This, however, requires working formal semantics for EVM.

Current idea for the formal EVM semantics to be the set of substitution rules with the core types mapping directly to the types of Microsoft z3 library. This compatibility should allow to express all the rules as the tulples of z3 expressions. Rules need to be simple enough to be understood with a very minimal context, and therefore are easy to refer to in EIPs (Ethereum Improvement Proposals). They also need to be written in simple text to make it suitable for Pull Requests.

The benefits of such approachs are many. One can execute the semantics concretely (with a help of a generic "driver" program) to test/fuzz it differentially against the concrete implementations of EVM. One can execute the semantics symbolically - this is useful for contract verification. One can use formal semantics for white-box fuzzing of smart contracts. One can use formal semantics for production of "super tests" - EVM conformance tests with very high coverage, effectively automating most of the work of preparing tests for new EVM changes.

First step would be to try to formalise a very small subset of EVM, supporting 3 instructions - PUSH1, ADD, and STOP. And demonstrate all the primary and secondary benefits in that example. Then, extend such EVM bit by bit, adding more opcodes and resources (memory, state, etc.).

## Research roadmap

### 1. Strategies for migrating from hexary to binary merkle tree for Ethereum state
It has been found that binary merkle tries are more beneficial than hexary merkle tries. There are many migration paths for existing implementations. One proposal is described here: https://ethresear.ch/t/optimizing-sparse-merkle-trees/3751

Theoretically, a minimally disruptive migration is to keep the patricia hex trie structure, but changing the hash function from
````
sha(rlp(x1 .... x16))
````
to
````
merkle_tree(x1 ... x16)
````
At DB level nothing would change.
There are also ways of performing incremental (as opposed to "stop the world") migration. Rough idea is to introduce a flag/marker at each trie leaf. This flag/marker will be unset by default, and set for any leaf that has been updated after the migration block number.

There is a way of making transition using a new sync algorithm providing the state using the new state roots.

### 2. Static jump analysis of deployed EVM code
We might not need this for code merkelisation, if we just include jump dest table into the code before merkelisation.

### 3. Efficient algorithms for validating static jumps
If it turns out that the static jump analysis effectively marks all (or most) contracts as "static jump only", the most efficient algorithm can be found to perform such analysis at the contract deploy time. Big downside of such marking is the inclusion of the static analysis into the consensus rules.

### 4. Benefits of code merkelisation (with oblivious chunking)
Initial data analysis was done, and the results look promising. However, more thourough analysis needs to be done, with different chunking strategy, with various chunk sizes (to see what is the current optimum), and on much larger set of blocks (to preclude the effects of time of the day, day of the week, or week of the months periodicity).
### 5. Visualisations of witnesses, and their reductions

### 6. Further work on semi-stateless approach as an "average case" optimisation
The data analysis on the reduction of witness sizes by semi-stateless appoach has been done only for one specific cache size (1 million nodes). Other cache sizes need to be analysed. Contract code needs to be included into the prototype. Network simulation needs to be done to see if we can use semi-stateless delivery to adjust the network composition do the presence of high-bandwidth pockets and chokepoints.
### 7. State analytics
### 8. Make witness semantics executable in Z3
### 9. One network vs "two networks" vs "three networks"
In the three networks idea, the first network is used to download past block, headers, and receipts. The second network is used to propagate (or gossip) transactions, new block headers, new block bodies, and block witnesses. The third network is dedicated to syncing to the current full state. This model, if applied exclusively, does not work for Beam Sync, because Beam Sync relies on the on-demand state access within the p2p network. Currently, on-demand state access is used to implement the initiall state sync, which is believed to be a sub-optimal way of doing it. Therefore, Beam Sync (and other applications requiring on-demand state access), would need to either rely on the legacy network (which mixes downloading, gossip, and on-demand state access), or build a separate network for on-demand state access. Currently, Light Client Protocol (LES) is aspiring to create an insentivised network to provide such on-demand state access. If a free (meaning non-incentivised) on-demand state access network continues to exist, this might impede the ability of LES to gain any serious adoption. An opinionated way forward is to eventually remove on-demand state access from the free networks, because it is not strictly required for improved resiliency. Anyone can still acquire any piece of state if they wanted to, but they might need to join the initial sync network for several hours and stay there. Alternatively, they can pay and get data immediately via LES protocol.
### 10. Stategies for enabling gas charge for witnesses
Make a change in the code to introduce the second gas counter (to be turned on optionally). Run it on the historical data to see how much extra gas the historical transactions would need to pay, and whether the results of the invocations would change with the second gas counter, given that there would be enough gas available.
### 11. Witness tiles for more efficient relay
When block witnesses are relatively large, trying to propagate them through the network as one single packet can be slower than it should be. This is because at every network hop, a participating node needs to completely ingest the block witness, verify it (this can be done at the same time as ingesting though), and only then start streaming it to the next peer. If the block witnesses are split in smaller "tiles", streaming to the next peer can be initiated as soon as the first tile is processed.
Create network simulation to study the relationship between prevailing bandwidth and latencies and the optimal witness tile size.
### 12. Transaction format to include proof of balance and proof of nonce of sender
Estimate how many bytes per transaction these extra proofs would add. Specify the way the transactions in a pool can be updated using information from the block witnesses.
### 13. Incentiviation of witness production and relay
Detailed break-down (this can be implementation specific, but useful netherless) of the process of composing block number `N` by a miner, with estimated durations (in milliseconds). Both cases of not having a witness for block `N-1` and having that witness need to be analysed and compared. Currently, the intuition is that the present of the witness for block `N-1` does not sufficiently speed up the production of the block `N`, possible conclusion being that the presence of witnesses on the network is not enough insentivisation on its own. If this hypothesis is true, the current favourite incentivisation is to have all the participants on gossip network to not propagate blocks without propagating the corresponding witness. Under such rules, stateless nodes would have no option than to refuse propagating the block if the corresponding witness did not arrive. Nodes with the full state, though, may be able to re-generated the witness. This can be a natural solution to the presence of "choke points" in the gossip network. The side effect of "no block propagation without witness" is slowing down the block propagation, with potential consequences being higher uncle rate, etc.
### 14. Periodic state swarming
The duration of swarming cycle is chosen. It can be, for example, 4096 blocks. This can be adjusted over time as the state grows or network becomes efficient at syncing. Alternatively, there can be multiple sub-networks with different cycle durations. Block numbers that are multiple of the cycle duration always start the swarm cycle. At this point (beginning of the new cycle), the seeders (providers of the full state) start maintaining enumeration of the state as of the beginning of the cycle, while also maintaining the current enumeration.
### 15. Modification of the state trie structure to support canonical witnesses without witness hash in the header
Idea of including witness hash into the header has merits. However, it introduces the need to come up with hashing technique of witness into the witness hash. Such technique would ossify the witness format. Additionally, miners' consensus on witness hashing makes it harder to come up with flexible chunking strategy for faster witness relay.
There is an alternative to witness hash, which is modification of the state trie hashing to include some extra bits of information so that the receiver can distinguish parts of the witnesses belonging to different block numbers.

## Implementation roadmap

### 1. Turbo-Geth release (flat database layout)
Although this looks like an unrelated deliverable, it might be enabling faster migration to binary tree hashing than otherwise. Both through turbo-geth potentially being able to support hexary and binary trees simultaneously, and through providing validation for the flat database layout (this can de-risk re-engineering efforts for other implementations).
It is believed that flat database layout is better suited than merkle-tree based layout for many algorithms and protocols that will become part of Stateless Ethereum. 
### 2. Supporting hexary and binary tries simultaneously
This functionality will need to be built into the implementation that are going to be around in the network for the "transition" period. For merkle-tree based database layouts this means figuring out how to store binary tree data efficiently, or perhaps transition to the flat database layout just for the sake of the supporting binary trees (and then optionally drop the support for hexary trees later)
### 3. State sync/swarming for binary trie
This is where we create a full state sync network (or subnetwork discoverable via ENR - Ethereum Node Registry) to perform efficient distribution of state with the proofs based on binary merkle tree (with temporarily centralised state roots). For most current implementation, it is much more efficient to acquire the state over the network than trying to extract it from its own database. Also, if the swarm sync is efficient, it can be supported by minority of nodes providing data and majority of nodes syncing (as opposed to the current situation where there has to be majority of data providers for a minority of syncing nodes). This is the justification for using this new syncing mechanism and not simply extending fast sync or others.
### 4. Migration of the state to binary trie
Once the swarm sync network is establish and there is a general satisfaction that new nodes can join the network at any time and sync properly, the migration time (block number) can be scheduled. After this time (block number), binary tree based state root will start appearing in the block headers, instead of being provided by centralised oracle.
