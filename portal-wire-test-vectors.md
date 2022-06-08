# Portal Wire Test Vectors

This document provides a collection of test vectors for the Portal wire protocol
aimed to aid new implementations to conform to the specification.

## Protocol Message Encodings

This section provides test vectors for the individual protocol messages defined
in the [Portal wire protocol](./portal-wire-protocol.md). These test vectors can
primarily verify the SSZ encoding and decoding of each protocol message.

### Ping Request

#### Input Parameters
```
enr_seq = 1
data_radius = 2^256 - 2 # Maximum value - 1
custom_payload = serialize(Container(data_radius))
```

#### Expected Output
```
message = 0x0001000000000000000c000000feffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff
```

### Pong Response

#### Input Parameters
```
enr_seq = 1
data_radius = (2^256 - 1) / 2 # Maximum value / 2
custom_payload = serialize(Container(data_radius))
```

#### Expected Output
```
message = 0x0101000000000000000c000000ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff7f
```

### Find Nodes Request

#### Input Parameters
```
distances = [256, 255]
```

#### Expected Output
```
message = 0x02040000000001ff00
```

### Nodes Response - Empty enrs

#### Input Parameters
```
total = 1
enrs = []
```

#### Expected Output
```
message = 0x030105000000
```

### Nodes Response - Multiple enrs

#### Input Parameters
```
enr1 = "enr:-HW4QBzimRxkmT18hMKaAL3IcZF1UcfTMPyi3Q1pxwZZbcZVRI8DC5infUAB_UauARLOJtYTxaagKoGmIjzQxO2qUygBgmlkgnY0iXNlY3AyNTZrMaEDymNMrg1JrLQB2KTGtv6MVbcNEVv0AHacwUAPMljNMTg"

enr2 = "enr:-HW4QNfxw543Ypf4HXKXdYxkyzfcxcO-6p9X986WldfVpnVTQX1xlTnWrktEWUbeTZnmgOuAY_KUhbVV1Ft98WoYUBMBgmlkgnY0iXNlY3AyNTZrMaEDDiy3QkHAxPyOgWbxp5oF1bDdlYE6dLCUUp8xfVw50jU"

total = 1
enrs = [enr1, enr2]
```

#### Expected Output
```
message = 0x030105000000080000007f000000f875b8401ce2991c64993d7c84c29a00bdc871917551c7d330fca2dd0d69c706596dc655448f030b98a77d4001fd46ae0112ce26d613c5a6a02a81a6223cd0c4edaa53280182696482763489736563703235366b31a103ca634cae0d49acb401d8a4c6b6fe8c55b70d115bf400769cc1400f3258cd3138f875b840d7f1c39e376297f81d7297758c64cb37dcc5c3beea9f57f7ce9695d7d5a67553417d719539d6ae4b445946de4d99e680eb8063f29485b555d45b7df16a1850130182696482763489736563703235366b31a1030e2cb74241c0c4fc8e8166f1a79a05d5b0dd95813a74b094529f317d5c39d235
```

### Find Content Request

#### Input Parameters
```
content_key = 0x706f7274616c
```

#### Expected Output
```
message = 0x0404000000706f7274616c
```

### Content Response - Connection id

#### Input Parameters
```
connection_id = [0x01, 0x02]
```

#### Expected Output
```
message = 0x05000102
```

### Content Response - Content payload

#### Input Parameters
```
content = 0x7468652063616b652069732061206c6965
```

#### Expected Output
```
message = 0x05017468652063616b652069732061206c6965
```

### Content Response - Multiple enrs

#### Input Parameters
```
enr1 = "enr:-HW4QBzimRxkmT18hMKaAL3IcZF1UcfTMPyi3Q1pxwZZbcZVRI8DC5infUAB_UauARLOJtYTxaagKoGmIjzQxO2qUygBgmlkgnY0iXNlY3AyNTZrMaEDymNMrg1JrLQB2KTGtv6MVbcNEVv0AHacwUAPMljNMTg"

enr2 = "enr:-HW4QNfxw543Ypf4HXKXdYxkyzfcxcO-6p9X986WldfVpnVTQX1xlTnWrktEWUbeTZnmgOuAY_KUhbVV1Ft98WoYUBMBgmlkgnY0iXNlY3AyNTZrMaEDDiy3QkHAxPyOgWbxp5oF1bDdlYE6dLCUUp8xfVw50jU"

enrs = [enr1, enr2]
```

#### Expected Output
```
message = 0x0502080000007f000000f875b8401ce2991c64993d7c84c29a00bdc871917551c7d330fca2dd0d69c706596dc655448f030b98a77d4001fd46ae0112ce26d613c5a6a02a81a6223cd0c4edaa53280182696482763489736563703235366b31a103ca634cae0d49acb401d8a4c6b6fe8c55b70d115bf400769cc1400f3258cd3138f875b840d7f1c39e376297f81d7297758c64cb37dcc5c3beea9f57f7ce9695d7d5a67553417d719539d6ae4b445946de4d99e680eb8063f29485b555d45b7df16a1850130182696482763489736563703235366b31a1030e2cb74241c0c4fc8e8166f1a79a05d5b0dd95813a74b094529f317d5c39d235
```

### Offer Request

#### Input Parameters
```
content_key1 = 0x010203
content_keys = [content_key1]
```

#### Expected Output
```
message = 0x060400000004000000010203
```

### Accept Response

#### Input Parameters
```
connection_id = [0x01, 0x02]
content_keys = [1, 0, 0, 0, 0, 0, 0, 0] # 8 bits bitlist, 0 bit set = byte 0x01
```

#### Expected Output
```
message = 0x070102060000000101
```
