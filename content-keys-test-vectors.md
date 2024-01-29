# Content Keys Test Vectors

This document contains test vectors for content keys to help implementations conform to the specification. 

Note: Currently, endianness is underspecified in the spec. These test vectors
assume BE when converting hash to id (u256) and also BE when taking the slot
(U256) and converting it to a byte array for hashing.

## Content Keys Encodings

These test vectors verify the proper SSZ encoding and decoding of content keys
as specified in the history and state network specs.

## Content Id Derivations

Following the testing of the encoding and decoding of the keys, we also test the proper derivation
of the corresponding `content-id`. This is given as both the hex string and corresponding raw U256 integer.

### State Network Keys

See [State Network Test Vectors](./state-network-test-vectors.md) page for details on these test vectors.

#### Account Trie Node Key

##### Input Parameters
```
path = [8, 6, 7, 9, 14, 8, 14, 13]
node_hash = 0x6225fcc63b22b80301d9f2582014e450e91f9b329b7cc87ad16894722fff5296
```

##### Expected Output
```
content_key = 0x20240000006225fcc63b22b80301d9f2582014e450e91f9b329b7cc87ad16894722fff529600050000008679e8ed
content_id = 0xefe4deaeda9a0a5701c949789edc5aac1b000ffb9792cb72ee288a3961746cec
content_id: U256 = 108507148843911294162476026997514952231509817597300850566428974289904710479084
```

#### Contract Storage Trie Node Key

##### Input Parameters
```
address = 0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2
path = [4, 0, 5, 7, 8, 7]
node_hash = 0xeb43d68008d216e753fef198cf51077f5a89f406d9c244119d1643f0f2b19011
```

##### Expected Output
```
content_key = 0x21c02aaa39b223fe8d0a0e5c4f27ead9083c756cc238000000eb43d68008d216e753fef198cf51077f5a89f406d9c244119d1643f0f2b190110005000000405787
content_id = 0xc95bbd117a8028c9663f1f8471135d2d9f05afddd8a9e12c81161113dff2c293
content_id: U256 = 91076970549410835066271491207747309001404436114077821232127034545703864156819
```

#### Contract Bytecode Key

##### Input Parameters
```
address = 0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2
code_hash = 0xd0a06b12ac47863b5c7be4185c2deaad1c61557033f56c7d4ea74429cbb25e23
```

##### Expected Output
```
content_key = 0x22c02aaa39b223fe8d0a0e5c4f27ead9083c756cc2d0a06b12ac47863b5c7be4185c2deaad1c61557033f56c7d4ea74429cbb25e23
content_id = 0x142f9d1bc05985f5316144e465a62bd646bb51128d8361fef49ae5de397eca99
content_id: U256 = 9130383106061705701162781228778634508369497435982686447872496028728850041497
```

### History Network Keys

#### Block Header Key

##### Input Parameters
```
block_hash = 0xd1c390624d3bd4e409a61a858e5dcc5517729a9170d014a6c96530d64dd8621d
```

##### Expected Output
```
content_key = 0x00d1c390624d3bd4e409a61a858e5dcc5517729a9170d014a6c96530d64dd8621d
content_id = 0x3e86b3767b57402ea72e369ae0496ce47cc15be685bec3b4726b9f316e3895fe
content_id: U256 = 28281392725701906550238743427348001871342819822834514257505083923073246729726
```

#### Block Body Key

##### Input Parameters
```
block_hash = 0xd1c390624d3bd4e409a61a858e5dcc5517729a9170d014a6c96530d64dd8621d
```

##### Expected Output
```
content_key = 0x01d1c390624d3bd4e409a61a858e5dcc5517729a9170d014a6c96530d64dd8621d
content_id = 0xebe414854629d60c58ddd5bf60fd72e41760a5f7a463fdcb169f13ee4a26786b
content_id: U256 = 106696502175825986237944249828698290888857178633945273402044845898673345165419
```

#### Receipt Key

##### Input Parameters
```
block_hash = 0xd1c390624d3bd4e409a61a858e5dcc5517729a9170d014a6c96530d64dd8621d
```

##### Expected Output
```
content_key = 0x02d1c390624d3bd4e409a61a858e5dcc5517729a9170d014a6c96530d64dd8621d
content_id = 0xa888f4aafe9109d495ac4d4774a6277c1ada42035e3da5e10a04cc93247c04a4
content_id: U256 = 76230538398907151249589044529104962263309222250374376758768131420767496438948
```

#### Epoch Accumulator Key

##### Input Parameters
```
epoch_hash = 0xe242814b90ed3950e13aac7e56ce116540c71b41d1516605aada26c6c07cc491
```

##### Expected Output
```
content_key = 0x03e242814b90ed3950e13aac7e56ce116540c71b41d1516605aada26c6c07cc491
content_id = 0x9fb2175e76c6989e0fdac3ee10c40d2a81eb176af32e1c16193e3904fe56896e
content_id: U256 = 72232402989179419196382321898161638871438419016077939952896528930608027961710
```
