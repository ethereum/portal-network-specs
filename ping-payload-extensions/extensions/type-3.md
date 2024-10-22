# Get Client info

This payload is only supposed to be usable from all Networks. This payload allows you to figure out peer's client info. Which will be useful for censuses.


### Type Specifications

Client info are ASCII hex encoded strings.

Client info strings consist of 4 parts
- client name (e.x. `trin`,`fluffy`)
- client version + short commit (e.x. `0.1.1-2b00d730`)
- operating system + cpu archtecture (e.x. `linux-x86_64`)
- programming language + language version (e.x. `rustc1.81.0`)

Example 
- String: `trin/0.1.1-2b00d730/linux-x86_64/rustc1.81.0`
- Hex encoding: `0x7472696E2F302E312E312D32623030643733302F6C696E75782D7838365F36342F7275737463312E38312E30`


Max length of a client info we should accept
- MAX_CLIENT_INFO_BYTE_LENGTH = 200


Ping and Pong payload
```python

client_info = SSZ.serialize(Container(client_info: ByteList[MAX_CLIENT_INFO_BYTE_LENGTH]))

ClientInfoPayload = Container(
  type: 3,
  payload: client_info
)
```
