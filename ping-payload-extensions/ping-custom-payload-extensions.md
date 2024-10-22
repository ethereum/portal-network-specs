# Ping Custom Payload Extensions

## The problem

Over time we will need to change what is sent over ping/pong `custom_payload`'s to adjust for what is needed in the future.
Currently the only way to update a `custom_payload` is through breaking changes which break protocol compatible between Portal implementations.
As we get users, deploying breaking changes to mainnet will no longer be an option as we are aiming for a 100% uptime.

## The Solution

Ping Custom Payload Extensions. A versioned type prefixed format where we can upgrade endpoints on a new version well giving a window for all Portal implementations to update before deprecating the older version. This will allow clients to implement new functionality without breaking compatibility with the standard specification.

# Type's

There are 65536 unique type ids.

Types 0-10_000 and 65436-65535 are reserved for for future upgrades.

The rest are first come first serve, but they should still be defined in this repo to avoid overlaps.


## Requirements

All payloads used in the Ping `custom_payload` MUST follow the `Ping Custom Payload Extensions` format.

## Custom Payload Extensions Format

- **type**: what payload type is it
- **payload**: a ssz ByteList of max length 1100 which contents are specified the type field


```python
CustomPayloadExtensionsFormat = Container(
  type: u16,
  payload: ByteList[max_length=1100]
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

error_payload = SSZ.serialize(Container(error_code: u16, message: ByteList[MAX_ERROR_BYTE_LENGTH]))

ErrorPayload = Container(
  type: 65535,
  payload: error_payload
)
```

### Error Code's

#### 0: Extension not supported
This code should be returned if the extension isn't supported. This error should only be returned if 
- The extension isn't supported
- The extension isn't a required extension for specified Portal Network.

#### 1: Requested data not found
This error code is for if an extension is asking for something and it doesn't exist.

#### 2: Failed to decode payload
Wasn't able to decode the payload

#### 3: System error
A critical error happened and the ping can't be processed