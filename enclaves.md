# Portal Enclaves

## Abstract

### Problem Statement

In the traditional DevP2P based `ETH` protocol, the security of the protocol is anchored in each node of the network exposing 100% of the necessary API for the network to operate.  As a participant of the network, you can connect to any random node in order to get whatever data you might need.  This property makes the network difficult to attack, requiring an attacker to either "eclipse" a node in order to only expose them to malicious nodes, or to operate a super-majority of the nodes in the network such that you probabalistically will only interact with malicious nodes.  One can view this as requiring an attacker to cover a very large surface area in order to perform an effective attack, with the surface area here being roughly the full size of the DevP2P `ETH` protocol.

In a DHT context, these attacks become much simpler to execute because the surface area is much smaller.  An attacker can pick a specific section of the network, and overpopulate that area of the network with their own malicious nodes.  The amount of computational resources needed to execute this attack is much lower than in the DevP2P context, and thus, the attack is easier to execute.

We are then looking for a solution for DHT based networks that:

- Preserves the *nice* property of DHTs of having an address space and topology which allows for zero-coordination distributed storage and retrieval of data.
- Provides protection against attacks on specific regions of the address space.
  - Eclipse attacks where an attacker controls a super majority of the nodes in a specific region of the address space.
  - DOS attacks where an attacker can effectively DOS a region of the address space.

### Introducing "Enclaves"

We present the idea of a DHT "enclave".  An Enclave is a collection of nodes in the DHT which operate as a single unit, storing and serving data from the full DHT address space.  From the external perspective, an Enclave can be interacted with in the same manner as a Full Node.  From the internal perspective, an Enclave is a collection of DHT nodes that act cooperatively to cover and serve data from the full DHT address space.

We propose that the Enclave system be built as an additive layer to the existing portal protocols, with the low level protocols having no awareness of the enclave system.  The Enclave network would effectively emulate the current way that the DevP2P ETH protocol is structured, allowing each enclave to interact with each other in much the same way that full nodes interact over DevP2P.

> Question: This seems to provide a similar level of security as the current DevP2P protocol would provide, effectively shifting the security problems down into the enclave system itself, needing to ensure that enclaves can protect themselves and have effective mitigation against infiltration by malicious nodes.

## Overview

TODO
