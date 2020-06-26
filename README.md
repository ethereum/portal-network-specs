# stateless-ethereum-specs
Specifications for the Stateless Ethereum research effort

## Problem Statement and Goals

[*Problem statement and goals subject to revision and the will of all contributers to Stateless Ethereum*]

The Ethereum state is ever-growing, and it will continue to do so at an accelerating pace. The growing size of the state will not only make running a full node more and more untennable for a ''normal" person, but may render the Ethereum network unstable and unusable if ignored. So we must not ignore it. 

Stateless Ethereum is the "all in" direction of Ethereum 1.x research to solve this problem. It encompasses a set of upgrades and features that will make keeping a full copy of the Ethereum state *optional* on the network, by introducing a proving scheme for clients without state (a block witness). 



## Contributing

**[Ethresear.ch (tag: "1.x research")](https://ethresear.ch/c/eth1x-research/37)**

**[Eth1x / 2 Research Discord]()** 



## In this Repo

### Specs

* WIP [Block Witness Format](./witness.md)

* [Beam Sync](./beam-sync-phase0.md)

### Roadmaps

* [Stateless Ethereum Tech Tree](./techTree.md)
* [Roadmaps for Eth1x and Stateless Ethereum](./roadmaps.md)




## Background

[Vitalik Buterin](https://ethresear.ch/u/vbuterin/summary) proposed the [Stateless Client Concept](https://ethresear.ch/t/the-stateless-client-concept/172) in October 2017. The purpose of the Stateless Client Concept is to create a new type of full Ethereum node that is no longer required to store the state of the entire blockchain.

Instead, miners would provide each mined block with the minimal information that is required to prove that block’s validity and to do a particular state transition. Such information is known as a witness. Witnesses are a set of Merkle branches proving the values of all data that the execution of the block accesses.

We encode the witness, the set of Merkle branches, as instructions. The block validator parses these instructions and constructs these Merkle branches, in order to check validity. Block validity is checked by constructing a partial Merkle tree using:

* the state-data provided by a state provider

* the above Merkle branches, and matching the computed Merkle root with the held Merkle root.

Therefore, block witnesses would allow stateless nodes to store only state roots instead of the entire Merkle Patricia trie for the entire blockchain. A node would receive the state root of a previous state, a newly mined block and the block’s witness. Successful validation of the new block would result in a new state. Only the state root for the new state would be stored by the node.

## Further Reading

### Overview & Concepts

* https://blog.ethereum.org/2019/12/30/eth1x-files-state-of-stateless-ethereum/
* https://blog.ethereum.org/2020/05/04/eth1x-witness-primer/
* https://medium.com/@pipermerriam/stateless-clients-a-new-direction-for-ethereum-1-x-e70d30dc27aa
* https://medium.com/@akhounov/on-the-state-rent-and-pivot-to-stateless-ethereum-ab4d967ff630
* https://medium.com/@akhounov/the-shades-of-statefulness-in-ethereum-nodes-697b0f88cd04


### Witness Optimization Techniques

* https://medium.com/@mandrigin/stateless-ethereum-binary-tries-experiment-b2c035497768
* https://medium.com/@mandrigin/semi-stateless-initial-sync-experiment-897cc9c330cb
* https://ethresear.ch/t/some-quick-numbers-on-code-merkelization/7260
* https://medium.com/ewasm/evm-bytecode-merklization-2a8366ab0c90

### Sync and Network

* SNAP protocol: https://github.com/ethereum/devp2p/blob/3fe9713658f3b3b56e4e99493c54f313e11b43a0/caps/snap.md
* Merry-go-round sync: https://ethresear.ch/t/merry-go-round-sync/7158

### State Trie

* https://medium.com/@gballet/ethereum-state-tree-format-change-using-an-overlay-e0862d1bf201

### EVM

* https://corepaper.org/ethereum/compatibility/leaky/
* https://ethresear.ch/t/meta-transactions-oil-and-karma-megathread/7472
* https://gist.github.com/holiman/8a3c31e459ee1bff04256bc214ea7f14

