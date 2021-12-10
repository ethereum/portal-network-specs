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


The expected total traffic per the given time period for a node in the header gossip network is as follows:

| Period | Data-in           | Data-out          | Total             |
| ------ | ----------------- | ----------------- | ----------------- |
| minute | 3.5KB - 4.1KB     | 10.1KB - 10.7KB   | 13.5KB - 14.8KB   |
| hour   | 207.7KB - 245.6KB | 603.1KB - 640.9KB | 810.8KB - 886.5KB |
| day    | 4.9MB - 5.8MB     | 14.1MB - 15.0MB   | 19.0MB - 20.8MB   |
| week   | 34.1MB - 40.3MB   | 98.9MB - 105.2MB  | 133.0MB - 145.4MB |
| month  | 148.1MB - 175.1MB | 429.9MB - 456.9MB | 578.0MB - 632.0MB |
| year   | 1.7GB - 2.1GB     | 5.0GB - 5.4GB     | 6.8GB - 7.4GB     |



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


Summing all this up for a single peer:

- outbound: 1446-1586 bytes
- inbound: 146-306 bytes

and multiplying by 8 for the 8x peers that must be communicated with:

- outbound: 11568 - 12686 bytes
- inbound: 1168 - 2448 bytes

These messages should occur roughly once per BLOCK_TIME (13 seconds).  Extrapolating from this rate gives us the following numbers which represent the upper bounds on data transfer for a node in the network that **always** gossips the block header to 8 other peers.


- Inbound

| Period | Bandwidth         |
| ------ | ----------------- |
| minute | 5.3KB - 11.0KB    |
| hour   | 315.9KB - 662.0KB |
| day    | 7.4MB - 15.5MB    |
| week   | 51.8MB - 108.6MB  |
| month  | 225.2MB - 471.9MB |
| year   | 2.6GB - 5.5GB     |

- Outbound

| Period | Bandwidth         |
| ------ | ----------------- |
| minute | 52.1KB - 57.2KB   |
| hour   | 3.1MB - 3.4MB     |
| day    | 73.3MB - 80.4MB   |
| week   | 513.2MB - 562.9MB |
| month  | 2.2GB - 2.4GB     |
| year   | 26.1GB - 28.7GB   |


A more realistic estimate is that on average, each node in the network on average will only have a single peer ACCEPT the offered data.  Under this estimate:

- 7x who do not ACCEPT the data:
    - outbound: 784 bytes
    - inbound: 602 bytes
- 1x who does ACCEPT:
    - outbound: 1446-1586 bytes
    - inbound: 146-306 bytes

Giving an average expected bandwidth usage of:

- outbound: 2230-2370 bytes
- inbound: 748-908 bytes

Giving a monthly transfer of:


- Inbound (average)

| Period | Bandwidth         |
| ------ | ----------------- |
| minute | 3.4KB - 4.1KB     |
| hour   | 202.3KB - 245.6KB |
| day    | 4.7MB - 5.8MB     |
| week   | 33.2MB - 40.3MB   |
| month  | 144.2MB - 175.1MB |
| year   | 1.7GB - 2.1GB     |

- Outbound (average)

| Period | Bandwidth         |
| ------ | ----------------- |
| minute | 10.1KB - 10.7KB   |
| hour   | 603.1KB - 640.9KB |
| day    | 14.1MB - 15.0MB   |
| week   | 98.9MB - 105.2MB  |
| month  | 429.9MB - 456.9MB |
| year   | 5.0GB - 5.4GB     |




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

### Chain History Network

#### Storage

Data sourced from `geth db inspect` at block height `13663937`


| Item     | Size     |
| -------- | ---------|
| Headers  |   6.07GB |
| Bodies   | 183.06GB |
| Receipts |  92.51GB |
| -------- | -------- |
| Total    |  281.64  |

The growth rate here is dependent on the current gas limit which is subject to change.  At the current gas limit of 30 million:

Block Bodies sizes from the latest 100,000 blocks:

