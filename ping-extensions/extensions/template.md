# [Title]

[Description]

Ping payload
```python

[Payload] = SSZ.serialize(Container([Key Value Pairs]))


Ping Message = Container(
  enr_seq: uint64,
  payload_type: [Type Number],
  payload: [Payload]
)
```

Pong payload
```python

[Payload] = SSZ.serialize(Container([Key Value Pairs]))

Pong Message = Container(
  enr_seq: uint64,
  payload_type: [Type Number],
  payload: [Payload]
)
```

## Test Vectors
