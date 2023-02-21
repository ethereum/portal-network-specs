- Who specifically will use a Portal client?
- What are they using Portal to accomplish, or what pain are they trying to avoid?
- What is their current best alternative, and where does it fall short?


## Wallet (probably broken)

1. I'm an Ethereum wallet.  More specifically, I'm the developer of an Ethereum
wallet that wants to provide my users with a decentralized way to use my wallet
and interact with the Ethereum network.

2. I'm using the Portal Network to do things like:

A. fetching information about the most recent blocks to determine appropriate gas prices.  **PROBABLY WORKS**
B. looking up ETH and ERC20 token account balances.  **WILL BE SLOW**
C. simulating the gas for transactions I want to sign and send  **WILL BE SLOW**
D. Broadcasting transactions that I want to be included in a future block  **UNPROVEN**
E. monitoring the network for my transactions to be included.  **PROBABLY WORKS**

3. My current best alternative is a centralized provider.  It does the job
really well.  It falls short for ideological reasons, being a centralized
single point of failure, and exposing information about my users on-chain
activity.

## Four Fours

1. I'm EIP 4444.  More specifically, I'm the developer of an execution client
that wants to adopt EIP 4444.

2. I want to use the portal network for on-demand retrieval of historical block
data so that I can modify my client to no retain historical block data beyond a
certain time horizon.  When my client needs block data from before that time
horizon, it will use the portal network to fetch it. I want to use the portal
network because my client already uses the discovery v5 protocol (though I will
still need to include portal network specificic functionality).

3. My best decentralized alternative are bittorrent or IPFS based solutions.
These should work, though they require my client to add a new peer-to-peer
protocol.  


## Execution Client - Tracking Beacon Head

1. I'm an Execution Client.  More specifically, I'm the developer of an execution client.

2. I want to use the Portal Network to follow the beacon chain in order to also
follow the execution chain.  I'm trying to avoid having my users be required to
run both an execution client and a consensus layer client.

3. My current best alternative is to run a separate consensus layer client.
