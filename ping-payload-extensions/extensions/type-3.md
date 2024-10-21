# Portal Beacon Network Distance

This payload is only supposed to be used for the beacon network

## version 1

Ping and Pong payload
```python
BeaconNetworkDistanceV1 = Container(
  type: 3,
  version: 1,
  payload: Container(data_radius: uint256)
)
```
