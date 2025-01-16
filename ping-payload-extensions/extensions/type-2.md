# History Radius Payload

A specialized radius payload for the history network which contains field for how many ephemeral headers the node holds.

Ping and Pong Payload
```python

history_radius = SSZ.serialize(Container(data_radius: U256, ephemeral_header_count=U16))

Ping/Pong Message = Container(
  enr_seq: uint64,    
  type: 2,
  payload: history_radius
)
```

## Test Vectors

### Protocol Message to ssz encoded ping

#### Input Parameters
```
enr_seq = 1
data_radius = 2^256 - 2 # Maximum value - 1
ephemeral_header_count = 4242
```

#### Expected Output
```
message = 0x00010000000000000002000e000000feffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff9210
```

### Protocol Message to ssz encoded pong

#### Input Parameters
```
enr_seq = 1
data_radius = 2^256 - 2 # Maximum value - 1
ephemeral_header_count = 4242
```

#### Expected Output
```
message = 0x01010000000000000002000e000000feffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff9210
```
