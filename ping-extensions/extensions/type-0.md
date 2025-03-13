# Client Info and Capabilities Payload

## Client Info 
Client info are UTF-8 hex encoded strings.

Client info strings consist of 4 parts
- client name (e.x. `trin`,`fluffy`)
- client version + short commit (e.x. `0.1.1-2b00d730`)
- operating system + cpu archtecture (e.x. `linux-x86_64`)
- programming language + language version (e.x. `rustc1.81.0`)

Example 
- String: `trin/0.1.1-2b00d730/linux-x86_64/rustc1.81.0`
- Hex encoding: `0x7472696E2F302E312E312D32623030643733302F6C696E75782D7838365F36342F7275737463312E38312E30`

#### Privacy Concerns
Clients can optionally return an empty string for privacy reasons, this is not recommended as client info helps researchers understand the network.

## Capabilities
Portal clients can only have max 400 extensions enabled per sub-network.

This payload provides a list of u16's each u16 provide in the list corresponds to an enabled extension type.

## Payload Outline

Ping and Pong Payload
```python

MAX_CLIENT_INFO_BYTE_LENGTH = 200
MAX_CAPABILITIES_LENGTH = 400

client_info_and_capabilities = SSZ.serialize(Container(
    client_info: ByteList[MAX_CLIENT_INFO_BYTE_LENGTH]
    data_radius: U256
    capabilities: List[u16, MAX_CAPABILITIES_LENGTH]
))

Ping/Pong Message = Container(
  enr_seq: uint64,
  type: 0,
  payload: client_info_and_capabilities
)
```

## Test Vectors

### Protocol Message to ssz encoded ping: case 1 with client info

#### Input Parameters
```
enr_seq = 1
data_radius = 2^256 - 2 # Maximum value - 1
client_info = "trin/v0.1.1-b61fdc5c/linux-x86_64/rustc1.81.0"
capabilities = [0, 1, 65535]
```

#### Expected Output
```
message = 0x00010000000000000000000e00000028000000feffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff550000007472696e2f76302e312e312d62363166646335632f6c696e75782d7838365f36342f7275737463312e38312e3000000100ffff
```

### Protocol Message to ssz encoded ping: case 2 without client info

#### Input Parameters
```
enr_seq = 1
data_radius = 2^256 - 2 # Maximum value - 1
client_info = ""
capabilities = [0, 1, 65535]
```

#### Expected Output
```
message = 0x00010000000000000000000e00000028000000feffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff2800000000000100ffff
```

### Protocol Message to ssz encoded pong: case 1 with client info

#### Input Parameters
```
enr_seq = 1
data_radius = 2^256 - 2 # Maximum value - 1
client_info = "trin/v0.1.1-b61fdc5c/linux-x86_64/rustc1.81.0"
capabilities = [0, 1, 65535]
```

#### Expected Output
```
message = 0x01010000000000000000000e00000028000000feffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff550000007472696e2f76302e312e312d62363166646335632f6c696e75782d7838365f36342f7275737463312e38312e3000000100ffff
```

### Protocol Message to ssz encoded pong: case 2 without client info

#### Input Parameters
```
enr_seq = 1
data_radius = 2^256 - 2 # Maximum value - 1
client_info = ""
capabilities = [0, 1, 65535]
```

#### Expected Output
```
message = 0x01010000000000000000000e00000028000000feffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff2800000000000100ffff
```
