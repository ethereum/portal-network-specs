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

 * Simulators of peer to peer networks to validate hypotheses on data propagation
 * Benchmarks that compute suitable parameters for the p2p simulators (latency of propagation, processing times, etc.)
 * Emulators of large state, reorgs, and various contract activity
 * EVM semantics for producting formalised proposals on the gas pricing changes. Secondary benefits are white-box fuzzing of smart contracts, creation of high-coverage "super-tests"

## Research roadmap

### 1. Strategies for migrating from hexary to binary merkle tree for Ethereum state.

### 2. Static jump analysis of deployed EVM code

### 3. Efficient algorithms for validating static jumps

### 4. Benefits of code merkelisation (with oblivius chunking)

### 5. Visualisations of witnesses, and their reductions

### 6. Further work on semi-stateless approach as an "average case" optimisation
### 7. Make witness semantics executable in Z3
### 8. One network vs "two networks" vs "three networks"
### 9. Stategies for enabling gas charge for witnesses
### 10. Witness chunking for more efficient relay
### 11. Transaction format to include proof of balance and proof of nonce of sender
### 12. Incentiviation of witness production and relay

## Implementation roadmap
