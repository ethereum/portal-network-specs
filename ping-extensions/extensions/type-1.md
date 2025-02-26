# Basic Radius Payload

A basic Ping/Pong payload which only contains the nodes radius

Ping and Pong Payload
```python

basic_radius = SSZ.serialize(Container(data_radius: U256))

Ping/Pong Message = Container(
  enr_seq: uint64,    
  type: 1,
  payload: basic_radius
)
```

## Test Vectors

### Protocol Message to ssz encoded ping

#### Input Parameters
```
enr_seq = 1
data_radius = 2^256 - 2 # Maximum value - 1
```

#### Expected Output
```
message = 0x00010000000000000001000e000000feffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff
```

### Protocol Message to ssz encoded pong

#### Input Parameters
```
enr_seq = 1
data_radius = 2^256 - 2 # Maximum value - 1
```

#### Expected Output
```
message = 0x01010000000000000001000e000000feffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff
```