| Percentile | Size    | Size-Bytes |
| ---------- | ------- | ---------- |
| median     | 59.3KB  | 60774.5    |
| average    | 67.8KB  | 69434.3    |
| 1          | 539B    | 539        |
| 5          | 5.5KB   | 5611       |
| 10         | 10.3KB  | 10542.9    |
| 20         | 20.0KB  | 20432.8    |
| 30         | 31.1KB  | 31861      |
| 40         | 44.0KB  | 45066      |
| 50         | 59.3KB  | 60774.5    |
| 60         | 77.8KB  | 79681      |
| 70         | 97.8KB  | 100106     |
| 80         | 114.9KB | 117676     |
| 85         | 123.2KB | 126118     |
| 90         | 133.1KB | 136340     |
| 95         | 149.8KB | 153418     |
| 97         | 161.1KB | 164998     |
| 98         | 170.6KB | 174680     |
| 99         | 187.6KB | 192107     |
| 100        | 499.8KB | 511816     |

Block Receipt Sizes from the latest 10,000 blocks

| Percentile | Size    | Size-Bytes |
| ---------- | ------- | ---------- |
| median     | 94.5KB  | 96736      |
| average    | 110.3KB | 112985     |
| 1          | 1B      | 1          |
| 5          | 16.4KB  | 16825.8    |
| 10         | 23.3KB  | 23814.9    |
| 20         | 39.3KB  | 40255      |
| 30         | 56.8KB  | 58148.2    |
| 40         | 75.3KB  | 77140.4    |
| 50         | 94.5KB  | 96736      |
| 60         | 119.6KB | 122453     |
| 70         | 151.6KB | 155221     |
| 80         | 193.0KB | 197610     |
| 85         | 210.2KB | 215246     |
| 90         | 224.4KB | 229815     |
| 95         | 233.4KB | 239011     |
| 97         | 240.6KB | 246390     |
| 98         | 246.6KB | 252521     |
| 99         | 249.7KB | 255707     |
| 100        | 264.1KB | 270422     |


With a block time of 13 seconds, we expect roughly 2.5 million blocks per year

This gives us loose bounds on the annual data growth rate:

> Note: these numbers dont include compression


| Thing      | Average | Median  | 50th    | 70th    | 90th    | 95th    |
| ---------- | ------- | ------- | ------- | ------- | ------- | ------- |
| Headers    |   1.2GB |   1.2GB |   1.2GB |   1.2GB |   1.2GB |   1.2GB |
| Bodies     | 156.9GB | 137.3GB | 137.3GB | 226.2GB | 308.0GB | 346.7GB |
| Receipts   | 255.3GB | 218.6GB | 218.6GB | 350.7GB | 519.2GB | 540.0GB |
| ---------- | ------- | ------- | ------- | ------- | ------- | ------- |
| Total      | 413.4GB | 357.1GB | 357.1GB | 578.1GB | 828.4GB | 847.9GB |


Looking at these numbers we have 281GB of existing chain data and should expect to acquire as much as 350-800GB of new chain data over the next year.  For this reason we will use the number 1TB as our initial required amount of network storage.


Deriving required average storage sizes for the network is a function of:

- Total required non-replicated storage: 10TB
- Replication factor: 5x, 10x, 20x
- Number of nodes: 100, 250, 500, 1000, 10000, 50000, 100000, 500000, 1000000


| nodes / replication | storage |
| ------------------- | ------- |
| 100 / 5             | 51.2GB  |
| 100 / 10            | 102.4GB |
| 100 / 20            | 204.8GB |
| 250 / 5             | 20.5GB  |
| 250 / 10            | 41.0GB  |
| 250 / 20            | 81.9GB  |
| 500 / 5             | 10.2GB  |
| 500 / 10            | 20.5GB  |
| 500 / 20            | 41.0GB  |
| 1000 / 5            | 5.1GB   |
| 1000 / 10           | 10.2GB  |
| 1000 / 20           | 20.5GB  |
| 5000 / 5            | 1.0GB   |
| 5000 / 10           | 2.0GB   |
| 5000 / 20           | 4.1GB   |
| 10000 / 5           | 524.3MB |
| 10000 / 10          | 1.0GB   |
| 10000 / 20          | 2.0GB   |
| 50000 / 5           | 104.9MB |
| 50000 / 10          | 209.7MB |
| 50000 / 20          | 419.4MB |
| 100000 / 5          | 52.4MB  |
| 100000 / 10         | 104.9MB |
| 100000 / 20         | 209.7MB |
| 500000 / 5          | 10.5MB  |
| 500000 / 10         | 21.0MB  |
| 500000 / 20         | 41.9MB  |
| 1000000 / 5         | 5.2MB   |
| 1000000 / 10        | 10.5MB  |
| 1000000 / 20        | 21.0MB  |

#### Processing

- benchmark verification of header accumulator proof + header validation (POW check)
- benchmark block body validation
    - construction of transaction trie
    - construction of uncle trie
