# Ping Custom Payload Extensions

## Motivation

Ping Payload Extensions. There is a minimal set of `standard extensions` which require a breaking change to update. This framework allows Portal clients to implement `non standard extensions` which don't require a breaking change to deploy to the network. A more flexible way to extend the Protocol without bloating the [Portal-Wire-Protocol](../portal-wire-protocol.md)

# Type's

There are 65536 unique type ids.

Types 0-10_000 and 65436-65535 are reserved for for future upgrades.

The rest are first come first serve, but they should still be defined in this repo to avoid overlaps.


## Requirements

All payloads used in the Ping `custom_payload` MUST follow the `Ping Custom Payload Extensions` format.

## Custom Payload Extensions Format

- **type**: numeric identifier which tells clients how the `payload` field should be decoded.
- **payload**: the SSZ encoded extension payload


```python
CustomPayloadExtensionsFormat = Container(
  type: u16,
  payload: ByteList[max_length=1100]
)
```

## Ping vs Pong
The relationship between Ping and Pong message will be determined by the requirements of the type.

Currently type 1,2,3 are symmetrical, having the same payload for both request and response.  This symmetry is not required.  Extensions may define separate payloads for Ping and Pong within the same type.


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
This error code should be used when a client is unable to provide the necessary data for the response.

#### 2: Failed to decode payload
Wasn't able to decode the payload

#### 3: System error
A critical error happened and the ping can't be processed

## Standard extensions

Every Portal Network Client is required to support 3 extensions
- [Type 0: Capabilities Payload](extensions/type-0.md): useful for finding what ping extensions a client supports
- Sub-network standard extension. For history this is currently [Type 2: History Radius Payload](extensions/type-2.md). For State and Beacon the base extension is [Type 1: Basic Radius Payload](extensions/type-1.md). These are extensions what are crucial. This standard extensions are specified the respective sub-networks specification  
- Type 3: [Get Client info Payload](extensions/type-3.md)

## What is the [Type 0: Capabilities Payload](extensions/type-0.md) for
It is for Portal implementations which want to see what extensions a peer supports. Not all extensions need to be implemented by all parties. So in order for a peer to find if an extension is implemented a [Type 0: Capabilities Payload](extensions/type-0.md) should be exchanged.

Non-required extension offer a way for Portal implementations to offer extended functionality to its users without requiring every Portal implementing party to agree to a new feature. This allows for a diverse set of use cases to be fulfilled without requiring every implementer implement every extension, or requiring the need to bloat the minimal [Portal-Wire-Protocol](../portal-wire-protocol.md) with new `Message Types`.

## How do sub-network standard extension's work
sub-network standard extension's are fundamental extensions that are required for a Portal sub-network to function. They must be supported by the sub-networks implementations.
