# Block header gossip 
The document describes how the block information (accumulator & block headers) are exchanged between the portal network clients. 

Each client has the responsibilty to track the tip of the chain and to store accumulators and block header information locally. Clients will be sharing the information with requesting clients in the network to maintain the health of the network as a whole


## Block storage
Each client will be storing blocks in two forms. As accumulators where the entire block history is recorded and as partial block headers where only a subset of the block header is stored. Partial block headers only stored for the most recent N number of blocks.

### Accumulator
Portal network's accumulator will be based on the [double-batched merkle log accumulator](https://ethresear.ch/t/double-batched-merkle-log-accumulator/571) 

#### Epoch Accumulator
A fixed sized accumulator of a proposed length of 2048. Block info will be added in into the SSZ list until it has filled up all 2048 of its entries. After which the next block will be included in a new epoch accumulator.

SSZ sede structure:
`List[Container[blockhash:bytes32, total_difficulty:uint256], max_length=2048]`

The root hash of an epoch will then be included as an entry in the master accumulator.

Aside from the first epoch, each client will need to store the current epoch as well as the epoch before in case of reorgs and block sync.

#### Master Accumulator

An accumulator that increases in size with each epoch. The root hash of each epoch will be appended to the master accumulator

SSZ sede structure:
`List[epoch_root_hash:bytes32, <a_large_number>]`


### Partial Block Header

Client will need more information to verify the validity of the block. In the event of network latency, some clients may have missed out on the last few blocks and will need to request for the partial block header from its neighbours. 

And so, each client number will also be required to store a certain amount of the most recent blocks.

Partial Block Header will include:
- Block Number
- Block Hash
- Difficulty
- Nonce
- Mixhash
- Previous Hash (may be required to determine longest, heaviest chain. to know if the current block is pointed to the previous block)

## DHT
The block header gossip will be an overlay of [DiscV5](https://github.com/ethereum/devp2p/blob/master/discv5/discv5-theory.md).

#### <u>Idea No.1</u>
It is the responsibility of all clients in the portal network to have a local version of accumulator and block header. The block header gossip can reuse the ENR from the underlying DiscV5 protocol. The the maintenence of node liveness and node records are being done solely by DiscV5.

Information that are required by Block header gossip can be passed onto the overlay block header gossip layer in TalkReq/TalkResp encapsulated message.

Pros:
1. Able to reuse underlying DiscV5
2. Pass the responsibility of node maintence to DiscV5 and reduce additional message exchange

Cons:
1. Could be potentially too tightly coupled


#### <u>Idea No.2</u>
A seperate DHT for ENR's are being maintained in the overlay network. Similar messages such as PING, PONG, FINDNODES and FOUNDNODES will be used to maintained node liveness in the DHT. 

Pros:
1. Loosely coupled

Cons:
1. Repeat of DiscV5 since every client is expected to store the block header info anyway. Extra overhead

### Distance function
The distance function (will be required if we opt for Idea no.2) will have the same definition as in DiscV5

`distance(n₁, n₂) = n₁ XOR n₂`


## Wire Protocol
Custom message types will be encapsulated in the DiscV5 TalkReq/TalkResponse message

Custom message types are being proposed for the request and response of block header info


### Message Type

#### <u>RequestAccumulator</u>
Request accumulator info from neighbour

```
ContentKey: N/A
ContentId: TODO
````

#### <u>ResponseAccumulator</u>
Response to RequestAccumulator

```
ContentKey: payload
ContentType: uint8 (0 for epoch, 1 for master)


payload for content type 0: 0 | epoch_number:uint | List[Container[blockhash:bytes32, total_difficulty:uint256 ], 2048]

payload for content type 1 : 1 | List[epoch_root_hash:bytes32, <a_large_number>]
```

#### <u>RequestBlockHeaders</u>
Used by nodes to request for lastest numbers of blocks from its neighbour. Only for the last N blocks. Otherwise, neigbour node will request for the requesting node to request for accumulator instead.
```
ContentKey: start_block:uint
```

#### <u>ResponseBlockHeader</u>
Response to the requesting node's request if block number is within N block range. Else, tells the request node to request for an accumulator instead as the node is too far behind

```
ContentKey: status | payload

status: 0 (to request for accumulator), 1 (successful request)

payload(not present when status is 0): List[Container[partial_block_header], N: uint256]

partial_block_header: structure TBD

```



#### <u>OfferBlockHeader</u>
Offer block header to its neighbour when the node comes to know of an existence of a new valid block.

Interested neighbours will respond with `RequestBlockHeader`.

Message will be dropped after no response after a certain time period

```
ContentKey: block_number:uint256
```

## Node Responsibilities
- All nodes are required to store and manage their local copy of the master and epoch accumulators. 
- Each node will need to store the master accumulator and 2 latest epoch accumulators. 
- Each block that the node receives must be validated by checking the POW seal.
- Nodes are also required to store N most recent partial valid block headers and share this information to neighbour nodes who will be asking for them.
- Nodes will `OfferBlockHeader` to other nodes in the DHT once a block has been validated and added to its accumulator 

### Gossip rules


WIP

### Accumulator handling
Describes how accumulator is shared when a node first joined the portal network or when a node tried to catch up to the tip of the chain after being N blocks away 

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
Describes how a node handles reorg. Occurs when a node realizes a longer valid chain that has a different parent block hash.

WIP


