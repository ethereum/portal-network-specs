# Basic Radius Payload

A basic Ping/Pong payload which only contains the nodes radius

Ping and Pong Payload
```python

basic_radius = SSZ.serialize(Container(data_radius: U256))

BasicRadiusPayload = Container(
  type: 1,
  payload: basic_radius
)
```

