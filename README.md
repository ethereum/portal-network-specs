# stateless-ethereum-specs
Specifications for the Stateless Ethereum research effort

## Documents

* [Roadmap](./roadmaps.md)
* [Block Witness Format Specification](./witness.md)
* [Beam Sync Phase 0](./beam-sync-phase0.md)

## Background

[Vitalik Buterin](https://ethresear.ch/u/vbuterin/summary) proposed the [Stateless Client Concept](https://ethresear.ch/t/the-stateless-client-concept/172) in October 2017. The purpose of the Stateless Client Concept is to create a new type of full Ethereum node that is no longer required to store the state of the entire blockchain. 

Instead, miners would provide each mined block with the minimal information that is required to prove that block’s validity and to do a particular state transition. Such information is known as a witness. Witnesses are a set of Merkle branches proving the values of all data that the execution of the block accesses. 

We encode the witness, the set of Merkle branches, as instructions. The block validator parses these instructions and constructs these Merkle branches, in order to check validity. Block validity is checked by constructing a partial Merkle tree using:

* the state-data provided by a state provider

* the above Merkle branches, and matching the computed Merkle root with the held Merkle root.

Therefore, block witnesses would allow stateless nodes to store only state roots instead of the entire Merkle Patricia trie for the entire blockchain. A node would receive the state root of a previous state, a newly mined block and the block’s witness. Successful validation of the new block would result in a new state. Only the state root for the new state would be stored by the node.
