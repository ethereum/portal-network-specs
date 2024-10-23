# Capabilities Payload

Any network can only have Portal client can only every have 500 extensions enabled per Portal sub-networks.

This payload provides a list of u16's each u16 provide in the list corresponds to an an enabled extension type.

Ping and Pong Payload
```python

MAX_CAPABILITIES_LENGTH = 500

capabilities = SSZ.serialize(List[u16, MAX_CAPABILITIES_LENGTH])

BasicRadiusPayload = Container(
  type: 0,
  payload: capabilities
)
```

