# Ping Custom Payload Extensions

## Motivation

Ping Payload Extensions. Messages on Portal are primarily made of ping/pong responses. This framework allows Portal clients to implement `non standard extensions` which don't require a breaking change to deploy to the network. A more flexible way to extend the Protocol without bloating the core specification [Portal-Wire-Protocol](../portal-wire-protocol.md) or requiring every client to agree to add a feature a subset of clients want.

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

Currently type 0, 1, and 2 are symmetrical, having the same payload for both request and response. This symmetry is not required. Extensions may define separate payloads for Ping and Pong within the same type.


### Error responses
If the ping receiver can't handle the ping for any reason the pong should return an error payload

[Type 65535: The definition of error responses can be found here](extensions/type-65535.md)

## Standard extensions

A standard extension is an extension which all nodes on the network MUST support. Nodes can send these without requiring a `Type 0: Client Info, Radius, and Capabilities Payload` request to discover what extensions the client supports. 

Changing standard extensions is considered a breaking change.

List of some standard extensions
- [Type 0: Client Info, Radius, and Capabilities Payload](extensions/type-0.md): useful for finding Client Info, Radius, and ping extensions a client supports
- [Type 65535: Error Payload](extensions/type-65535.md): this payload can only be used as a response to a ping

# Non standard extensions
Non standard extensions are extensions in which you can't assume all other clients support, to use a non standard extension it is required that Portal clients first send a [Type 0: Client Info, Radius, and Capabilities Payload](extensions/type-0.md) packet, then upgrade to use their desired non standard extensions.

## What is the [Type 0: Client Info, Radius, and Capabilities Payload](extensions/type-0.md) for
It is for Portal implementations which want to see what extensions a peer supports. Not all extensions need to be implemented by all parties. So in order for a peer to find if an extension is implemented a [Type 0: Client Info, Radius, and Capabilities Payload](extensions/type-0.md) should be exchanged.

Non-required extension's offer a way for Portal implementations to offer extended functionality to its users without requiring every Portal implementing party to agree to a new feature. This allows for a diverse set of use cases to be fulfilled without requiring every implementer implement every extension, or requiring the need to bloat the minimal [Portal-Wire-Protocol](../portal-wire-protocol.md) with new `Message Types`.

## How do sub-network standard extension's work
sub-network standard extension's are fundamental extensions that are required for a Portal sub-network to function. They must be supported by the sub-networks implementations. Changing a standard extension requires a breaking change. 
