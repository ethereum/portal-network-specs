# Header Gossip Network Test Vectors

This document contains test vectors for the Header Gossip Network to help implementations conform to the specification.

## Header Accumulator Encodings

These test vectors specify the proper encoding of the header accumulator in certain well defined scenarios

### Epoch 0 Accumulator

#### Accumulator after genesis block

This test vector represents the input parameters and the expected output for the current epoch accumulator after adding
the genesis block from Ethereum Mainnet.

##### Input Parameters
```
genesis block hash = 0x88e96d4537bea4d9c05d12549907b32561d3bf31f45aae734cdc119f13406cb6
genesis block difficulty = 17171480576
```
##### Expected Output
```
accumulator hash root = 0x1978df242d723405f28d26184e57ccf1938b253ef08234bfeb4951abdf3bbe4c
```

#### Current Epoch Accumulator after Block 2
This test vector represents the input parameters and the expected output for the current epoch accumulator after adding
block 2 from Ethereum Mainnet.

##### Input Parameters
```
block 2 hash = 0xb495a1d7e6663152ae92708da4843337b958146015a2802f4193a410044698c9
block 2 difficulty = 17163096064
```
##### Expected Output
```
accumulator hash root = 0x90cc48e39fe7062a3e5b6a3e78ff1f01544c22b87c6453cd718a1e5fe5ed8fa9
```
