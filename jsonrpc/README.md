# Portal Network JSON-RPC Specification

[View the spec][playground]

The Portal Network JSON-RPC is a collection of methods that all clients implement.
This interface allows downstream tooling and infrastructure to treat different
Portal Network clients as modules that can be swapped at will.

## Building

The specification is split into multiple files to improve readability. It
can be compiled the into a single document by running:

```console
$ npm install
$ npm run build
Build successful.
```

This will output the file `openrpc.json` in the root of the project. This file
will have all schema `#ref`s resolved.

## Contributing

The specification is written in [OpenRPC][openrpc]. Refer to the
OpenRPC specification and the JSON schema specification to get started.

### Testing

There are currently two tools for testing contributions. The first tool is
an [OpenRPC validator][validator].

```console
$ npm install
$ npm run lint
OpenRPC spec validated successfully.
```

The second tool can validate a live JSON-RPC provider hosted at
`http://localhost:8545` against the specification:

```console
$ ./scripts/debug.sh discv5_sendPing \"enr:-....\"
data.json valid
```

[playground]: https://playground.open-rpc.org/?schemaUrl=https://raw.githubusercontent.com/ethereum/portal-network-specs/assembled-spec/jsonrpc/openrpc.json&uiSchema%5BappBar%5D%5Bui:splitView%5D=false&uiSchema%5BappBar%5D%5Bui:input%5D=false&uiSchema%5BappBar%5D%5Bui:examplesDropdown%5D=false
[openrpc]: https://open-rpc.org
[validator]: https://open-rpc.github.io/schema-utils-js/globals.html#validateopenrpcdocument
