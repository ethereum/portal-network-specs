We are currently talking about three roadmaps for Eth1x, and, specifically, for Stateless Ethereum.

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

## Research roadmap

### 1. Strategies for migrating from hexary to binary merkle tree for Ethereum state.

### 2. Static jump analysis of deployed EVM code

### 3. Efficient algorithms for validating static jumps

### 4. Benefits of code merkelisation (with oblivious chunking)

### 5. Visualisations of witnesses, and their reductions

### 6. Further work on semi-stateless approach as an "average case" optimisation
### 7. Make witness semantics executable in Z3
### 8. One network vs "two networks" vs "three networks"
### 9. Stategies for enabling gas charge for witnesses
### 10. Witness chunking for more efficient relay
### 11. Transaction format to include proof of balance and proof of nonce of sender
### 12. Incentiviation of witness production and relay
### 13. Periodic state swarming

## Implementation roadmap
