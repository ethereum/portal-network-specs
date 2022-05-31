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
EPOCH_SIZE = 8192 # blocks
MAX_HISTORICAL_EPOCHS = 100000

# An individual record for a historical header.
HeaderRecord = Container[block_hash: bytes32, total_difficulty: uint256]

# The records of the headers from within a single epoch
EpochAccumulator = List[HeaderRecord, max_length=EPOCH_SIZE]

Accumulator = Container[
    historical_epochs: List[bytes32, max_length=MAX_HISTORICAL_EPOCHS],
    current_epoch: EpochAccumulator,
]
```

The algorithm for managing the accumulator is as follows.

> TODO: provide a written spec too

```python
def update_accumulator(accumulator: Accumulator, new_block_header: BlockHeader) -> None:
    # get the previous total difficulty
    if len(accumulator.current_epoch) == 0:
        # genesis
        last_total_difficulty = 0
    else:
        last_total_difficulty = accumulator.current_epoch[-1].total_difficulty

    # check if the epoch accumulator is full.
    if len(accumulator.current_epoch) == EPOCH_SIZE:
        # compute the final hash for this epoch
        epoch_hash = hash_tree_root(accumulator.current_epoch)
        # append the hash for this epoch to the list of historical epochs
        accumulator.historical_epochs.append(epoch_hash)
        # initialize a new empy epoch
        accumulator.current_epoch = []

    # construct the concise record for the new header and add it to the current epoch.
    header_record = HeaderRecord(header.hash, last_total_difficulty + header.difficulty)
    accumulator.current_epoch.append(header_record)
```

### Growth over time

Each `HeaderRecord` is 64 bytes meaning the `EpochAccumulator` can range from `0 - 64 * EPOCH_SIZE` bytes (0-512KB) over the course of a single epoch.

The `Accumulator.historical_epochs` grows by 32 bytes per epoch.

At a 13 second block time we expect:

- ~1 epochs per day
- ~6 epochs per week
- ~25 epochs per month
- ~296 epochs per year

Ignoring fluxuations in the size of `Accumulator.current_epoch` we should expect the size of the accumulator to grow at a rate of roughly 10kb per year.


## Wire Protocol

The Header Gossip Network is an overlay network on the [Discovery V5 Protocol](https://github.com/ethereum/devp2p/blob/master/discv5/discv5-theory.md).  The overlay network uses the PING/PONG/FINDNODES/FOUNDNODES/FINDCONTENT/FOUNDCONTENT/OFFER/ACCEPT messages from the [Portal Wire Protocol](./portal-wire-protocol.md).

### Distance Function

The Header Gossip Network uses the standard XOR distance function.

### PING payload

TODO: specify what a node should do prior to having acquired a copy of the accumulator

```
Ping.custom_payload := ssz_serialize(custom_data)
custom_data         := Container(accumulator_root_hash: Bytes32, fork_id: Bytes32, head_hash: Bytes32, head_td: uint256)
```

### PONG payload

TODO: specify what a node should do prior to having acquired a copy of the accumulator

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

The gossip protocol for the header network is designed to quickly spread new headers around to all nodes in the network.

Upon receiving a new block header via OFFER/ACCEPT a node should first check the validity of the header.

Headers that pass the validity check should be propagated to `LOG2(num_entries_in_routing_table)` random nodes from the routing table via OFFER/ACCEPT.

## Accumulator Acquisition

New nodes entering the network will need to acquire an up-to-date snapshot of the accumulator.

The Header Gossip Network does provide the ability to acquire a snapshot of another node's accumulator. Since the accumulator is not a part of the base protocol (and thus is not part of the block header), nodes will have to do their own due diligence to either build the full accumulator from genesis or to adequately verify and validate a snapshot acquired from another peer.

TODO: provide basic probabilistic approach for verification of an accumulator snapshot.
