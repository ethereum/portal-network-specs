Block Witness Formal Specification
---


# 1. Introduction

## 1.1. Design Goals

### 1.1.1. Semantics

**Language-independent**

**Platform-independent**

**Hardware-independent**

**Well defined**
The semantics should fully and precisely define valid witnesses in a way that
is easy to reason about.

### 1.1.2. Representation

**Efficient**
Witness should be decoded, validated and executed in a single pass with minimum
dynamic memory allocation.

**Streamable without intermediate dynamic buffer**
It should be possible to 'stream-as-you-encode' the trie on one node,
and recreate it at the same time, by using a fixed allocated buffer. That helps
to efficiently transfer and encode/decode witnesses.

The witness allows you to walk through the trie and to produce the witness as you go without buffering;
sending it straight to a network socket. A peer can then receive it from the socket
and start computing the hash of the state root straight away.

Also, it means that the memory consumption of witness processing itself will be
fixed and predictable, which helps nodes that have limited memory.

**Chunkable**
It should be possible to split witness in chunks that are independently
verifiable to speed-up witness propagation in the network.

The witness format doesn't limit a chunk size. That makes it easy to experiment with and find
the best size for efficient relaying properties.

**Upgradeable**
It should be able to upgrade witness format in the future in a backward
compatible way (e.g. new versions of clients will support the old versions of
the witness). Old versions of clients should be able to discard unsupported
versions of witness.

**Compact**
Witness should have a binary format that is compact to save bandwith when
propagating in network.


# 2. Syntax, Semantics, and Validation

