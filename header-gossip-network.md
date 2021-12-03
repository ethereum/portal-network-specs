# Portal Network: Header Gossip

This document is the specification for the "Header Gossip" network which is responsible for dissemination of new headers as new blocks are mined and  transmission of recent snapshots of the "Header Accumulator" data structure which all nodes on the network are expected to maintain.

## Design Requirements

The network functionality has been designed around the following requirements.

- A DHT node can reliably receive the headers for new blocks via the gossip mechanism in a timely manner.
- A DHT node can retrieve a recent snapshot of another DHT node's "Header Accumulator"


## The "Header Accumulator"

The "Header Accumulator" is based on the [double-batched merkle log accumulator](https://ethresear.ch/t/double-batched-merkle-log-accumulator/571) that is currently used in the beacon chain.  This data structure is designed to allow nodes in the network to "forget" the deeper history of the chain, while still being able to reliably receive historical headers with a proof that the received header is indeed from the canonical chain (as opposed to an uncle mined at the same block height).

The accumulator is defined as an [SSZ](https://ssz.dev/) data structure with the following schema:

```python
EPOCH_SIZE = 8192
MAX_EPOCH_COUNT = XXXX

# The verbose version of the accumulator
MasterAccumulator = List[EpochAccumulator, max_length=MAX_EPOCH_COUNT]

# A schema equivalent version of the `MasterAccumulator` which references the individual EpochAccumulator values by their ssz merkle root hash.
ConciseAccumulator = List[bytes32, max_length=MAX_EPOCH_COUNT]

# The records of the headers from within a single epoch
EpochAccumulator = List[HeaderRecord, max_length=EPOCH_SIZE]

# An individual record for a historical header.
HeaderRecord = Container[block_hash: bytes32, total_difficulty: uint256]
```

The `MasterAccumulator` schema above is included for explanatory purposes, however clients of the network will not actually maintain this data structure, but the schema-equivalent `ConciseAccumulator`.  The `MasterAccumulator` would require retaining a large amount of historical header data which would exceed the storage limits of resource constrained devices.  The `ConciseAccumulator` is designed to leverage the SSZ merkle hashing, storing only the ssz merkle hash of the individual `EpochAccumulator` entries as opposed to the full epoch information.

TODO: full spec for construction and maintenance of the accumulator.

## Wire Protocol

The Header Gossip Network is an overlay network on the [Discovery V5 Protocol](https://github.com/ethereum/devp2p/blob/master/discv5/discv5-theory.md).  The overlay network uses the PING/PONG/FINDNODES/FOUNDNODES/FINDCONTENT/FOUNDCONTENT/OFFER/ACCEPT messages from the [Portal Wire Protocol](./portal-wire-protocol.md).

### Distance Function

The Header Gossip Network uses the standard XOR distance function.

### PING payload

TODO: instructions on what a node should do prior to having acquired a copy of the accumulator

```
Ping.custom_payload := ssz_serialize(custom_data)
custom_data         := Container(accumulator_root_hash: Bytes32, fork_id: Bytes32, head_hash: Bytes32, head_td: uint256)
```

### PONG payload

TODO: instructions on what a node should do prior to having acquired a copy of the accumulator

```
Pong.custom_payload := ssz_serialize(custom_data)
custom_data         := Container(accumulator_root_hash: Bytes32, fork_id: Bytes32, head_hash: Bytes32, head_td: uint256)
```

## Content Keys

### Accumulator Snapshot

> Note: The `content-id` for this content key is not used for any purpose.

```
content_key  := Container(content_type: uint8, accumulator_root_hash: Bytes32)
content_type := 0x01
content_id   := accumulator_root_hash
```

TODO: wire serialization for FINDCONTENT/FOUNDCONTENT

### New Block Header


```
content_key  := Container(content_type: uint8, block_hash: Bytes32, block_number: uint256)
content_type := 0x02
content_id   := block_hash
```

TODO: block validation and wire serialization

## Gossip

TODO: offer block to `log(len(routing_table))` number of nodes from your routing table.
TODO: block validation rules


### Accumulator handling
Describes how accumulator is shared when a node first joined the portal network or when a node tries to catch up to the tip of the chain after being N blocks away 

1. Nodes request for accumulator will `RequestAccumulator` from more than 1 node in its DHT.

2. Node that receives `RequestAccumulator` will respond with 3 `ResponseAccumulator` responses. 1 for the master accumulator and the other 2 for the 2 latest epoch accumulator it currently stores. A node that receives too many  `RequestAccumulator` from the same node within a short time span may choose to drop the request for DOS protection.

3. Requesting node will compare the master accumulator response and determined the 'correct' master accumulator via a heuristic approach. The last entry of the master accumulator will not be taken in account as network latency will result in some differences in the last few blocks

4. The epoch accumulator associated the 2nd last entry of the master accumulator is validated by checking the root hash and is accepted and stored. 

5. The correctness epoch accumulator associated to the last entry of master accumulator is also determined heuristically. 
A common length and block hash that the majority of the neighbour nodes shared will be accepted and stored.

6. The node will proceed to sync the later blocks through the normal process

### Incoming blocks handling
Describes how new blocks are being shared among nodes. 

1. New blocks originate from bridge nodes and the full block header is stripped to contain only information that is needed for block validation. Refer <u>Partial Block Header</u> section. 

2. New validated blocks are offered to neighbour nodes (not including nodes which the block is received from) via  `OfferBlockHeader`

3. Nodes receiving the `OfferBlockHeader` will check to see if the blocknumber being offered is currently than that it currently stores

4. Nodes who are interested in the new block will `RequestBlockHeaders` to the offering node and includes a starting block number. 

5. Offering node will respond the partial block headers starting from the requested starting block number via `ResponseBlockHeader`.

6. Receiving nodes will validate the blocks and include them into the accumulator. It will send out `OfferBlockHeader` of the latest block only to other nodes in its DHT.


### Reorg handling
Describes how a node handles reorg. Occurs when a node realizes a longer valid chain has a different canonical parent block hash.

1. When a node receives partial block header from `ResponseBlockHeader` it checks to see if it has a canonical parant block hash. A reorg will occur if the parent block hash expected by the new block does not match the block hash of the previous block from the new block.

e.g. 
| New block | Previous block |
|-----------|----------------|
| number:100| number:99      |
| hash: irrelevant | hash: 0xbb|
| parenthash: 0xbc | parenthash: irrelevant|


2. A node will `RequestBlockHeaders` and setting the starting block number to a few blocks behind the current block in an attempt to determine the canonical block.

3. If the canonical block is beyond the range of the selected starting block number, the node will `RequestBlockHeaders` again until a canonical block hash is found or the requested block header is beyond N blocks away

4. If block header requested is N blocks away, the node will need to `RequestAccumulator` to resync its accumulator. If it is within N blocks, the entries of the accumulator in the node's local storage will be replaced with the new block hashes

## Analysis on storage growth for different epoch size

*Assuming block time of 15secs


| Epoch size | 2048 | 8192 |
| --- | --- | --- |
| Size of fully filled epoch file | 131,072 bytes | 524,288 byte |
| Rate of Growth of master accumulator | 3.75 bytes/hr | 0.9375 bytes/hr |
| Size of master accumulator at block 1000 | 32 bytes | 32 bytes |
| Size of master accumulator at block 5000 | 96 bytes | 32 bytes |
| Size of master accumulator at block 10,000 | 160 bytes | 64 bytes |
| Size of master accumulator at block 15,000 | 256 bytes | 64 bytes |