- benchmark receipts validation
    - construction of receipts trie
    
    
#### Bandwidth

Here are the expected numbers for gossip trafic


Block Headers: Single Gossip Iteration
| case        | packet-in | packet-out | bytes-in     | bytes-out     |
| ----------- | --------- | ---------- | ------------ | ------------- |
| lower-bound | 8         | 8          | 688B         | 896B          |
| upper-bound | 40 - 96   | 40 - 96    | 1.3KB - 984B | 11.1KB - 984B |
| average     | 12 - 19   | 12 - 19    | 768B - 1.1KB | 2.0KB - 2.3KB |

Block Headers: Usage

| Period | Data-in           | Data-out          | Total             |
| ------ | ----------------- | ----------------- | ----------------- |
| minute | 3.5KB - 4.1KB     | 10.1KB - 10.7KB   | 13.5KB - 14.8KB   |
| hour   | 207.7KB - 245.6KB | 603.1KB - 640.9KB | 810.8KB - 886.5KB |
| day    | 4.9MB - 5.8MB     | 14.1MB - 15.0MB   | 19.0MB - 20.8MB   |
| week   | 34.1MB - 40.3MB   | 98.9MB - 105.2MB  | 133.0MB - 145.4MB |
| month  | 148.1MB - 175.1MB | 429.9MB - 456.9MB | 578.0MB - 632.0MB |
| year   | 1.7GB - 2.1GB     | 5.0GB - 5.4GB     | 6.8GB - 7.4GB     |

Block Bodies: Single Gossip Iteration

| case        | packet-in   | packet-out  | bytes-in       | bytes-out       |
| ----------- | ----------- | ----------- | -------------- | --------------- |
| lower-bound | 8           | 8           | 688B           | 896B            |
| upper-bound | 568 - 3,728 | 568 - 3,728 | 11.6KB - 4.5KB | 554.1KB - 4.5KB |
| average     | 78 - 473    | 78 - 473    | 2.0KB - 10.0KB | 69.8KB - 77.8KB |

Block Bodies: Usage

| Period | Data-in          | Data-out          | Total             |
| ------ | ---------------- | ----------------- | ----------------- |
| minute | 9.4KB - 45.0KB   | 323.3KB - 358.9KB | 332.7KB - 403.9KB |
| hour   | 564.7KB - 2.6MB  | 18.9MB - 21.0MB   | 19.5MB - 23.7MB   |
| day    | 13.2MB - 63.3MB  | 454.6MB - 504.7MB | 467.9MB - 568.0MB |
| week   | 92.6MB - 443.1MB | 3.1GB - 3.5GB     | 3.2GB - 3.9GB     |
| month  | 402.5MB - 1.9GB  | 13.5GB - 15.0GB   | 13.9GB - 16.9GB   |
| year   | 4.7GB - 22.6GB   | 162.1GB - 179.9GB | 166.8GB - 202.5GB |

Receipt Bundle: Single Gossip Iteration

| case        | packet-in   | packet-out  | bytes-in       | bytes-out         |
| ----------- | ----------- | ----------- | -------------- | ----------------- |
| lower-bound | 8           | 8           | 688B           | 896B              |
| upper-bound | 912 - 6,056 | 912 - 6,056 | 18.3KB - 6.8KB | 901.0KB - 6.8KB   |
| average     | 121 - 764   | 121 - 764   | 2.9KB - 15.6KB | 113.2KB - 126.0KB |

Receipt Bundle: Usage

| Period | Data-in           | Data-out          | Total             |
| ------ | ----------------- | ----------------- | ----------------- |
| minute | 13.3KB - 71.2KB   | 523.5KB - 581.4KB | 536.8KB - 652.7KB |
| hour   | 797.2KB - 4.2MB   | 30.7MB - 34.1MB   | 31.5MB - 38.2MB   |
| day    | 18.7MB - 100.2MB  | 736.1MB - 817.6MB | 754.8MB - 917.8MB |
| week   | 130.8MB - 701.4MB | 5.0GB - 5.6GB     | 5.2GB - 6.3GB     |
| month  | 568.3MB - 3.0GB   | 21.9GB - 24.3GB   | 22.4GB - 27.3GB   |
| year   | 6.7GB - 35.7GB    | 262.4GB - 291.4GB | 269.1GB - 327.2GB |


- gossip messages need to have accumulator proof included.
- expected gossip message volume for full radius node, move down from there.


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
