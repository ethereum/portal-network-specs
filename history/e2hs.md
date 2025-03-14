# e2hs (Portal Network History Storage Format)

## Purpose
`e2hs` is a file format designed to store Portal Network history data. It is based on the [`e2store`](https://github.com/status-im/nimbus-eth2/blob/613f4a9a50c9c4bd8568844eaffb3ac15d067e56/docs/e2store.md) format and draws inspiration from the `era1` format, with modifications to meet Portal Network history data requirements. This format covers all history network data pre & post merge, except for data in the ephemeral range (eg. head - 8192).

Each `e2hs` file corresponds to an epoch (8,192 blocks) and contains a sequence of block data including:
- Header with proofs
- Block bodies 
- Transaction receipts

## Key Features
- Pre-generated header proofs to reduce computational overhead during gossip
- Post-merge receipt storage (not available in era files)
- Compressed storage format
- Indexed block access
- Support for all Portal History Network content types, except for ephemeral headers, which are out of scope for this file format.

## File Format Specification

### File Naming Convention
`<config-name>-<era-number>-<short-historical-root>.e2hs`

Where:
- `config-name`: Network configuration identifier (e.g., mainnet, sepolia)
- `era-number`: Sequential epoch identifier
- `short-historical-root`: Truncated root hash of the accumulator

### Structure

The file format is defined as:

```
    e2hs := Version | BlockTuple* | OtherEntry* | Accumulator | BlockIndex
    BlockTuple := CompressedHeader | CompressedBody | CompressedReceipts
    -----
    Version := {type: 0x3265,          data: nil}
    CompressedHeader := {type: 0x03,   data: snappyFramed(rlp(HeaderWithProof))}
    CompressedBody := {type: 0x04,     data: snappyFramed(rlp(BlockBody))}
    CompressedReceipts := {type: 0x05, data: snappyFramed(rlp(Receipts))}
    Accumulator := {type: 0x06,        data: hash_tree_root(List(block_hash, 8192))}
    BlockIndex := {type: 0x3266,       data: block-index}
    block-index := starting-number | index | index | index ... | count
```

### Validation
A valid e2hs file must:
1. Begin with the correct version identifier (0x3265)
2. Contain exactly 8,192 blocks (one epoch)
3. Include all required components for each block
4. End with a valid accumulator and block index
5. Maintain sequential block ordering
6. **Not** contain any ephemeral data (eg. head - 8192)
