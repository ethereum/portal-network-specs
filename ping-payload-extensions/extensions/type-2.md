# History Radius Payload

A specialized radius payload for the history network which contains field for how many ephemeral headers the node holds.

Ping and Pong Payload
```python

history_radius = SSZ.serialize(Container(data_radius: U256, ephemeral_header_count=U16))

Ping/Pong Message = Container(
  enr_seq: uint64,    
  type: 2,
  payload: history_radius
)
```