The binary format of an Ethereum block witness is a byte array whose structure is defined in this section.
The witness encoding is defined using [context-free](https://en.wikipedia.org/wiki/Context-free_grammar) syntax rules.
We equip each syntax rule with semantics, which gives us a [syntax-directed translation](https://en.wikipedia.org/wiki/Syntax-directed_translation)
from the binary format to a client's internal representation of a block witness.
With each syntax rule, we may also give additional restrictions, which we refer to as "validation rules".

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD", "SHOULD NOT", "RECOMMENDED",  "MAY", and "OPTIONAL" in this document are to be interpreted as described in [RFC 2119](https://tools.ietf.org/html/rfc2119).

## 2.1. Notation

First, we define the notation which will be used to define the syntax, semantics, and validation rules.

 - We use Backus-Naur form notation, namely symbols like `|`, `:=`, `>`, and `<` are used to define production rules.
 - Because this is a binary format, the only terminal symbols are bytes, which we write in hexadecimal notation `0x00`, `0x01`, ..., and `0xff`.
 - Parentheses `(` and `)` enclose a tuple. 
 - Brackets `[` and `]` are used to index an element of a tuple, for example the `i`th element of tuple `T` is denoted `T[i]`. 
 - Brackets following a variable named `bitmask` means that the index is of a bit, e.g. `bitmask[0]` represents the leftmost bit.
 - Ellipses `...` are notation for "and so on until", and are used to avoid writing a long enumerated tuple. For example, `A[1] A[2] ... A[5]` is short-hand notation for `A[1] A[2] A[3] A[4] A[5]`.
 - `A^n` represents symbol `A` repeated `n` times. We allow `n` to be `0`, representing zero occurances of `A`. Also, if there is a logical expression in place of `n`, then a false expression is replaced by `0` and a true expression is replaced with `1`.
 - `A^+` represents symbol `A` repeated one or more times.
 - `A^*` represents symbol `A` repeated zero or more times.
 - Curly braces `{` and `}` enclose semantics after each syntax rule.
 - Semantics are just an English explanation of what is produced by that syntax rule.
 - After each semantics rule, an optional validation rule starts with `Where` and ends with `.`. These extra restrictions may not be easily rendered in the syntax without introducing much more notation, which we wish to avoid.
 - Whitespace between a syntax rule, semantics rule, and validation rule is arbitrary, and could include new lines and indentation for aesthetics.
- `x:<Non-terminal>` means that we bind variable `x` to whatever is produced by non-terminal `<Non-terminal>`. We use this variable in the syntax or semantics of this rule.
 - A syntax rule starting with `<Non-terminal1(n<64)>` or `<Non-terminal2(d<65,s<2)>` is a parameterization of different syntax rules for `<Non-terminal1(0)>`, `<Non-terminal1(1)>`, ..., `<Non-terminal1(63)>` and similarly for `<Non-terminal2(0,0)>`,...,`<Non-terminal2(64,1)>`, each with the same structure, but using symbols `n`,`d`, and `s` as bound variables later in the syntax rule and corresponding semantics and validation rules. When this non-terminal is used after the `:=`, the specific parameter is given like `<Non-terminal1(k)>` where `k` is a non-negative integer up to 63 or an arithmetic expression in terms of bound variables.
 - `||` between byte arrays means concatenation.
 - Function `numbits()` takes a byte and outputs the number of bits set to `1`.


## 2.2. Definition of the Syntax, Semantics, and Validation Rules

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
            | 0x01 lenid:<U32> id:<Byte>^lenid lendata:<U32> data:<Byte>^lendata
              {a tuple (id, data)}
              Where the 0x01 case is disallowed in a block witnesses, but allowed for extending this spec.
```

Next, recursively define the encoding for an Ethereum tree nodes, with some nodes possibly replaced by their merkle hash. Following the yellowpaper section 4.1 and appendix D, the tree has three types of nodes: branch, extension, and leaf. Add a fourth type of node which can replace any node with the merkle hash of the subtree rooted at that node. Note that the parametrization variable `d` represents the nibble-depth and `s` represents a flag which is `0` when this node is in the account tree and `1` when in a storage tree.

```
<Tree_Node(d<65,s<2)> := 0x00 b:<Branch_Node(d,s)>
                         {branch node b}
                       | 0x01 e:<Extension_Node(d,s)>
                         {extension node e}
                       | 0x02 a:<Leaf_Node(d,s)>
                         {account node a}
                       | 0x03 h:<Bytes32>
                         {hash node with merkle hash h}

<Branch_Node(d<64,s<2)> := bitmask:<Bytes2_More_Than_One_Bit_Set> c[0]:<Tree_Node(d+1,s)>^bitmask[0]==1 c[1]:<Tree_Node(d+1,s)>^bitmask[1]==1 ... c[15]:<Tree_Node(d+1,s)>^bitmask[15]==1
                      {branch node with children nodes (c[0], c[1], ..., c[15]), note that some children may be empty based on the bitmask}

<Extension_Node(d<63,s<2)> := nibbleslen:<Byte_Nonzero> nibbles:<Nibbles(nibbleslen)> child:<Child_Of_Extension_Node(d+nibbleslen,s)>
                              {extension node with values (nibbleslen, nibbles, child)}

<Child_Of_Extension_Node(d<65,s<2)> := 0x00 b:<Branch_Node(d,s)>
                                       {branch node b}
                                     | 0x03 h:<Bytes32>
                                       {hash node with merkle hash h}

<Leaf_Node(d<65,s<2)> := accountleaf:<Account_Node(d)>^s==0 storageleaf:<Storage_Leaf_Node(d)>^s==1
                         {leaf node accountleaf or storageleaf, depending on whether s==0 or s==1}

<Account_Node(d<65)> := 0x00 pathnibbles:<Nibbles(64-d)> address:<Address> balance:<Bytes32> nonce:<Bytes32>
                        {account node for externally owned account with values (pathnibbles, address, balance, nonce)}
                      | 0x01 pathnibbles:<Nibbles(64-d)> address:<Address> balance:<Bytes32> nonce:<Bytes32> code:<Bytecode> storage:<Account_Storage_Tree_Node(0)>
                        {account node for executed contract account with values (pathnibbles address balance nonce code storage)}
                      | 0x02 pathnibbles:<Nibbles(64-d)> address:<Address> balance:<Bytes32> nonce:<Bytes32> codehash:<Bytes32> codesize:<U32> storage:<Account_Storage_Tree_Node(0)>
                        {account node for contract account with values (pathnibbles address balance nonce codehash codesize storage)}

<Bytecode> := len:<U32> b:<Byte>^len
              {byte array b of length len}

<Storage_Leaf_Node(d<65)> := pathnibbles:<Nibbles(64-d))> key:<Bytes32> val:<Bytes32>
                             {leaf node with value (pathnibbles, key, val)}
```


# 3. Execution

TBD

# 4. Properties

## 4.1. Unambiguity

For a witness `w`, we write `<Block_Witness> :=* w`, to mean that the non-terminal `<Block_Witness>` derives `w` in one or many steps. In general, there can exist many ways to derive a given `w`. Each derivation is modelled by a parse tree. If there is any witness with more than one parse trees, then the grammar is termed ambiguous. If there exist exactly one parse tree for every sentence derived from the grammar, then the grammar is termed unambiguous.

Claim: The witness grammar is unambiguous. 

Proof: The rules with a single body cannot introduce ambiguity. Consider the rules with multiple bodies, rules for the non-terminals `<Byte>`, `<Byte_Nonzero>`, `<Byte_More_Than_One_Bit_Set>`, `<Bytes2_More_Than_One_Bit_Set>`, `<Byte_Lower_Nibble_Zero>`, `<Metadata>`, `<Tree_Node(d)>`, `<Child_Of_Extension_Node(d)>`, `<Account_Node(d)>`, `Account_Storage_Tree_Node(d)>`, and `<Child_Of_Account_Storage_Extension_Node(d)>`. The first byte determines the choice of the rule to be applied. So, the above grammar is LL(1), meaning there is at most one rule in the parsing table. Hence, the grammar is unambiguous by construction.

# 5. Implementer's guide

This section contains some guidelines on actually implementing this spec.

## 5.1. Simple stack machine execution

One simpler implementation of these rules can be a stack machine, taking one
instruction from the left of the witness and applying rules. That allows one to
rebuild a trie in a single pass.


### 5.2. Building hashes.

It might be useful to build hashes together with building the nodes so we can
execute and validate the trie in the same pass.


## 6. Alternatives considered

### 6.1. GetNodeData

TBD
