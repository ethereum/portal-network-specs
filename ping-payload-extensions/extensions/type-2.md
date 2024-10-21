# Portal State Network Distance

This payload is only supposed to be used for the state network

## version 1

Ping and Pong payload
```python
StateNetworkDistanceV1 = Container(
  type: 2,
  version: 1,
  payload: Container(data_radius: uint256)
)
```
