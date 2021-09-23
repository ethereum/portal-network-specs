# Block Header Gossip

Block info that needs to be passed around
- Block Number
- Block Hash
- Difficulty
- Nonce
- Mixhash
- Previous Hash (may be required to determine longest, heaviest chain. to know if the current block is pointed to the previous block)

Nonce and mixhash will be used to verify POW seal. (to be replaced after the merge?) along with block number and block hash


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
