# [Title]

[Description]

Ping payload
```python

[Payload] = SSZ.serialize(Container([Key Value Pairs]))


[Container Name] = Container(
  type: [Type Number],
  payload: [Payload]
)
```

Pong payload
```python

[Payload] = SSZ.serialize(Container([Key Value Pairs]))

[Container Name] = Container(
  type: [Type Number],
  payload: [Payload]
)
```
