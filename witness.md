# Block Witness Formal Specification

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD", "SHOULD NOT", "RECOMMENDED",  "MAY", and "OPTIONAL" in this document are to be interpreted as described in [RFC 2119](https://tools.ietf.org/html/rfc2119).

## Goals Of This Document

1. Describe the witness format fully. Helps to implement witnesses support in multiple clients, no matter which programming language is used;

2. Highlighting changes in the witness format. Makes it clear how changes to the witness format affect generation and parsing rules.

3. Provide the single place to discuss the format and its future improvements.

4. Formal analysis. Helps claim, prove and review correctness of the format, as well as, analyse the performance of generation and parsing using complexity theoretic metrics.

5. Reference Tests. Helps to construct a minimal set of test witnesses, which can be encoded and decoded using the witness format. These test witness serve as reference tests for witness format generators and parsers that are included inside a client.


This document motivates the use of witnesses, provides some use cases, and specifies the witness format.

## Motivation

The witness format was picked to satisfy the following criteria.

**1. Witness Streaming without intermediate dynamic buffers**
It should be possible to stream-as-you-encode the trie on one node
and recreate it at the same time by using a fixed allocated buffer. That helps
efficiently transfer and encode/decode witnesses.

The witness allows to walk through the trie and produce the witness as you go without buffering;
sending it straight to a network socket. A peer can then receive it from the socket
and it can start computing the hash of the state root straight away.

Also, it means that the memory consumption of witness processing itself will be
fixed and predictable, which helps for nodes with limited memory.


**2. Building Forests**
It should be possible to build a forest of tries from a single witness. It is
needed for two use-cases: 

- partial witnesses (like the ones that are used in
semi-stateless initial sync, when you already have some trie that you need to
extend with more data);

- splitting the witness into verifiable chunks (when we can build a trie piece
    by piece and verify root hashes). That is possible by first constructing
    a witness for the top of the trie (to verify the root hash) and then for
    subtries from the top level to the bottom. At all times you will be able to
    verify a subtrie root hash.

**3. Arbitrary chunk sizes**
The witness format doesn't limit a chunk size. That makes it easy to experiment with and find
the best size for efficient relaying properties.


## Use Cases

The format described in this document can be used to store and build
partial hexary Patricia Merkle Tries and forests in a linear way.

It can be used to store full or sparse tries as well.
It is also suitable to store subtries that can be used for semi-stateless
initial sync and other semi-stateless operations.


## Syntax, Semantics, and Validation

