# Ping Custom Payload Extensions

## The problem

Over time we will need to change what is sent over ping/pong `custom_payload`'s to adjust for what is needed in the future.
Currently the only way to update a `custom_payload` is through breaking changes which break protocol compatible between Portal implementations.
As we get users, deploying breaking changes to mainnet will no longer be an option as we are aiming for a 100% uptime.

## The Solution

Ping Custom Payload Extensions. A versioned type prefixed format where we can upgrade endpoints on a new version well giving a window for all Portal implementations to update before deprecating the older version. This will allow clients to implement new functionality without breaking compatibility with the standard specification.

# Type's

There are 4_294_967_296 unique type ids.

Types 0-10_000 and 4_294_957_295-4_294_967_296 are reserved for for future upgrades.

The rest are first come first serve, but they should still be defined in this repo to avoid overlaps.


## Requirements

All payloads used in the Ping `custom_payload` MUST follow the `Ping Custom Payload Extensions` format.

## Custom Payload Extensions Format

- **type**: what payload type is it
- **verison**: what version of the type it is
- **payload**: a ssz container which contents are specified by the type and version field


```python
CustomPayloadExtensionsFormat = Container(
  type: Bytes4,
  version: Bytes4,
  payload: Container(inner payload is defined by type and version)
)
```

## Ping vs Pong
The relationship between Ping and Pong message will be determined by the requirements of the type/version.

Currently type 1,2,3 are mirrored formats, but there is room for a Ping `custom_payload` to specify details about what it wants to request, then pong handles it.


### Error responses
If the ping receiver can't handle the ping for any reason the pong should return an error payload

Pong payload
```python

# Max ASCII hex encoded strings length
MAX_ERROR_BYTE_LENGTH = 300

CustomPayloadExtensionsFormat = Container(
  type: 4_294_967_295,
  version: 1,
  payload: Container(error_code: Bytes4, message: ByteList[MAX_ERROR_BYTE_LENGTH])
)
```

### Error Code's

- 0: Extension not supported
- 1: Requested data not found
- 2: System error
