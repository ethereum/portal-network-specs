# Block header gossip v2
The document describes how the block information (accumulator & block headers) are exchanged between the portal network clients. 

Each client has the responsibilty to track the tip of the chain and to store accumulators and block header information locally. Clients will be sharing the information with requesting clients in the network to maintain the health of the network as a whole


## Block storage
Each client will be storing blocks in two forms. As accumulators where the entire block history is recorded and as partial block headers where only a subset of the block header is stored. Partial block headers only stored for the most recent N number of blocks.

### Accumulator
Portal network's accumulator will be based on the [double-batched merkle log accumulator](https://ethresear.ch/t/double-batched-merkle-log-accumulator/571) 

#### Epoch Accumulator
A fixed sized accumulator of a proposed length of 2048. Block info will be added in into the SSZ list until it has filled up all 2048 of its entries. After which the next block will be included in a new epoch accumulator.

SSZ sede structure:
`List[Container[blockhash:bytes32, total_difficulty:uint256 ], 2048]`

The root hash of an epoch will then be included as an entry in the master accumulator.

Aside from the first epoch,each client will need to store the current epoch as well as the epoch before in case of reorgs and block sync.

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
The distance function (if required if we opt for Idea no.2) will have the same definition as DiscV5

`distance(n₁, n₂) = n₁ XOR n₂`


## Wire Protocol
Custom message types will be encapsulated in the DiscV5 TalkReq/TalkResponse message

Custom message types are being proposed for the request and response of block header info


### Message Type

#### <u>RequestAccumulator</u>
Request accumulator info from neighbour

```
ContentKey: start_block: uint 
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

Neighbour will respond with RequestBlockHeader.

Message will be dropped after no response after a certain time period

```
ContentKey: block_number:uint256
```

## Node Responsibilities
WIP
# To Edit


## How does portal network gets to block header?
Bridge nodes which are joining the existing devp2p network will also be joining the portal network and will be responsible in 'pumping' in incoming block data.


## General idea
1. Bridge nodes will send block info to nodes within its radius
2. Nodes in turn will confirm if the block is valid (in the canonical chain and has a valid POW seal), add it to to running accumulator and propograte it to other nodes within its radius.
3. Nodes that received block info will not resend info back to nodes that provide this info


## Requirements
- Nodes need to have the ability to get info of master accumulator and epoch accumulator from other nodes. (hash and encoded ssz)


## Syncing process

There are 3 different scenarios of which a node may encounter

N is defined as the number of block headers which should be stored by each nodes in the portal network

- sync from the start (new nodes)
- Sync from only a few blocks away or when node has fully caught up to the chain tip (within N blocks away)
- Sync from more than N blocks away from the chaintip


## Sync for new nodes 
- Generate a random node id, and retrieve master and last 2 epoch acumulators from x number of nodes within a its distance
(* nodes should be storing the current epoch accumulator and the previous epoch accumulator)

- ![](https://i.imgur.com/DHASZSo.png)

neigboring nodes made returns epoch / master accumulators which can be longer or shorter

for majority of the case, the length of the master accumulator may be the same however the value in the last entry may be different (due to epoch accumulators not being filled up equally by all neigboring nodes, which is why i think getting the last 2 epoch accumulator is required)


compare the hashes of the epoch accumulator and master accumulator to ensure that the information we received are valid. 

in the lastest epoch, as the heights may not be the same due to network latency, we will try to find a common hash of the majority and store it

Where the common majority hash is in the same epoch
![](https://i.imgur.com/hVe20tP.png)


Where the common majority hash is in the previous epoch
![](https://i.imgur.com/PSswoId.png)



Heuristic approach is to 'trust' the result from majority of the nodes from which we verify that the hashes are valid.

The node will now have the information of the latest epoch accumulator (probably just a few blocks behind) and can start to ask or to receiving latest blocks from neighboring nodes. 

## Sync from only a few blocks away or when node has fully caught up to the chain tip

In this process, the block validity (POW seal) will be checked. 

Nodes are expected to store the current block header as well as the past N number of block headers in case other nodes may ask for blocks which are slightly away from the chain tip.

Each node thats receives a new block will validate the block's POW seal and add it into the latest epoch accumulator.

A block that has been successfully added will then be broadcasted to its neighbouring blocks to 'pass on' the message

If a receiving node receives a block which is slightly away, from its chain tip, the receiving node will request for blocknumber -1 until a common parent hash has been obtained. (Not more than N). Each blocks will then checked for its validity and be added to the epoch accumulator if its valid. 

If the receiving node already has a few blocks on top of the common parent hash, a reorg has occured and the reorged blocks will be purged from the epoch accumulator and the new master hash will be calculated and stored



If nodes ask for blocks with are more than N away from the chain tip (beyond the block header storage), nodes should indicate to the requesting node that a batch sync needs to take place.


## Sync from more than N blocks away from the chaintip
When a node realizes that the neighbouring node is asking
for a block that is N away from the chaintip, it will respond to the neighbour node to tell it to perform a 'batch sync'.

A batch sync will require that the node to request for epoch and master accumulator data similar to how a new node works. 

When the node is back within the N block range, it will then continue to request and validate the block headers