The binary format of an Ethereum block witness is a byte array whose structure is defined in this section. The witness encoding is defined using [context-free](https://en.wikipedia.org/wiki/Context-free_grammar) syntax rules. We equip each syntax rule with semantics, which gives us a [syntax-directed translation](https://en.wikipedia.org/wiki/Syntax-directed_translation) from the binary format to to a client's internal representation of a block witness. With each syntax rule, we may also give additional restrictions, which we refer to as "validation rules".


### Notation

First define the notation which will be used to define the syntax, semantics, and validation rules.

 - We use Backus-Naur form notation, namely symbols like `|`, `:=`, `>`, and `<` are used to define production rules.
 - Because this is a binary format, the only terminal symbols are bytes, which we write in hexadecimal notation `0x00`, `0x01`, ..., and `0xff`.
 - Parentheses `(` and `)` enclose a tuple. 
 - Brackets `[` and `]` are used to index an element of a tuple, for example the `i`th element of tuple `T` is denoted `T[i]`. Brackets following a variable named `bitmask` means that the index is of a bit, e.g. `bitmask[0]` represents the leftmost bit.
 - Ellipses `...` are notation for "and so on until", used to avoid writing a long enumerated tuple. For example, `A[1] A[2] ... A[5]` is short-hand notation for `A[1] A[2] A[3] A[4] A[5]`.
 - `A^n` represents symbol `A` repeated `n` times. We allow `n` to be `0`, representing zero occurances of `A`. Also, if there is a logical expression in place of `n`, then a false expression is replaced by `0` and a true expression is replaced with `1`.
 - `A^+` represents symbol `A` repeated one or more times.
 - `A^*` represents symbol `A` repeated zero or more times.
 - Curly braces `{` and `}` enclose semantics after each syntax rule.
 - Semantics are just an English explanation of what is produced by that syntax rule.
 - After each semantics rule, an optional validation rule starts with `Where` and ends with `.`. These extra restrictions may not be easily rendered in the syntax without introducing much more notation, which we wish to avoid.
 - Whitespace between a syntax rule, semantics rule, and validation rule is arbitrary, and could include new lines and intentation for aesthetics.
- `x:<Non-terminal>` means that we bind variable `x` to whatever is produced by non-terminal `<Non-terminal>`. We use this variable in the syntax or semantics of this rule.
 - A syntax rule starting with `<Non-terminal1(n<64)>` is a parameterization of different syntax rules for `<Non-terminal1(0)>`, `<Non-terminal1(1)>`, ..., `<Non-terminal1(63)>`, all with the same structure, but possibly using symbol `n` as a variable later in the syntax rule and corresponding semantics and validation rules. When this non-terminal is used after the `:=`, the specific parameter is given like `<Non-terminal(5)>` where `5` can be replaced with any non-negative integer up to 63, or an arithmetic expression in terms of variables like `n`.
 - `||` between byte arrays means concatenation.
 - Function `numbits()` takes a byte and outputs the number of bits set to `1`.


### Definition of the Syntax, Semantics, and Validation Rules

The only terminal symbols are 8-bit bytes, represented in hexary notation.

```
<Byte> := 0x00        {byte with value 0x00}
        | 0x01        {byte with value 0x01}
        | ...
        | 0xff        {byte with value 0xff}

```

First define some non-terminals to simplify later definitions.

```
<U32> := u32:<Byte>^4		{u32 as a 32-bit unsigned integer in big-endian}

<Bytes32> := b:<Byte>^32	{byte array b in big-endian}

<Address> := b:<Byte>^20	{byte array b in big-endian}

<Byte_Nonzero> := 0x01          {byte with value 0x01}
                | 0x02          {byte with value 0x02}
                | ...
                | 0xff          {byte with value 0xff}

<Byte_More_Than_One_Bit_Set> := 0x03          {byte with value 0x03}
                              | 0x05          {byte with value 0x05}
                              | 0x06          {byte with value 0x06}
                              | 0x07          {byte with value 0x07}
                              | 0x09          {byte with value 0x09}
                              | 0x0a          {byte with value 0x0a}
                              | ...
                              | 0x0f          {byte with value 0x0f}
                              | 0x11          {byte with value 0x11}
                              | 0x12          {byte with value 0x12}
                              | ...
                              | 0xff          {byte with value 0xff}

<Bytes2_More_Than_One_Bit_Set> := b1:<Byte> b2case1:<Byte>^numbits(b1)>1 b2case2:<Byte_Nonzero>^numbits(b1)==1 b2case3:<Byte_More_Than_One_Bit_Set>^numbits(b1)==0
                                  {byte array b1||b2case1||b2case2||b2case3}

<Byte_Lower_Nibble_Zero> := 0x00    {byte with value 0x00}
                          | 0x10    {byte with value 0x10}
                          | ...
                          | 0xf0    {byte with value 0xf0}

<Nibbles(n<65)> := nibbles:<Byte>^(n//2) overflownibble:<Byte_Lower_Nibble_Zero>^(n%2)
                   {byte array nibbles||overflownibble}


```

The designated starting non-terminal is `<Block_Witness>`.

```
<Block_Witness> := v:<Version> t:<Tree>^*
                   {tuple of witness trees t}
                   Where we exhaust all bytes available.

<Version> := 0x01
             {the version byte 0x01}

<Tree> := 0xbb m:<Metadata> n:<Tree_Node(0)>
          {a tuple (m, n)}

<Metadata> := 0x00
              {nothing}
            | 0x01 lenid<U32> id:<Byte>^lenid lendata:<U32> data:<Byte>^lendata
              {a tuple (id, data)}
              Where the 0x01 case is disallowed in a block witnesses, but allowed for extending this spec.
```

Next, recursively define the encoding for an Ethereum state tree node, with some nodes possibly replaced by their merkle hash. Following the yellowpaper section 4.1 and appendix D, the world state tree has three types of node: branch, extension, and account. Add a fourth type of node which can replace any node with the merkle hash of the subtree rooted at that node. Note that the parametrization variable `d` represents the nibble-depth.

```
<Tree_Node(d<64)> := 0x00 b:<Branch_Node(d)>
                     {branch node b}
                   | 0x01 e:<Extension_Node(d)>
                     {extension node e}
                   | 0x02 a:<Account_Node(d)>
                     {account node a}
                   | 0x03 h:<Bytes32>
                     {hash node with merkle hash h}

<Branch_Node(d<64)> := bitmask:<Bytes2_More_Than_One_Bit_Set> c[0]:<Tree_Node(d+1)>^bitmask[0]==1 c[1]:<Tree_Node(d+1)>^bitmask[1]==1 ... c[15]:<Tree_Node(d+1)>^bitmask[15]==1
                      {branch node with children nodes (c[0], c[1], ..., c[15]), note that some children may be empty based on the bitmask}

<Extension_Node(d<63)> := nibbleslen:<Byte_Nonzero> nibbles:<Nibbles(nibbleslen)> child:<Child_Of_Extension_Node(d+nibbleslen)>
                          {extension node with values (nibbleslen, nibbles, child)}

<Child_Of_Extension_Node(d<65)> := 0x00 b:<Branch_Node(d)>
                                   {branch node b}
                                 | 0x03 h:<Bytes32>
                                   {hash node with merkle hash h}

<Account_Node(d<65)> := 0x00 pathnibbles:<Nibbles(64-d)> address:<Address> balance:<Bytes32> nonce:<Bytes32>
                        {account node for externally owned account with values (pathnibbles, address, balance, nonce)}
                      | 0x01 pathnibbles:<Nibbles(64-d)> address:<Address> balance:<Bytes32> nonce:<Bytes32> bytecode:<Bytecode> storage:<Account_Storage_Tree_Node(0)>
                        {account node for contract account with values (pathnibbles address balance nonce bytecode storage)}

<Bytecode> := len:<U32> b:<Byte>^len
              {byte array b of length len}
```

Account storage tree nodes are slightly different from world state tree nodes defined above.

```
<Account_Storage_Tree_Node(d<64)> := 0x00 b:<Account_Storage_Branch_Node(d)>
                                     {branch node b}
                                   | 0x01 e:<Account_Storage_Extension_Node(d)>
                                     {extension node e}
                                   | 0x02 a:<Account_Storage_Leaf_Node(d)>
                                     {storage leaf node a}
                                   | 0x03 h:<Bytes32>
                                     {hash node with merkle hash h}

<Account_Storage_Branch_Node(d<64)> := bitmask:<Bytes2_More_Than_One_Bit_Set> c[0]:<Account_Storage_Tree_Node(d+1)>^bitmask[0]==1 c[1]:<Account_Storage_Tree_Node(d+1)>^bitmask[1]==1 ... c[15]:<Account_Storage_Tree_Node(d+1)>^bitmask[15]==1
                                      {branch node with children nodes (c[0], c[1], ..., c[15]), note that some children may be empty based on the bitmask}

<Account_Storage_Extension_Node(d<63)> := nibbleslen:<Byte_Nonzero> nibbles:<Nibbles(nibbleslen)> child:<Child_Of_Account_Storage_Extension_Node(d+nibbleslen)>
                          {extension node with values (nibbleslen, nibbles, child)}

<Child_Of_Account_Storage_Extension_Node(d<65)> := 0x00 b:<Account_Storage_Branch_Node(d)>
                                                   {branch node b}
                                                 | 0x03 h:<Bytes32>
                                                   {hash node with merkle hash h}

<Account_Storage_Leaf_Node(d<65)> := pathnibbles:<Nibbles(64-d))> key:<Bytes32> val:<Bytes32>
                                     {leaf node with value (pathnibbles, key, val)}
```


## Implementer's guide

This section contains a few tips on actually implementing this spec.

#### Simple stack machine execution

One simpler implementation of these rules can be a stack machine, taking one
instruction from the left of the witness and applying rules. That allows one to
rebuild a trie in a single pass.


#### Building hashes.

It might be useful to build hashes together with building the nodes so we can
execute and validate the trie in the same pass.


## Alternatives considered

### GetNodeData

TBD
