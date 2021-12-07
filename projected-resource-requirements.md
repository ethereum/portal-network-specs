# Portal Network Feasibility

This document is intended to examine the expected storage, processing, and bandwidth requirements for participants of the Portal Network

## Basics

### Routing Table Sizes

We can compute how many entries on average should exist in an individual node's routing table with the following:

```python
def get_bucket_size(total_network_size: int, bucket: int) -> int:
    return min(16, total_network_size / 2**bucket)
    
def get_routing_table_size(total_network_size: int) -> int:
    return sum(
        get_bucket_size(total_network_size, bucket_idx)
        for bucket_idx in range(1, 256)
    )
```

| Network Size | Routing Table Size |
| ------------ | ------------------ |
| 1,000        | 106                |
| 10,000       | 160                |
| 20,000       | 176                |
| 50,000       | 198                |
| 100,000      | 214                |
| 500,000      | 250                |
| 1,000,000    | 266                |


### Content Key Sizes

TODO

### Content Sizes

TODO


## Networks

### Header Gossip Network

#### Storage

- establish current size and growth rate for accumulator

#### Processing

- benchmark header verification
- benchmark maintenance of accumulator


#### Bandwidth

- gossip message volume as a function of radius (and network size)
- providing a copy of local accumulator


### Transaction Gossip Network

#### Storage

No storage

#### Processing

- benchmark transaction validation (which includes validation of account proofs)

#### Bandwidth

- size metrics for `transaction + proof` payload
- expected gossip message volume as a function of radius (and network size)

### History Network

#### Storage

Need size and growth metrics for:

- header + accumulator proof
- block bodies
- receipts

Parametrize storage based on network size and projected growth rates.

Growth rates can be parametrized by block gas limit


#### Processing

- benchmark verification of header accumulator proof + header validation (POW check)
- benchmark block body validation
    - construction of transaction trie
    - construction of uncle trie
- benchmark receipts validation
    - construction of receipts trie
    
    
#### Bandwidth

- expected gossip message volume


### State Network

#### Storage

- Size of individual trie nodes
    - intermediate trie node sizes
    - distribution of trie node sizes
    - account leaf trie node sizes
- Size of account range proof
    - the size of storing a contiguous range of the main account trie with proof data
    - the size of storing a contiguous range of contract storage with proof data
- Contract code...

#### Processing

- benchmark verification of hexary merkle proofs for:
    - intermediate trie nodes
    - account leaf nodes
    - storage stuff
- benchmark updating contiguous account range proof


#### Bandwidth

For a number of recent blocks:

1. compute the access list
2. pull individual proofs for all state fromm access list
3. compute total and individual payload sizes for all proof data for a block
4. figure out parametrized formula for the portion of this data that single node is responsible for.
5. figure out expected gossip messages for an individual node in the network.
