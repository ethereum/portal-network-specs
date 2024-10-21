# Portal Transaction Gossip Network Distance

This payload is only supposed to be used for the Transaction Gossip network

## version 1

Ping and Pong payload
```python
Transaction GossipNetworkDistanceV1 = Container(
  type: 5,
  version: 1,
  payload: Container(data_radius: uint256)
)
```
