# Portal Network Feasibility

This document is intended to examine the expected storage, processing, and bandwidth requirements for participants of the Portal Network

## Basics

### Message Sizes

Here we establish the overhead for various messages in the protocol.

#### Base protocol message overhead

We expect most messages to use the regular MESSAGE type packet from discovery v5 which has 39 bytes of overhead.

#### TALKREQ/TALKRESP message overhead

We expect each TALKREQ message to contain:

- `request-id`: 4 bytes
- `protocol-id`: 2 bytes
- `payload`: variable

Combined with the base overhead from the message packet this gives us 55 bytes of overhead per packet.


#### uTP message overhead.

TODO: ask konrad



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

| Network Size | Routing Table Size | Log2    |
| ------------ | ------------------ | ------- |
| 1,000        | 106                | 6.72792 |
| 10,000       | 160                | 7.32193 |
| 20,000       | 176                | 7.45943 |
| 50,000       | 198                | 7.62936 |
| 100,000      | 214                | 7.74147 |
| 500,000      | 250                | 7.96578 |
| 1,000,000    | 266                | 8.05528 |


### Accumulator Sizes

The Accumulator should exibit the following growth characteristics.

The "History Size" column is for the portion of the accumulator that stores the hashes of historical epochs.

The "Max Size" column is the size of the accumulator when the current epoch is full (and will be hashed and stored in the history section upon adding the next block).


| Block Number | Accumulator History Size | Accumulator Max Size |
| ------------ | ------------------------ | -------------------- |
| 100,000      | 390B                     | 512.4KB              |
| 1,000,000    | 3.8KB                    | 515.8KB              |
| 10,000,000   | 38.1KB                   | 550.1KB              |
| 15,000,000   | 57.2KB                   | 569.2KB              |
| 30,000,000   | 114.4KB                  | 626.4KB              |


### Block Headers

A block header is about 540 bytes.

### Accumulator Info

Using an epoch size of 8192 results in an SSZ merkle trie 13 levels (8192 = 2**13).  The proof for a single element in the SSZ data structure will contain:

- The element being proven which is a `HeaderMeta`: 64 bytes
- The hash of the sibling element: 32 bytes
- 12 layers of intermediate node hashes: 12 * 32 bytes
- The hash of the SSZ "length" node in the trie: 32 bytes (compressable using LEB128 if desired)
- The root hash: 32 bytes

Summing these up gives us: 544 bytes of proof data for the epoch portion of the proof.

The epoch proof must be anchored to the accumulator history.  At present the chain has progressed through approximately 1600 epochs (13000000 / 8192).

The proof for a single element from history with today's chain at a heigh of 13 million blocks will contain:

- The hash of the epoch accumulator for the epoch in question: 32 bytes
- The sibling hash of the node adjacent to the epoch in question: 32 bytes
- Approximately 10 layers of intermediate hashes: 10 * 32 bytes
- The hash of the length node: 32 bytes
- The root hash: 32 bytes

This gives us roughly 170 bytes for the main accumulator proof

The expected total proof size is 714 bytes.

## Header Gossip

Gossip of block headers in the history network will include both the header (540 bytes) and the proof (714) bytes, with a total payload size of roughly 1254 bytes.

The header gossip algorithm encourages gossip to `log2(len(routing_table))` peers, which is between 6-8 peers.

The content-key for header gossip is specified as `Container(chain-id: uint16, content-type: uint8, block-hash: Bytes32)` which results in a 35 byte encoded length.

The least number of messages we expect a node to send are 8 OFFER messages for which none are acccepted, resulting in sending:

- OFFER:
  - message overhead: 55 bytes 
  - content key encoding: 35 bytes
- ACCEPT: 
  - message overhead: 55 bytes 
  - message: 9 bytes (4-byte connection id, 1 byte bit-list + 4-byte length prefix)

This gives us a total of 80 bytes out and 64 bytes inbound.  Totalling the 8 OFFER/ACCEPT messages gives us:

- Best case:
  - 640 bytes out
  - 512 bytes in


The loose upper bound for data transmission is all 8 peers ACCEPT the OFFER, resulting in:

- OFFER overhead
  - message overhead: 55 bytes 
  - content key encoding: 35 bytes
- ACCEPT: 
  - message overhead: 55 bytes 
  - message: 9 bytes (4-byte connection id, 1 byte bit-list + 4-byte length prefix)
- uTP:
  - overhead???
  - 1254 bytes for payloads

These messages should occur roughly once per BLOCK_TIME (13 seconds)....



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
