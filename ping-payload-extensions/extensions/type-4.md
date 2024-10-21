# Portal Canonical Transaction Index Network Distance

This payload is only supposed to be used for the Canonical Transaction Index Network

## version 1

Ping and Pong payload
```python
CanonicalTransactionIndexNetworkDistanceV1 = Container(
  type: 4,
  version: 1,
  payload: Container(data_radius: uint256)
)
```
