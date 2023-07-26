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

### Design Principles

The ideal design here seems to be to firmly specify the core API for enclaves for these things:

- How they are discovered
- How they are interacted with for retrieval of data

Then we likely want to keep the specificatiion flexible enough that we can support a range of enclave types:

- Public enclaves that any "random" node could join
- Staked enclaves where joining requires nodes to have something "at stake"
- Private enclaves that implement their own structure.

The goal here would be to keep enough freedom for there to be a diverse set of enclaves, while still providing a clear and "secure enough" structure for Public enclaves.

### Enclave Mechanics and Ideas

> Everything here is "first draft" and needs to be picked apart and reviewed.  Take this as an attempt to provide a rough description that is expected to have flaws that need to be addressed.

#### Gateways

A "Gateway" is how enclaves communicate externally.  An enclave can have a single gateway, or many gateways.  A gateway is a node that receives external requests for data, proxies those requests internally to the appropriate nodes within the enclave and serves the returned data to the original external requester.


#### Public Enclave Operation

The naive starting point for establishing public enclaves is to have individual nodes opt-in to being the coordinator for an enclave and act as the "gateway" node for that enclave.  They would then need a mechanism to solicit new nodes to join their enclave, likely listing areas of the address space where coverage is needed.  There would also likely need to be mechaniccs for "auditing" a new enclave member for whether they are able to adequately respond to requests for data, as well as a way to evict enclave members who are not performing their duties adequately.

#### Full Coverage of DHT Address Space

For "Public" enclaves, the internal structure would be made up of many individual nodes.  These nodes would likely be somewhat evenly spaced throughout the DHT such that they provide full coverage of the full DHT address space.  An enclave would likely want to work towards redundancy in this reguard ensuring that they have multiple nodes covering every portion of the address space to account for attrition and under-performing nodes.

#### Internal Communication

Ideally, one benefit of being in an enclave would be that you should be able to request data from other nodes in the enclave and receive responses faster than you might in the public network.  In this manner, an enclave could operate in much the same way as the overall DHT does, with nodes maintaining a kind of "routing table" that is populated with the other nodes of the enclave and being able to traverse the enclave nodes to find the ones that have the necessary data.

#### Security Things

It will be important for public enclaves to be able to do the following.

- Induction verification of new nodes joining the enclave to ensure they are able to perform their duties (serving data from a portion of the DHT)
- Ongoing auditing of enclave nodes to detect underperforming or malicious nodes (TODO: modes of maliciousness should be defined here)
- Quality-Of-Service control to limit requests/response in times of high load.
- Internal QOS control to prevent individual nodes over-using the resources of the enclave.

## Securing Public Enclaves

In order for this system to work well, public enclaves need to be viable which means that they will need to be able to have some level of mitigation for the following issues:

- Leaching: Enclave node that is "leaching" too much data.
- Censorship: Enclave node that is selectively responding to queries for data (censorship)
- <what else?>

> My intuition is that we *can* secure enclaves in a way that we cannot secure the whole DHT simply because enclaves would be smaller, and their full membership known.  These small changes seem to allow a class of security improvemments that are otherwise not feasible in the full DHT.

### Leaching

All nodes in the enclave should be able to be heald accountable for their internode communication.  This can be done by having nodes sign some kind of accumulated running total/tally of the total message bytes passed between them and regular reporting of this data to the "Gateway" node or whatever node is acting as coordinator for the enclave.  This shouold allow for enclaves to evict, throttle, or otherwise deal with nodes that are consuming a disporportionate amount of enclave resources.

## Censorship

In the event that a node in the network fails to respond to a query for a piece of data, there are two possibilities

- They don't have the data
- They are censoring the data

Censorship should be detectable by first providing the node in question with known data via gossip and then requesting the data from that node.  This operation could be performed opaquely by multiple nodes, one performing the gossip, and another performing the request to prevent a situation where the node in question is able to correctly guess that they are being audited.  There are many way this scheme could be subtly augmented to increase the guarantees or confidence it provides.
