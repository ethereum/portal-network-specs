# Content Keys Test Vectors

This document contains test vectors for content keys to help implementations conform to the specification. 

## Content Keys Encodings

These test vectors verify the proper SSZ encoding and decoding of content keys
as specified in the history and state network specs.

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
content_key = 0x01829bd824b016326a401d083b33d092293333a830580000003e190b68719aecbcb28ed2271014dd25f2aa633184988eb414189ce0899cade5d1c390624d3bd4e409a61a858e5dcc5517729a9170d014a6c96530d64dd8621d01000f0e0c00
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

