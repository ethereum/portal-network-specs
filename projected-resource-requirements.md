# Portal Network Feasibility

This document is intended to examine the expected storage, processing, and bandwidth requirements for participants of the Portal Network

## Basics

### Message Sizes

Here we establish the overhead for various messages in the protocol.

#### Base protocol message overhead

We expect most messages to use the regular MESSAGE type packet from discovery v5 which has 71 bytes of overhead.

#### TALKREQ/TALKRESP message overhead

We expect each TALKREQ message to contain:

- `request-id`: 4 bytes
- `protocol-id`: 2 bytes
- `payload`: variable

Combined with the base overhead from the message packet this gives us 77 bytes of overhead per packet.

> The few additional bytes needed for RLP encoding are intentionally left out of this estimate.


#### uTP message overhead.

Setting up a stream involves 40 bytes of packet overhead:

- SYN packet:
    - sent by initiator
    - 20 bytes
- ACK packet:
    - sent by recipient
    - 20 bytes

Closing a stream involves 40 bytes of packet overhead:

- FIN packet:
    - sent by initiator
    - 20 bytes
- ACK packet:
    - sent by recipient
    - 20 bytes

The data payload is divided up into chunks of as small as 150 bytes and as large as 1180 bytes, each with 20 bytes of overhead giving us a formula of:

```python
UTP_PACKET_MIN_SIZE = 150
UTP_PACKET_MAX_SIZE = 1024


@dataclass
class Meter:
    packets: int = 0
    bytes: int = 0

    def add_packet(self, num_bytes: int) -> None:
        self.packets += 1
        self.bytes += num_bytes


@dataclass
class UDPMeter:
    # number of inbound bytes
    inbound: Meter = field(default_factory=Meter)

    # number of outbound bytes
    outbound: Meter = field(default_factory=Meter)

    def __str__(self) -> str:
        return f"packets={self.num_packets:n}  inbound={humanize_bytes(self.inbound)}  outbound={humanize_bytes(self.outbound)}"


def _compute_utp_transfer(payload_size: int, packet_payload_size: int) -> Tuple[UDPMeter, UDPMeter]:
    initiator = UDPMeter()
    recipient = UDPMeter()

    # SYN to initiate stream
    initiator.outbound.add_packet(20)
    recipient.inbound.add_packet(20)

    # ACK to acknowledge stream setup
    recipient.outbound.add_packet(20)
    initiator.inbound.add_packet(20)

    # Data packets
    total_data_packets = int(math.ceil(payload_size / packet_payload_size))

    # 20 bytes of overhead per packet
    initiator.outbound.packets += total_data_packets
    initiator.outbound.bytes += total_data_packets * (packet_payload_size + 20)

    # acks from the recipient for the data packets
    initiator.inbound.packets += total_data_packets
    initiator.inbound.bytes += total_data_packets * 20

    # receipt of the data packets
    recipient.inbound.packets += total_data_packets
    recipient.inbound.bytes += total_data_packets * (packet_payload_size + 20)

    # acks sent for data packets
    recipient.outbound.packets += total_data_packets
    recipient.outbound.bytes += total_data_packets * 20

    # FIN to close the stream
    initiator.outbound.add_packet(20)
    recipient.inbound.add_packet(20)

    # ACK to acknowledge the stream is closed
    recipient.outbound.add_packet(20)
    initiator.inbound.add_packet(20)

    return initiator, recipient
```


Here is a table of uTP expected traffic for various known payloads:

| Payload                 | Initiator: packets-in | I: packets-out | I: bytes-in | I: bytes-out  | Recipient: packets-in | R: packets-out | R: bytes-in   | R: bytes-out |
| ----------------------- | --------------------- | -------------- | ----------- | ------------- | --------------------- | -------------- | ------------- | ------------ |
| Header                  | 3 - 6                 | 3 - 6          | 60 - 120    | 600 - 660     | 3 - 6                 | 3 - 6          | 600 - 660     | 60 - 120     |
| Header+AccumulatorProof | 4 - 11                | 4 - 11         | 80 - 220    | 1,334 - 1,474 | 4 - 11                | 4 - 11         | 1,334 - 1,474 | 80 - 220     |



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
  - message overhead: 77 bytes
  - content key encoding: 35 bytes
- ACCEPT: 
  - message overhead: 77 bytes
  - message: 9 bytes (4-byte connection id, 1 byte bit-list + 4-byte length prefix)

This gives us a total of 80 bytes out and 64 bytes inbound.  Totalling the 8 OFFER/ACCEPT messages gives us:

- Best case:
  - 640 bytes out
  - 512 bytes in


The loose upper bound for data transmission is all 8 peers ACCEPT the OFFER, resulting in:

- OFFER overhead
  - message overhead: 77 bytes 
  - content key encoding: 35 bytes
- ACCEPT: 
  - message overhead: 77 bytes 
  - message: 9 bytes (4-byte connection id, 1 byte bit-list + 4-byte length prefix)
- uTP:
  - best case: 60 bytes in / 1334 bytes out
  - worst case: 220 bytes in / 1474 bytes out


Summing all this up and multiplying by 8 for the 8x peers that must be communiccated with:

- inbound: 2064 - 3344 bytes
- outbound: 12256 - 13376 bytes

These messages should occur roughly once per BLOCK_TIME (13 seconds)....


- Inbound Best

| Time             | Bandwidth |
| ---------------- | --------- |
| bytes-per-second | 158.77    |
| minute           | 9.3KB     |
| hour             | 558.2KB   |
| day              | 13.1MB    |
| week             | 91.6MB    |
| month            | 397.9MB   |
| year             | 4.7GB     |

- Inbound Worst

| Time             | Bandwidth |
| ---------------- | --------- |
| bytes-per-second | 257.23    |
| minute           | 15.1KB    |
| hour             | 904.3KB   |
| day              | 21.2MB    |
| week             | 148.4MB   |
| month            | 644.7MB   |
| year             | 7.6GB     |

- Outbound Best

| Time             | Bandwidth |
| ---------------- | --------- |
| bytes-per-second | 942.77    |
| minute           | 55.2KB    |
| hour             | 3.2MB     |
| day              | 77.7MB    |
| week             | 543.8MB   |
| month            | 2.3GB     |
| year             | 27.7GB    |

- Outbound Worst

| Time             | Bandwidth |
| ---------------- | --------- |
| bytes-per-second | 1028.92   |
| minute           | 60.3KB    |
| hour             | 3.5MB     |
| day              | 84.8MB    |
| week             | 593.5MB   |
| month            | 2.5GB     |
| year             | 30.2GB    |



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
