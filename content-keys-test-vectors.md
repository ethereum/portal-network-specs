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
