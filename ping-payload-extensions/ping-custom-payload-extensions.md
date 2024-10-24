# Ping Custom Payload Extensions

## The problem

Over time we will need to change what is sent over ping/pong `custom_payload`'s to adjust for what is needed in the future.
Currently the only way to update a `custom_payload` is through breaking changes which break protocol compatible between Portal implementations.
As we get users, deploying breaking changes to mainnet will no longer be an option as we are aiming for a 100% uptime.

## The Solution

Ping Payload Extensions. There is a minimal set of `standard extensions` which require a fork hard fork to change. This framework allows Portal clients to implement `non standard extensions` which don't require a hard fork to deploy to the network. A more flexible way to extend the Protocol without bloating the [Portal-Wire-Protocol](../portal-wire-protocol.md)

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
The relationship between Ping and Pong message will be determined by the requirements of the type.

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

## Standard extensions

Every Portal Network Client is required to support 3 extensions
- [Type 0: Capabilities Payload](extensions/type-0.md): useful for finding what ping extensions a client supports
- Sub-network standard extension. For history this is currently [Type 2: History Radius Payload](extensions/type-2.md). For State and Beacon the base extension is [Type 1: Basic Radius Payload](extensions/type-1.md). These are extensions what are crucial. This standard extensions are specified the respective sub-networks specification  
- Type 3: [Get Client info Payload](extensions/type-3.md)

## What is the [Type 0: Capabilities Payload](extensions/type-0.md) for
It is for Portal implementations which want to see what extensions a peer supports. Not all extensions need to be implemented by all parties. So in order for a peer to find if an extension is implemented a [Type 0: Capabilities Payload](extensions/type-0.md) should be exchanged.

Non-required extension offer a way for Portal implementations to offer extended functionality to its users without requiring every Portal implementing party to agree to a new feature. This allows for a diverse set of use cases to be fulfilled without requiring every implementer implement every extension, or requiring the need to bloat the minimal [Portal-Wire-Protocol](../portal-wire-protocol.md) with new `Message Types`.

## Does implementing non-standard-extensions require a hardfork?
No only changing a sub-networks standard extension requires a hard fork.


## How do sub-network standard extension's work
sub-network standard extension's are fundamental extensions that are required for a Portal sub-network to function. They must be supported by the sub-networks implementations.

### What is the process for changing a sub-network standard extension

The process of changing a Portal sub-networks standard extension is through a hard fork set by a timestamp. When the timestamp is reached usage of the old standard extension is replaced by the new standard extension. Details on what standard extensions for what networks are being replace are specified in the fork's document.

### Can a node use the next standard extension for a network before the hardfork
Yes there is no limitation for a Portal Client implementation using the next standard extension or a 3rd party extension before the hard fork has taken place. A requirement of this flexibility is that the new extension being used in-place of the standard extension must still fulfill the duties of the current standard extension. One downside of using new Standard Extension's before the fork is you won't know if a peer supported it yet unless you did either a
- trial and error to see if the peer supports the call
- Sent a [Type 0: Capabilities Payload](extensions/type-0.md)

This can be useful for 
- accessing functionality before the hard fork has taken place in a none breaking way
- Extending the protocol with implementation specific heuristics.

It is only recommended to do this for peers in an implementations routing table as most connections are too short lived to make the addition call worth it.
