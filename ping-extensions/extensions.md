# This document lists defined extensions
This is a list and short description of all the extensions

- Extensions can be supported by all sub-networks or a subsection


| Type number | Name | Supported sub-networks | Short Description | Is standard extension |
|---|---|---|---|---|
| [0](extensions/type-0.md) | Client Info, Radius, and Capabilities | All | Returns client info e.x. `trin/0.1.1-2b00d730/linux-x86_64/rustc1.81.0`, the nodes radius and a list of enabled extensions | Yes |
| [1](extensions/type-1.md) | Basic Radius Payload | History, State, Beacon | Provides the nodes Radius | No |
| [2](extensions/type-2.md) | History Radius Payload | Legacy History | Provides the nodes radius and ephemeral header count | No |
| [65535](extensions/type-65535.md) | Error Response | All | Returns an error for respective ping message | Yes |
