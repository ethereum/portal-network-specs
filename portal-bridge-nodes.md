# Bridge Node JSON-RPC Interface

### Original Link: https://notes.ethereum.org/@lithp/r1NB6M4Gu
### Author: @lithp
### Created: 2021-02-24

# Description
Bridge nodes push state into the state availability network. They need to be in communication with an eth1 full node, here is a protocol they could use.

### Bridge nodes will send two kinds of messages:
- (ingress) an account/slot has some value
	- This is useful for adding new accounts/slots to the network, updating existing accounts/slots, as well as for re-inserting cold accounts/slots which the network might have forgotten
- (egress) an account/slot has been removed
	- The state availability network is not an archive node, it only stores the last x⪅1000 state tries. A recent proof of non-inclusion is enough to convince the network to drop data.
	- There is some logic to selectively ignore these messages. If the account is brand new it’s possible to construct a recent non-inclusion proof but that proof is not relevant.

# API
### To do this they will rely on a few different RPCs:
- `bridge_waitNewCanonicalChain()`
	- Blocks the caller until the canonical chain tip changes (indicating there is more work to be done).

- `bridge_getBlockChanges(blockHash) -> List[(acctAddr, [slotAddr, ...])]`
	- Returns a list containing every account/slot which was created, updated, or deleted in the given block.
	- Return type mirrors [eth1 mainnet access list API](https://eips.ethereum.org/EIPS/eip-2930#definitions)
		- Accounts are represented by `(acctAddr, [])`
		- Storage slots are represented by `(acctAddr, [slotAddr, ...])`

- `bridge_getItemWitness(blockHash, acctAddr, slotAddr) -> List[Bytes]`
	- Returns a list of RLP-encoded nodes starting with the root node and ending with the requested node.
	- If the account was deleted this returns a proof-of-non-inclusion, and the final node will be `null`.
	- If `slotAddr` is `null` this method returns a witness for the requested account.

- `bridge_getNextItem(blockHash, acctAddr, slotAddr) -> [acctAddr, slotAddr]`
	- Used for scanning through the state to find cold items which ought to be re-inserted into the network.

- `bridge_getNextItem(blockHash, '0x0', null)` will return the the lowest (hashed) address, throwing that address back into `bridge_getNextItem` will return the next address.
	- Returns `null` if there is no next address/slot.
