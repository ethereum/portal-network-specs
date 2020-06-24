Block Witness Formal Specification
---

# 1. Introduction

## 1.1. Design Goals

### 1.1.1. Semantics

**Language-independent.** The semantics shouldn't depend on features of
specific programming languages.

**Platform-independent.** The semantics shouldn't depend on features of
specific programming platforms or operating systems.

**Hardware-independent.** The semantics shouldn't depend on features of
specific hardware platforms.

**Well defined.** The semantics should fully and precisely define valid witnesses in a way that is easy to reason about.

### 1.1.2. Representation

**Efficient.** Witness should be decoded, validated and executed in a single pass with minimum dynamic memory allocation.

**Streamable (without intermediate dynamic buffers).** It should be possible to 'stream-as-you-encode' the trie on one node, and recreate it at the same time, by using a fixed allocated buffer. That helps to efficiently transfer and encode/decode witnesses.

The witness allows you to walk through the trie and to produce the witness as you go without buffering;
sending it straight to a network socket. A peer can then receive it from the socket
and start computing the hash of the state root straight away.

Also, it means that the memory consumption of witness processing itself will be
fixed and predictable, which helps nodes that have limited memory.

**Chunkable.** It should be possible to split witness in chunks that are independently verifiable to speed-up witness propagation in the network.

The witness format doesn't limit a chunk size. That makes it easy to experiment with and find the best size for efficient relaying properties.

**Upgradeable.** It should be able to upgrade witness format in the future in a backward compatible way (e.g. new versions of clients will support the old versions of the witness). Old versions of clients should be able to discard unsupported
versions of witness.

**Compact.** Witness should have a binary format that is compact to save bandwidth when propagating in network.


## 1.2. Scope

Witnesses are a way to efficiently store, transmit and recover Merkle Patricia multiproofs. That makes them flexible and they can be used in different environments for different purposes.

This document is only concerned with witness abstract syntax, semantics, binary
encoding, validation & execution semantics.

It does not:
- define how the witnesses are being propagated across the network.
- provide specific implementation algorithms, and way to optimize it.
- provide suggestions on specific use cases of witnesses in sync, hash checks and state storage.
- provide explanations on how stateless ethereum works in general.

In the present version the specification is catered for hexary trie support. Binary trie support will be added later as a change to the specification.

