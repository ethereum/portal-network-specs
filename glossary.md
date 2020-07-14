A Glossary of Stateless Ethereum
---------------------------------
*This glossary is a work in progress; contributions are welcome*

**Beam Sync**. An stateless sync protocol similarities to what is imagined for Stateless Ethereum. The scheme works by executing a block first, and then requesting missing state data on demand. Beam Sync may be used stand-alone, or as a building block to other sync protocols.

**Code Merkleization**. A method of splitting contract bytecode into smaller pieces, so that an execution that only touches part of a smart contract does not need to include the entire contract in its witness.

**Merkle Tree**. A [tree](https://en.wikipedia.org/wiki/Tree_(data_structure)) data structure in which every leaf node is labeled with the [hash](https://en.wikipedia.org/wiki/Cryptographic_hash_function) of a data block, and every non-leaf node is labeled with the hash of the labels of its child nodes.

**Patricia Trie**. A special variant of the radix trie, in which rather than explicitly store every bit of every key, the nodes store only the position of the first bit which differentiates two sub-trees.

**Merkle-Patricia Trie** Ethereum's cryptographically secure data structure, which combines characteristics of Merkle and Patricia tries to enable a reasonably efficient and verifiable representation of all accounts, balances, transactions, receipts, and state. See the [Ethereum wiki](https://eth.wiki/en/fundamentals/patricia-tree) for detailed information
  * **Hexary trie**. Ethereum's current trie format is hexary: Each node in the trie has 16 children.
  * **Binary trie**. Transitioning to a binary trie where each node has only two children is a major milestone in the Stateless Ethereum effort to bound witness sizes.

**Polynomial commitment**

**SNARK / STARK** "A family of cryptosystems, usually classified as [Zero-Knowledge](https://en.wikipedia.org/wiki/Zero-knowledge_proof), which can be used to cryptographically prove a computation, such as processing a block of transactions, without requiring a state witness to verify the proof. The [hardness assumption](https://en.wikipedia.org/wiki/Computational_hardness_assumption) of forging such a proof are considered cryptographically strong.

**State** or **State Trie**. The Merkleized representation of Ethereum's shared execution state, which contains all account balances, smart contract storage (storage is a nested trie within each account and has its own root). For more information see the [Ethereum wiki](https://eth.wiki/en/fundamentals/patricia-tree).


**Statelessness** or **Statefullness**. The degree to which any Ethereum client participating in the Stateless Ethereum network keeps a local copy of state, or alternatively relies on a Witness for block execution.

  * **Stateful nodes** keep a complete copy of state, as all clients do currently.

  * **Semi-stateless nodes** keep a full state for a bounded number of blocks or a partial state that they’re interested in, relying on witnesses to provide the rest of the data needed to verify new blocks.

  * **Zero-state**  or **stateless nodes** keep no information about a block's state besides a valid `stateRoot`, and rely entirely on witnesses for block execution and tx validation.


**Stateless Verification** the process of validating a block using only a witness.

**Witness**. The centerpiece of Stateless Ethereum: A data structure that 'proves' a valid state without containing the actual state data, only the missing hashes required to reproduce a particular `stateRoot`. See the [formal specification](./witness.md) for more information. Much of the work surrounding Stateless Ethereum is related to reducing the size of witnesses so that they can be useful on the network.
