# uTP SubProtocol over Discovery v5

## Abstract

This document specifies an implementation of the [uTP](https://www.bittorrent.org/beps/bep_0029.html) streaming protocol which uses [Node Discovery Protocol v5](https://github.com/ethereum/devp2p/blob/6eddaf50298d551a83bcc242e7ce7024c6cc8590/discv5/discv5.md) as a transport instead of raw UDP packets.

## Motivation

The Discovery v5 protocol provides a simple and extensible UDP based protocol with robust encryption and resistance to deep packet inspection.  The use of UDP however imposes a tight limit on packet sizes. [Sub-protocols](https://github.com/ethereum/devp2p/blob/master/discv5/discv5-wire.md#talkreq-request-0x05) which wish to implement functionality that requires transmission of data that exceeds this packet size are forced to implement their own solutions for splitting these payloads across multiple UDP packets.  Packet loss makes this type of solution fragile.  A generic solution that can be reused across different Discovery v5 sub-protocols will improve the overall security and robustness of sub-protocols.

## Basic Goals
**1.1 Offer a reliable data transfer mechanism for serving data**

**1.2 Have a consistent RDT mechanism across all discv5 sub-protocols**

**1.3 Be built on top of discv5 so that we can afford the benefits of discv5 (e.g. encryption), while making it more simple and interoperable.**

## Rationale
The Portal Network's current design consists of three subnetwork protocols (state, history, gossip) that lay on top of discv5, using discv5's TALKREQ message as an encapsulation over any subnetwork messages. Discv5 in turn uses UDP as a transport, which is unreliable. This is fine for message pairs such as `Ping/Pong` and `FindNodes/Nodes` , since it only means the routing table will not be updated.

However, for other message pairs such as `FindContent/Content` and `Offer/Accept`, a reliable data transfer mechanism is desirable, since these messages involve sending a stream of data over the network, and the complete transfer of requested content is necessary for a robust network.

Additionally, it is likely that the data sent will take up more than 1 UDP packet, and thus must be broken up into a stream of UDP packets. If each sub-network has to implement their own solution for splitting up packets, this leads to loss of interoperability among other things like having to redefine a solution for each subprotocol.

These two problems—a lack of reliable data transfer and the absence of a generic solution for splitting up data—can be solved by introducing a **protocol offering reliable data transfer** that will be used by all sub-networks when sending data.

A simple solution is just using TCP. However, since we are building on top of discv5, we cannot do this, as we would have two transport protocols. This leads to many complications, for example, TCP would expect to deliver it's payload to the specified port, but the sub-networks are not applications listening on separate ports.

However, we could use TCP to stream data separately from discv5, ie, avoiding the discv5/UDP stack entirely. When `FindContent` is sent, it contains a TCP port, and then the receiver opens a TCP connection on that port and sends a stream of data to the requester, who is listening on that port. A downside is the TCP overhead. The main downside is that it's not implemented over discv5...but why is it necessary for every message to go through discv5 in the first place? From the spec, discv5 "offers encryption and resistance to deep packet inspection". By operating separate from discv5, we lose these capabilities. Furthermore, all packets currently go through discv5, and we lose some consistency if we go this route.

With this consideration in mind, we now seek an extensible protocol built on discv5 that offers RDT. Thus, uTP was chosen as the solution because it is an already established protocol that creates a stream over UDP packets. uTP is a UDP-extensible protocol that adds reliable data transfer. It also offers a congestion control mechanism that yields to TCP traffic. However, the main motivation behind choosing uTP is that it is a pragmatic solution that offers reliable data transfer, and can easily be stitched on top of discv5.

This solves our problem. We get reliable data transfer over discv5. The only modification we need to make is to have uTP use discv5 as a transport, instead of raw UDP, which is what the original uTP spec uses. This is a relatively simple modification.

### Example Usage

Suppose we have a sub-protocol with the following messages:

- `GetData` (request)
- `Data` (response)

In this protocol, a request is sent by Alice using the `GetData` message,
containing some identifier.  The size of the data to be transmitted exceeds the
UDP packet size, so the `Data` response sent by Bob will contain a randomly
generated `connection_id` instead.

Alice will then initiate a new uTP connection with Bob using this `connection_id`.

Bob, upon sending the `Data` message containing the `connection_id` will
*listen* for a new incoming connection from Alice over the `utp` sub-protocol.
When this new connection is opened, Alice can then read the bytes from the stream
until the connection closes.

## BEP29

https://www.bittorrent.org/beps/bep_0029.html

The uTP protocol as specified in BEP29 defines the packet structure and logic for handling packets.

The only change we make to BEP29 is that rather than using the full UDP packet for uTP packets, we instead use the TALKREQ `payload` for the uTP packet.

## Specification

The Discovery v5 uTP protocol uses the byte string `utp` (`0x757470` in hex) as value for the protocol byte string in the `TALKREQ` message.

All packets are sent using the `TALKREQ` message.

This protocol does not use the `TALKRESP` message.

> Note: `TALKREQ` is part of a request-response mechanism and might cause Discovery v5 implementations
to invalidate peers when not receiving a `TALKRESP` response. This is an unresolved item in the specification.

The payload passed to the `request` field of the `TALKREQ` message is the uTP packet as specified in BEP29.
