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
It is expected that the gas schedule of EVM will need to be adjusted to account for the block witnesses. There are multiple possible ways of doing it. One of the current favourites is the charging of gas specifically for the witness, and not adding extra charges to opcodes like `SLOAD`, `BALANCE`, `CODECOPY`, etc. Such approach would need to deal with a lot of edge cases. These edge cases arise from the rules of gas forwarding set by instructions like `CALL`. Sometimes, invocation of another contract forwards the entire gas, and in this situation, charge for the witness size needs to be taken from the "forwarded gas pool". Sometimes, the invocation of anither contract forwards limited amount of gas (though this needs to be discouraged), and in this situaton, charge for the witness size needs to be taken from the "remaining gas pool". Dealing with this edge cases one by one manually is an error prone approach and may result in a prevaling pessimism about such gas repricing change. Therefore, automatic exploration of all edge cases and checking certain invariants might be the only way to enact such change. This, however, requires working formal semantics for EVM.

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

### 4. Benefits of code merkelisation (with oblivious chunking)
Initial data analysis was done, and the results look promising. However, more thourough analysis needs to be done, with different chunking strategy, with various chunk sizes (to see what is the current optimum), and on much larger set of blocks (to preclude the effects of time of the day, day of the week, or week of the months periodicity).
### 5. Visualisations of witnesses, and their reductions

### 6. Further work on semi-stateless approach as an "average case" optimisation
The data analysis on the reduction of witness sizes by semi-stateless appoach has been done only for one specific cache size (1 million nodes). Other cache sizes need to be analysed. Contract code needs to be included into the prototype. Network simulation needs to be done to see if we can use semi-stateless delivery to adjust the network composition do the presence of high-bandwidth pockets and chokepoints.
### 7. State analytics
### 8. Make witness semantics executable in Z3
### 9. One network vs "two networks" vs "three networks"
In the three networks idea, first network is used to download past block, headers, and receipts.
### 10. Stategies for enabling gas charge for witnesses
Make a change in the code to introduce the second gas counter (to be turned on optionally). Run it on the historical data to see how much extra gas the historical transactions would need to pay, and whether the results of the invocations would change with the second gas counter, given that there would be enough gas available.
### 11. Witness chunking for more efficient relay
Create network simulation to study the relationship between prevailing bandwidth and latencies and the optimal witness chunk size.
### 12. Transaction format to include proof of balance and proof of nonce of sender
Estimate how many bytes per transaction these extra proofs would add. Specify the way the transactions in a pool can be unpdated using information from the block witnesses.
### 13. Incentiviation of witness production and relay
### 14. Periodic state swarming
The duration of swarming cycle is chosen. It can be, for example, 4096 blocks. This can be adjusted over time as the state grows or network becomes efficient at syncing. Alternatively, there can be multiple sub-networks with different cycle durations. Block numbers that are multiple of the cycle duration always start the swarm cycle. At this point (beginning of the new cycle), the seeders (providers of the full state) start maintaining enumeration of the state as of the beginning of the cycle, while also maintaining the current enumeration.
### 15. Modification of the state trie structure to support canonical witnesses without witness hash in the header
Idea of including witness hash into the header has merits. However, it introduces the need to come up with hashing technique of witness into the witness hash. Such technique would ossify the witness format. Additionally, miners' consensus on witness hashing makes it harder to come up with flexible chunking strategy for faster witness relay.
There is an alternative to witness hash, which is modification of the state trie hashing to include some extra bits of information so that the receiver can distinguish parts of the witnesses belonging to different block numbers.

## Implementation roadmap

### 1. Turbo-Geth release (flat database layout)
### 2. Supporting hexary and binary tries simultaneously
### 3. State sync/swarming for binary trie
### 4. Migration of the state to binary trie
