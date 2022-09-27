<!-- 

This template is meant to provide a common structure for the individual sub
protocol specifications.  Removal of these comments is recommended.

-->

# Title

<!-- This section contains a concise description of what this network does. -->

## Overview

<!-- 

This section should remain concise and high level, but provide descriptions of the functionality provided by the network, what data types it works with, and the overall shape and structure of the network.

### Data

#### Types

<!-- This sections contains high level descriptions of each data type -->


#### Retrieval

<!-- 

For networks that support content retrieval, this section should contain a high
level description of what content can be fetched and how it is identified such
as "Retrieval of block headers by their hash" 

-->

## Specification

<!-- This section is where the actual technical specification is written -->

### Distance Function

<!-- The network specific definition of the distance function should be placed here -->

### Content ID Derivation Function

<!-- The network specific definition of the Content ID derivation function should be placed here -->

### Wire Protocol

#### Protocol Identifier

<!-- The protocol identifier used by this network -->

#### Supported Message Types

<!-- The list of message types from the portal wire protocol that are supported by this network -->

#### `Ping.custom_data` & `Pong.custom_data`

<!-- If the PING/PONG messages are used by this protocol they should be specified here -->

### Routing Table 

<!-- This section should contain any network specific information about the routing table. -->

### Node State

<!-- If the protocol includes additional node state information it should be specified here. -->

### Data Types

<!--

This section should contain individual sections defining each type of content
supported by this network.  Each content type defined should have a definition
which includes how the content is encoded and the encoding for the
corresponding Content Key

-->

### Algorithms

<!-- This section should contain definitions of any protocol specific algorithms -->
