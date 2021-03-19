# uTP SubProtocol for Discovery V5

## Abstract

This document specifies an implementation of the [uTP](https://www.bittorrent.org/beps/bep_0029.html) streaming protocol which uses [Discovery v5](https://github.com/ethereum/devp2p/blob/6eddaf50298d551a83bcc242e7ce7024c6cc8590/discv5/discv5.md) as a transport instead of raw UDP packets.

## Motivation

The Discovery v5 protocol provides a simple and extensible UDP based protocol with robust encryption and resistance to deep packet inspection.  The use of UDP however imposes a tight limit on packet sizes.  SubProtocols which wish to implement functionality that requires transmission of data that exceeds this packet size are forced to implement their own solutions for splitting these payloads across multiple UDP packets.  Packet loss makes this type of solution fragile.  A generic solution that can be reused across different discovery v5 sub-protocol will improve the overall security and robustness of subprotocols.

### Example Usage

Suppose we have a sub-protocol with the following messages

- `GetData` (request)
- `Data` (response)

In this protocol, a request is sent by Alice using the `GetData` message,
containing some identifier.  The size data to be transmitted exceeds the UDP
packet size, so the `Data` response sent by Bob will contain a randomly
generated `connection_id` instead.

Bob will then initiate a new uTP connection with Alice using this connection ID.

Alice, upon receiving the `Data` message containing the `connection_id` will
*listen* for a new incoming connection from Bob over the `utp` sub-protocol.
When this new connection is opened, she can then read the bytes from the stream
until the connection closes.

## BEP29

https://www.bittorrent.org/beps/bep_0029.html

The uTP protocol as specified in BEP29 defines the packet structure and logic for handling packets.

The only change we make to BEP29 is that rather than using the full UDP packet for uTP packets, we instead use the TALKREQ `payload` for the uTP packet.

## Specification

The Discovery v5 uTP protocol uses the byte string `utp` (`0x757470` in hex)

All packets are sent using the TALKREQ message.

This protocol does not use the TALKRESP message.

The `payload` portion of the TALKREQ message is the same as the packet format specified in BEP29
