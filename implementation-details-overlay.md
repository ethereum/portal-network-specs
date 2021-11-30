# Portal Network: Overlay Network Functionality

This document outlines the units of functionality that are necessary for an implementation of the [portal wire protocol](./portal-wire-protocol.md)

> Note that in some places the exact functionality may not be strictly necessary and may be influenced by the implementation details of individual clients. There are alternative ways to implement the protocol and this is merely intended to serve as a guide.

# A - Base Protocol

Support for the base Discovery v5 protocol functionality

## A.1 - Base Protocol TALKREQ and TALKRESP

Base protocol support for the TALKREQ and TALKRESP messages

## A.2 - TALKREQ/TALKRESP message routing

The ability to route incoming TALKREQ/TALKRESP messages to custom handlers.

## A.3 - TALKREQ/TALKRESP request and response handling

The ability to send a TALKREQ with a specific `request_id` and receive the corresponding TALKRESP message.

# B - Portal Wire Protocol Messages

Support for the message types that are part of the [portal wire protocol](./portal-wire-protocol)

## B.1 - PING & PONG

Support for the PING and PONG message types

### B.1.a - PING message support

Support for the PING message type

#### B.1.a.1 - PING sending

The ability to send a PING message

#### B.1.a.2 - PING receiving

The ability to receive PING messages

### B.1.b - PONG message support

Support for the PONG message type

#### B.1.b.1 - PONG sending

The ability to send a PONG message

#### B.1.b.2 - PONG receiving

The ability to receive PONG messages

### B.1.c - PONG when PING'd

When a PING message is received a PONG response is sent.

## B.2 - FINDNODES & FOUNDNODES

Support for the FINDNODES and FOUNDNODES message types

### B.2.a - FINDNODES message support

Support for the FINDNODES message type

#### B.2.a.1 - FINDNODES sending

The ability to send a FINDNODES message

#### B.2.a.2 - FINDNODES receiving

The ability to receive FINDNODES messages

### B.2.b - FOUNDNODES message support

Support for the FOUNDNODES message type

#### B.2.b.1 - FOUNDNODES sending

The ability to send a FOUNDNODES message

#### B.2.b.2 - FOUNDNODES receiving

The ability to receive FOUNDNODES messages

### B.2.c - Serving FINDNODES

