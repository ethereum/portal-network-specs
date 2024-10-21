# Portal History Network Distance

This payload is only supposed to be used for the history network

## version 1

Ping and Pong Payload
```python
HistoryNetworkDistanceV1 = Container(
  type: 1,
  version: 1,
  payload: Container(data_radius: uint256)
)
```

## version 2
Ping and Pong Payload
```python
HistoryNetworkDistanceV2 = Container(
  type: 1,
  version: 2,
  payload: Container(data_radius: uint256, ephemeral_header_count: uint16)
)
```
