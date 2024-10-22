# This document lists defined extensions
Some extensions are network specific some are generic

This is a list and short description of all the extensions


| Type number  |  Name | Supported sub-networks  | Short Description  | Is this call Required to Implement  |
|---|---|---|---|---|
| [1](extensions/type-1.md)  |  Basic Radius Payload | State, Beacon, Canonical Transaction Index, Transaction Gossip  | Provides the nodes Radius  |  Yes  |
| [2](extensions/type-2.md)  | History Radius Payload  |  History | Provides the nodes radius and ephemeral header count  |  Yes  |
| [3](extensions/type-3.md)  |  Client Info | All  | It will return you something like `trin/0.1.1-2b00d730/linux-x86_64/rustc1.81.0`  |  Yes  |
