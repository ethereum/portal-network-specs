# Content Keys Test Vectors

This document contains test vectors for content keys to help implementations conform to the specification. 

## Content Keys Encodings

These test vectors verify the proper SSZ encoding and decoding of content keys
as specified in the history and state network specs.

## Content Id Derivations

Following the testing of the encoding and decoding of the keys, we also test the proper derivation
of the corresponding `content-id`. This is given as a raw U256 integer.

### State Network Keys

#### AccountTrieNode

##### Input Parameters
```
path = [1,2,0,1]
node_hash = 0xb8be7903aee73b8f6a59cd44a1f52c62148e1f376c0dfa1f5f773a98666efc2b
state_root = 0xd1c390624d3bd4e409a61a858e5dcc5517729a9170d014a6c96530d64dd8621d
```

##### Expected Output
```
content_key = 0x0044000000b8be7903aee73b8f6a59cd44a1f52c62148e1f376c0dfa1f5f773a98666efc2bd1c390624d3bd4e409a61a858e5dcc5517729a9170d014a6c96530d64dd8621d01020001
content_id = 47897795058347058605412668629651179584081164718037256665467324407551262019119
```

#### ContractStorageTrieNode

##### Input Parameters
```
address = 0x829bd824b016326a401d083b33d092293333a830
path = [1, 0, 15, 14, 12, 0]
node_hash = 0x3e190b68719aecbcb28ed2271014dd25f2aa633184988eb414189ce0899cade5
state_root = 0xd1c390624d3bd4e409a61a858e5dcc5517729a9170d014a6c96530d64dd8621d
```

##### Expected Output
```
content_key = 0x01829bd824b016326a401d083b33d092293333a830580000003e190b68719aecbcb28ed227i1014dd25f2aa633184988eb414189ce0899cade5d1c390624d3bd4e409a61a858e5dcc5517729a9170d014a6c96530d64dd8621d01000f0e0c00
content_id = 25680383300664040273242561870690068993412664133017293325738180250066184811418
```

#### AccountTrieProof

##### Input Parameters
```
address = 0x829bd824b016326a401d083b33d092293333a830
state_root = 0xd1c390624d3bd4e409a61a858e5dcc5517729a9170d014a6c96530d64dd8621d 
```

##### Expected Output
```
content_key = 0x02829bd824b016326a401d083b33d092293333a830d1c390624d3bd4e409a61a858e5dcc5517729a9170d014a6c96530d64dd8621d
content_id = 43465612782205511670822123236532824350432587419315966553603081916412044245142
```

#### ContractStorageTrieProof

##### Input Parameters
```
address = 0x829bd824b016326a401d083b33d092293333a830
slot = U256(239304)
state_root = 0xd1c390624d3bd4e409a61a858e5dcc5517729a9170d014a6c96530d64dd8621d
```

##### Expected Output
```
content_key = 0x03829bd824b016326a401d083b33d092293333a830c8a6030000000000000000000000000000000000000000000000000000000000d1c390624d3bd4e409a61a858e5dcc5517729a9170d014a6c96530d64dd8621d
content_id = 79658526332306414556395474549365643323764436888599322145395883955218537063092
```

#### ContractBytecode

##### Input Parameters
```
address = 0x829bd824b016326a401d083b33d092293333a830
code_hash = 0xd1c390624d3bd4e409a61a858e5dcc5517729a9170d014a6c96530d64dd8621d
```

##### Expected Output
```
content_key = 0x04829bd824b016326a401d083b33d092293333a830d1c390624d3bd4e409a61a858e5dcc5517729a9170d014a6c96530d64dd8621d
content_id = 31267377065281845690157498188438069085695127970365917173070983743319684416958
```

### History Network Keys

#### HeaderKey

##### Input Parameters
```
chain_id = 15
block_hash = 0xd1c390624d3bd4e409a61a858e5dcc5517729a9170d014a6c96530d64dd8621d
```

##### Expected Output
```
content_key = 0x000f00d1c390624d3bd4e409a61a858e5dcc5517729a9170d014a6c96530d64dd8621d
```

#### BodyKey

##### Input Parameters
```
chain_id = 20
block_hash = 0xd1c390624d3bd4e409a61a858e5dcc5517729a9170d014a6c96530d64dd8621d
```

##### Expected Output
```
content_key = 0x011400d1c390624d3bd4e409a61a858e5dcc5517729a9170d014a6c96530d64dd8621d
```

#### ReceiptsKey

##### Input Parameters
```
chain_id = 4
block_hash = 0xd1c390624d3bd4e409a61a858e5dcc5517729a9170d014a6c96530d64dd8621d
```

##### Expected Output
```
content_key = 0x020400d1c390624d3bd4e409a61a858e5dcc5517729a9170d014a6c96530d64dd8621d
```