The specification is complemented by a [Stateless Ethereum overview document](./README.md), an [implementer's handbook](TBD), [example code](TBD) and [tests](TBD) to help with the specific implementation.


## 1.3. Security Considerations

TBD

## 1.4. Dependencies

This specification depends on the following specifications and standards:

- [Ethereum Yellow Paper](https://ethereum.github.io/yellowpaper/paper.pdf)

- [RFC2119](https://tools.ietf.org/html/rfc2119): The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD", "SHOULD NOT", "RECOMMENDED",  "MAY", and "OPTIONAL" in this document are to be interpreted as described in [RFC 2119](https://tools.ietf.org/html/rfc2119).

## 1.5. Overview

### 1.5.1. Semantic Phases

The semantics of the block witness can be divided into phases:

**Decoding** witnesses are distributed in binary format. Decoding process
processes that format and converts it into an internal representation of a
witness. In this specification this representation is modelled by the abstract
syntax, but it could be represented as classes and functions of a programming
language used to implement witnesses support.

**Execution** is the phase, where the multiproof is being built from the
specified block witness.

**Validation** of the witness is happening during both decoding and execution.
- *Validation while decoding* checks that the witness binary representation only contains opcodes valid for specified version and that serialized data matches the defined syntax.
- *Validation while executing* checks that it is possible to build one or more valid multiproofs out of the internal representation and that that consumes the whole witness.

# 2. Syntax, Semantics, and Validation

The binary format of an Ethereum block witness is a byte array whose structure is defined in this section.
The witness encoding is defined using [context-free](https://en.wikipedia.org/wiki/Context-free_grammar) syntax rules.
We equip each syntax rule with semantics, which gives us a [syntax-directed translation](https://en.wikipedia.org/wiki/Syntax-directed_translation)
from the binary format to a client's internal representation of a block witness.
With each syntax rule, we may also give additional restrictions, which we refer to as "validation rules".

## 2.1. Notation

First, we define the notation which will be used to define the syntax, semantics, and validation rules.

 - We use [Backus-Naur form](https://en.wikipedia.org/wiki/Backus%E2%80%93Naur_form) notation, namely symbols like `|`, `::=`, `>`, and `<` are used to define production rules.
 - Because this is a binary format, the only terminal symbols are bytes, which we write in hexadecimal notation `0x00`, `0x01`, ..., and `0xff`.
 - Parentheses `(` and `)` enclose a tuple.
 - Brackets `[` and `]` are used to index an element of a tuple. `T[i]` denotes the `i`th element of `n`-tuple `T`, where `i` is either `0`, `1`, ..., or `n-1`. The tuple can be of any elements. Notably, we use a variable named `bitmask` for a tuple of bits, e.g. `bitmask[0]` represents the leftmost bit.
 - Ellipses `...` are notation for "and so on until", and are used to avoid writing a long enumerated tuple. For example, `A[1] A[2] ... A[5]` is short-hand notation for `A[1] A[2] A[3] A[4] A[5]`.
 - `A^n` represents symbol `A` repeated `n` times. We allow `n` to be `0`, representing zero occurrences of `A`.
 - `A^+` represents symbol `A` repeated one or more times.
 - `A^*` represents symbol `A` repeated zero or more times.
 - Curly braces `{` and `}` after each syntax rule enclose semantics, which describe what is produced by that syntax rule.
 - After each semantics rule, an optional validation rule starts with `Where` and ends with `.`. These validation rules are extra restrictions on the syntax or semantics. Perhaps these restrictions can be rendered directly in syntax or semantics rules, but using validation rules is more concise.
 - Whitespace between a syntax rule, semantics rule, and validation rule is arbitrary, and could include new lines and indentation for aesthetics.
- `x:<Non-terminal>` means that we bind variable `x` to whatever is produced by non-terminal `<Non-terminal>`. We use this variable in the syntax or semantics of this rule.
 - A syntax rule starting with `<Non-terminal1(0<=n<64)>` is a parameterization of different syntax rules for `<Non-terminal1(0)>`, `<Non-terminal1(1)>`, ..., `<Non-terminal1(63)>`, each with the same structure, but using symbol `n` as a bound variable later in the syntax rule, and in corresponding semantics and validation rules. When this non-terminal is used after the `:=`, the specific parameter is given like `<Non-terminal1(k)>` where `k` is a non-negative integer up to 63 or an arithmetic expression in terms of bound variables. This notation is generalized for multiple parameters, using a comma to separate parameters, `<Non-terminal2(0<=d<65,0<=s<2)>`.
 - In place of a variable, there may be an arithmetic or logical expression in terms of bound variables. The expression is evaluated to an integer. For example, `A^(n-7)` represents `A` repeated `n-7` times, where `n` is a bound variable representing a non-negative integer. We omit defining the structure of arithmetic expressions, we just use standard notation for binary infix operations `+`, `-`, `*`, modulo `%`, floor division `//`. Logical expressions use binary infix relations `<`, `>`, `<=`, `>=`, and `==`, evaluating to integer `0` if false and `1` if true. Order of operations is standard, and parentheses `(`, `)` enclose expressions to be evaluated first.
 - `||` between bytes or byte arrays means concatenation.
 - Function `numbits()` takes a byte or tuple of bytes, and outputs the number of bits set to `1`.


## 2.2. Definition of the Syntax, Semantics, and Validation Rules

The only terminal symbols are 8-bit bytes, represented in hexadecimal notation. First define some base non-terminals to simplify later non-terminals.

```
<Byte> ::= 0x00        {byte with value 0x00}
        | 0x01        {byte with value 0x01}
        | ...
        | 0xff        {byte with value 0xff}
```

Define some non-terminals to simplify later definitions. The rule for `Nibbles` pads the final byte with zero bits if there are an odd number of nibbles.

```
<Bytes2> ::= b:<Byte>^2          {byte array b in big-endian}

<Bytes32> ::= b:<Byte>^32        {byte array b in big-endian}

<Address> ::= b:<Byte>^20        {byte array b in big-endian}

<Byte_Nonzero> ::= 0x01          {byte with value 0x01}
                 | 0x02          {byte with value 0x02}
                 | ...
                 | 0xff          {byte with value 0xff}

<Nibbles(0<=n<65)> ::= nibbles:<Byte>^(n//2) overflownibble:<Byte>^(n%2)
                       {byte array nibbles||overflownibble}
                       Where `overflownibble`, if it is non-empty, has its least significant 4 bits set to zero.
```


Next, a variable-length integer encoding. [LEB128](https://en.wikipedia.org/wiki/LEB128#Unsigned_LEB128), with the restriction that the most-significant "chunk" is non-zero. We use `>>` and `<<` as the standard logical bit-shift operators.

```
Integer(0<n<=256) ::= low:<Byte> high:<Integer(n-7)>^(low>>7)
                      {Integer high<<7 + low - 128*(low>>7) where we assign high=0 if (low>>7)==0.}
                      Where low<2^n and where high==0 only if (low>>7)==0.
```


The designated starting non-terminal is `<Block_Witness>`.

```
<Block_Witness> ::= v:<Version> t:<Tree>^*
                   {tuple of witness tries t}
                   Where we exhaust all bytes available.

<Version> ::= 0x01
             {the version byte 0x01}

<Tree> ::= 0x00 n:<Tree_Node(0)>
           {tree root node n}
```
The rule for `Tree` includes an unused byte `0x00` which may be used in the future to extend the spec in a backwards-compatible way.

Next, recursively define the encoding for all Ethereum trie nodes, with some nodes possibly replaced by their merkle hash. Following the yellowpaper section 4.1 and appendix D, the trie has three types of nodes: branch, extension, and leaf. Add a fourth type of node which can replace any node with the merkle hash of the subtrie rooted at that node. Note that the parametrization variable `d` represents the nibble-depth and `s` represents a flag which is `0` when this node is in the account trie and `1` when in a storage trie.

```
<Tree_Node(0<=d<65,0<=s<2)> ::= 0x00 b:<Branch_Node(d,s)>
                                {branch node b}
                              | 0x01 e:<Extension_Node(d,s)>
                                {extension node e}
                              | 0x02 a:<Leaf_Node(d,s)>
                                {account node a}
                              | 0x03 h:<Bytes32>
                                {hash node with merkle hash h}

<Branch_Node(0<=d<64,0<=s<2)> ::= bitmask:<Bytes2> c[0]:<Tree_Node(d+1,s)>^(bitmask[0]==1) c[1]:<Tree_Node(d+1,s)>^(bitmask[1]==1) ... c[15]:<Tree_Node(d+1,s)>^(bitmask[15]==1)
                                  {branch node with children nodes (c[0], c[1], ..., c[15]), note that some children may be empty based on the bitmask}
                                  Where numbits(`bitmask`)>=2.

<Extension_Node(0<=d<63,0<=s<2)> ::= nibbleslen:<Byte_Nonzero> nibbles:<Nibbles(nibbleslen)> child:<Child_Of_Extension_Node(d+nibbleslen,s)>
                                     {extension node with values (nibbleslen, nibbles, child)}

<Child_Of_Extension_Node(0<=d<65,0<=s<2)> ::= 0x00 b:<Branch_Node(d,s)>
                                              {branch node b}
                                            | 0x03 h:<Bytes32>
                                              {hash node with merkle hash h}

<Leaf_Node(0<=d<65,0<=s<2)> ::= accountleaf:<Account_Node(d)>^(s==0) storageleaf:<Storage_Leaf_Node(d)>^(s==1)
                                {leaf node accountleaf or storageleaf, depending on whether s==0 or s==1}

<Account_Node(0<=d<65)> ::= 0x00 address:<Address> balance:<Integer(256)> nonce:<Integer(256)>
                            {externally owned account node with values (address, balance, nonce)}
                          | 0x01 address:<Address> balance:<Integer(256)> nonce:<Integer(256)> bytecode:<Bytecode> storage:<Tree_Node(0,1)>
                            {contract account node with values (address balance nonce bytecode storage)}

<Bytecode> ::= 0x00 codelen:<Integer(32)> b:<Byte>^codelen
               {byte array b of length codelen}
               Where code b must be accessed in the block, otherwise use case 0x01.
             | 0x01 codelen:<Integer(32)> codehash:<Bytes32>
               {tuple (codelen, codehash)}

<Storage_Leaf_Node(0<=d<65)> ::= key:<Bytes32> val:<Bytes32>
                                 {leaf node with value (key, val)}
```


# 3. Execution

TBD

# 4. Properties

## 4.1. Unambiguity

For a witness `w`, we write `<Block_Witness> ::=* w`, to mean that the non-terminal `<Block_Witness>` derives `w` in one or many steps. In general, there can exist many ways to derive a given `w`. Each derivation is modeled by a parse tree. If there is any witness with more than one parse tree, then the grammar is termed ambiguous. If there exist exactly one parse tree for every sentence derived from the grammar, then the grammar is termed unambiguous.

Claim: The witness grammar is unambiguous.

Proof: The rules with a single body cannot introduce ambiguity. Consider the rules with multiple bodies, rules for the non-terminals `<Byte>`, `<Byte_Nonzero>`, `<Byte_More_Than_One_Bit_Set>`, `<Bytes2_More_Than_One_Bit_Set>`, `<Byte_Lower_Nibble_Zero>`, `<Metadata>`, `<Tree_Node(d)>`, `<Child_Of_Extension_Node(d)>`, `<Account_Node(d)>`, `Account_Storage_Tree_Node(d)>`, and `<Child_Of_Account_Storage_Extension_Node(d)>`. The first byte determines the choice of the rule to be applied. So, the above grammar is LL(1), meaning there is at most one rule in the parsing table. Hence, the grammar is unambiguous by construction.


## 5. Alternatives considered

### 5.1. GetNodeData

TBD
