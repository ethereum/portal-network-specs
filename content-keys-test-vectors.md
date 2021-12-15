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
content_id = 0x5b2b5ea9a7384491010c1aa459a0f967dcf8b69988adbfe7e0bed513e9bb8305
content_id: U256 = 41237096982860596884042712109427867048220765019203857308279863638242761605893
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
content_id = 0x603cbe7902925ce359822378a4cb1b4b53e1bf19d003de2c26e55812d76956c1
content_id: U256 = 43529358882110548041037387588279806363134301284609868141745095118932570363585
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
content_id = 0x6427c4c8d42db15c2aca8dfc7dff7ce2c8c835441b566424fa3377dd031cc60d
content_id: U256 = 45301550050471302973396879294932122279426162994178563319590607565171451545101
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
content_id = b1c89984803cebd325303ba035f9c4ca0d0d91b2cbfef84d455e7a847ade1f08
content_id: U256 = 80413803151602881485894828440259195604313253842905231566803078625935967002376
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
content_id = 0x146fb937afe42bcf11d25ad57d67734b9a7138677d59eeec3f402908f54dafb0
content_id: U256 = 9243655320250466575533858917172702581481192615849913473767356296630272634800
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
content_id = 0x2137f185b713a60dd1190e650d01227b4f94ecddc9c95478e2c591c40557da99
content_id: U256 = 15025167517633317571792618561170587584740338038067807801482118109695980329625
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
content_id = 0x1c6046475f0772132774ab549173ca8487bea031ce539cad8e990c08df5802ca
content_id: U256 = 12834862124958403129911294156243112356210437741210740000860318140844473844426
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
content_id = 0xaa39e1423e92f5a667ace5b79c2c98adbfd79c055d891d0b9c49c40f816563b2
content_id: U256 = 76995449220721979583200368506411933662679656077191192504502358532083948020658
```

