# Capabilities Payload

Portal clients can only have max 500 extensions enabled per sub-network.

This payload provides a list of u16's each u16 provide in the list corresponds to an enabled extension type.

Ping and Pong Payload
```python

MAX_CAPABILITIES_LENGTH = 500

capabilities = SSZ.serialize(List[u16, MAX_CAPABILITIES_LENGTH])

BasicRadiusPayload = Container(
  type: 0,
  payload: capabilities
)
```