When a FINDNODES message is received the appropriate `node_id` records are pulled from the sub protocol [routing table](#TODO) and a FOUNDNODES response is sent with the ENR records.

## B.3 - FINDCONTENT & FOUNDCONTENT

Support for the FINDCONTENT and FOUNDCONTENT message types

### B.3.a - FINDCONTENT message support

Support for the FINDCONTENT message type

#### B.3.a.1 - FINDCONTENT sending

The ability to send a FINDCONTENT message

#### B.3.a.2 - FINDCONTENT receiving

The ability to receive FINDCONTENT messages

### B.3.b - FOUNDCONTENT message support

Support for the FOUNDCONTENT message type

#### B.3.b.1 - FOUNDCONTENT sending

The ability to send a FOUNDCONTENT message

#### B.3.b.2 - FOUNDCONTENT receiving

The ability to receive FOUNDCONTENT messages

## B.4 - OFFER & ACCEPT

Support for the OFFER and ACCEPT messages

### B.4.a - OFFER message support

Support for the OFFER message type

#### B.4.a.1 - OFFER sending

The ability to send a OFFER message

#### B.4.a.2 - OFFER receiving

The ability to receive OFFER messages

### B.4.b - ACCEPT message support

Support for the ACCEPT message type

#### B.4.b.1 - ACCEPT sending

The ability to send a ACCEPT message

#### B.4.b.2 - ACCEPT receiving

The ability to receive ACCEPT messages

# C - ENR Database

Management of known ENR records

## C.1 - ENR handling

Support for encoding, decoding, and validating ENR records according to [EIPTODO](#TODO)

### C.1.a - Extraction of IP address and port

IP address and port information can be extracted from ENR records.

## C.2 - Store ENR record

ENR records can be saved for later retrieval.

### C.2.a - Tracking highest sequence number

Storage of ENR records respects or tracks sequence numbers, preserving and tracking the record with the highest sequence number.

## C.3 - Retrieve ENR Record

ENR records can be retrieved by their `node_id`.

# D - Overlay Routing Table

Management of routing tables

## D.1 - Sub Protocol Routing Tables

Separate routing tables for each supported sub protocol.

## D.2 - Distance Function

The routing table is able to use the custom distance function.

## D.3 - Manage K-Buckets

The routing table manages the K-buckets

### D.3.a - Insertion of new nodes

Nodes can be inserted into the routing table into the appropriate bucket, ensuring that buckets do not end up containing duplicate records.

### D.3.b - Removal of nodes

Nodes can be removed from the routing table.

### D.3.c - Maximum of K nodes per bucket

Each bucket is limited to `K` total members

### D.3.d - Replacement cache

Each bucket maintains a set of additional nodes known to be at the appropriate distance.  When a node is removed from the routing table it is replaced by a node from the replacement cache when one is available. The cache is managed such that it remains disjoint from the nodes in the corresponding bucket.

## D.4 - Retrieve nodes at specified log-distance

The routing table can return nodes at a requested log-distance

## D.5 - Retrieval of nodes ordered by distance to a specified `node_id`

The routing table can return the nodes closest to a provided `node_id`.

# E - Overlay Network Management

Functionality related to managing a node's view of the overlay network.

## E.1 - Bootstrapping via Bootnodes

The client uses a set of bootnodes to acquire an initial view of the network.

### E.1.a - Bootnodes

Each supported sub protocol can have its own set of bootnodes.  These records can be either hard coded into the client or provided via client configuration.

## E.2 - Population of routing table

The client actively seeks to populate its routing table by performing [RFN](#TODO) lookups to discover new nodes for the routing table

## E.3 - Liveliness checks

The client tracks *liveliness* of nodes in its routing table and periodically checks the liveliness of the node in its routing table which was least recently checked.

### E.3.a - Rate Limiting Liviliness Checks

The liveliness checks for any individual node are rate limited as to not spam individual nodes with lots of PING messages when the routing table is sparse.

# F - Content Database

Management of stored content.

## F.1 - Content can be stored

Content can be stored in a persistent database.  Databases are segmented by sub protocol.

## F.2 - Content can be retrieved by `content_id`

Given a known `content_id` the corresponding content payload can be retrieved.

## F.3 - Content can be removed

Content can be removed.


## F.4 - Query furthest by distance

Retrieval of the content from the database which is furthest from a provided `node_id` using the custom distance function.


## F.5 - Total size of stored content

Retrieval of the total number of bytes stored.

# G - Content Management

## G.1 - Support for the uTP Sub Protocol

Support for sending and receiving streams of data using the uTP sub protocol.

### G.1.a - Support for outbound streams

The ability to establish a new outbound connection with another node with a specified `connection-id`

### G.1.a - Support for inbound streams

The ability to listening for an inbound connection from another node with a `connection-id` that is known in advance.

## G.2 - Enforcement of maximum stored content size

When the total size of stored content exceeds the configured maximum content storage size the content which is furthest from the local `node_id` is evicted in a timely manner.  This should also result in any "data radius" values relevant to this network being adjusted.

## G.3 - Retrieval via FINDCONTENT/FOUNDCONTENT & uTP

Support for retrieving content using the FINDCONTENT, FOUNDCONTENT, and uTP sub protocol.

### G.3.a - DHT Traversal

The client can use the FINDCONTENT and FOUNDCONTENT messages to traverse the DHT until they encounter a node that has the desired content.

### G.3.b - Receipt via direct payload

Upon encountering a FOUNDCONTENT response that contains the actual content payload, the client can return the payload.

### G.3.c - Receipt via uTP

Upon encountering a FOUNDCONTENT response that contains a uTP `connection-id`, the client should initiate a uTP stream with the provided `connection-id` and receive the full data payload over that stream.

## G.4 - Gossip via OFFER/ACCEPT & uTP

Support for receipt of content using the GOSSIP/ACCEPT messages and uTP sub protocol.

### G.4.a - Handle incoming gossip

Client can listen for incoming OFFER messages, responding with an ACCEPT message for any offered content which is of interest to the client.  

#### G.4.a.1 - Receipt via uTP

After sending an ACCEPT response to an OFFER request the client listens for an inbound uTP stream with the `connection-id` that was sent with the ACCEPT response.

### G.4.b - Neighborhood Gossip Propogation

Upon receiving and validating gossip content, the content should then be gossiped to some set of interested nearby peers.

#### G.4.b.1 - Sending content via uTP

Upon receiving an ACCEPT message in response to our own OFFER message the client can initiate a uTP stream with the other node and can send the content payload across the stream.


## G.5 - Serving Content

The client should listen for FINDCONTENT messages.

When a FINDCONTENT message is received either the requested content or the nodes known to be closest to the content are returned via a FOUNDCONTENT message.


# H - JSON-RPC

Endpoints that require for the portal network wire protocol.

## H.1 - `TODO`

TODO
