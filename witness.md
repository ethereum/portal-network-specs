# Block Witness Formal Specification

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD", "SHOULD NOT", "RECOMMENDED",  "MAY", and "OPTIONAL" in this document are to be interpreted as described in [RFC 2119](https://tools.ietf.org/html/rfc2119).

## Use Cases

The format described in this document can be used to store and build
partial Patricia Merkle Tries and forests in a linear way.

It can be used to store the whole or a partial trie (for executing the block
w/o any trie), or a subtrie of that (can be used for semi-stateless initial
sync).

## Notation & Data types

### Basic data types

`nil` - an empty value.

`Bool` -a boolean value.

`Any` - any data type. MUST NOT be `nil`.

`Int` - an integer value. We treat the domain of integers as infinite,
the overflow behaviour or mapping to the actual data types is undefined
in this spec and should be up to implementation.

`Byte` - a single byte.

`Hash` - 32 byte value, representing a result of Keccak256 hashing.

### Composite data types

`()` - an empty array of arbitrary type.

`(Type...)` - an array of a type `Type`. MUST NOT be empty.

`{field:Type}` - an dictionary with a field `field` of type `Type`.

  - full notation: `type T = {field:Type}`

  - inline `type TBase = T1{field:Type}|T2{field2:Type2}`

### Type Definitions

The type definitions are a bit similar to [Haskell](https://en.wikibooks.org/wiki/Haskell/Type_declarations).
The key differences are how the arrays and type fields are defined.

**Full type definition**
```
type HashNode = {raw_hash:Hash}
type CodeNode = {code:(Byte...)}
type Node = HashNode|CodeNode
```
this definition defines 3 types: `Node`, `HashNode` and `CodeNode`.

Inline type definition
```
type Node = HashNode{raw_hash:Hash}|CodeNode{code:(Byte...)}
```
this definition defines the exact 3 types (`Node`, `HashNode`, `CodeNode` as
the previous one.

the defined type `Node` can be used to pattern-match both `CodeNode` and
`HashNode`.


### The Witness Format

A block witness is a binary format that consists of the following logical
elements:

- witness header;

- list of instructions with parameters.

### The Logical Structure

Here, we will discuss a logical structure of the witness and its elements.

Note, that the keys names in the dictionaries aren't encoded in the binary
format and are serving the purpose to improve readability.

The header at the moment contains the versioning information.
```
type WitnessHeader = {version:Int}
```

The list of instructions is the key element for pattern-matching when building
a trie from the witness. 
We will use a simple naming convention to make them more salient: `BRANCH`, etc

The list of instructions is defined here.

```
type Instruction = LEAF{key:(Byte...) value:(Byte...)}
                 | EXTENSION{key:(Byte...) nonce:Int balance:Int has_code:Bool has_storage:Bool}
                 | HASH{raw_hash:Hash}
                 | CODE{raw_code:(Byte...)}
                 | ACCOUNT_LEAF{key:(Byte...)
                 | BRANCH{mask:Int}
                 | NEW_TRIE{}

type Witness = (INSTRUCTION...)

```

### The Physical structure

Each block witness consists of a header followed by a list of instructions.

There is no length of witness specified anywhere, the code expects to just reach `EOF`.

### Endianness

All the data is interpreted as big-endian.

#### Encoding

##### CBOR

The parts of the key that are encoded with CBOR are marked by the `CBOR` function.

##### Keys

Keys are also using custom encoding to make them more compact.

The nibbles of a key are encoded in a following way `(FLAGS NIBBLE1+NIBBLE2 NIBBLE3+NIBBLE4 NIBBLE5... )`

*FLAGS*
* bit 0 -- 1 if the number of nibbles were odd
* bit 1 -- 1 if the nibbles end with 0x10 (the terminator byte)

This is shown later as `ENCODE_KEY` function.

#### Header

format: `version:byte`

encoded as `( version )`

the current version MUST BE 1.

#### Instructions 

To distinguish between instuctions, they are serialized in the following way:
`(opcode [parameters])`

The `opcode` is a single byte that has a unique identifier of the instruction.
It defines how the next bytes are interpreted.

For some data, like `Hash` or some kind of flags byte, we know the length in
advance, so we can just read the known amount of bytes.

For the other types of data the encoder defines how to interpret it.

Here is how the instuctions are encoded:

* `LEAF` -> `( 0x00 CBOR(ENCODE_KEY(key))... CBOR(value)... )`

* `EXTENSION` -> `( 0x01 CBOR(ENCODE_KEY(key))... )`

* `BRANCH` -> `( 0x02 CBOR(mask)... )`
    *mask* defines which children are present 
    (e.g. `0000000000001011` means that children 0, 1 and 3 are present and the other ones are not)

* `HASH` -> `( 0x03 hash_byte_1 ... hash_byte_32 )`

* `CODE` -> `( 0x04 CBOR(code)... )`

* `ACCOUNT_LEAF` -> `( 0x05 CBOR(ENCODE_KEY(key))... flags /CBOR(nonce).../ /CBOR(balance).../ )`

  *flags* is a bitset encoded in a single byte (bit endian):
    * bit 0 defines if **code** is present; if set to 1, then `has_code=true`;
    * bit 1 defines if **storage** is present; if set to 1, then `has_storage=true`;
    * bit 2 defines if **nonce** is not 0; if set to 0, *nonce* field is not encoded;
    * bit 3 defines if **balance** is not 0; if set to 0, *balance* field is not encoded;

* `NEW_TRIE` -> `( 0xBB )`


## Algorithms

Let's take a look on how to build a witness from a trie and build a trie from
the witness.

### Rebuilding the trie

### Trie Nodes

```
type Node = HashNode{raw_hash:Hash}
          | ValueNode{raw_value:(Byte...)}
          | AccountNode{nonce:Int balance:Int storage:nil|Node code:nil|CodeNode|HashNode}
          | LeafNode{key:(Byte...) value:ValueNode|AccountNode}
          | ExtensionNode{key:(Byte...) child:Node}
          | BranchNode{child0:nil|Node child1:nil|Node child3:nil|Node ... child15:nil|Node}
          | CodeNode{code:(Byte... )}
```


The witness execution environment MUST contain the following 3 elements:

- **WitnessHeader** -- a header containing the version of the witness. The `version` MUST be 1.

- **Witness** -- a witness to be executed;

- **Substitution Rules** -- a list of all possible substitution rules.


## Execution process

Initially, the witness MUST BE an array of `Instruction`s.

Then, as substitution rules are applied to the witness, some elements of the
array are replaced with `Node`s.

The execution continues until there are no substitution rules left to execute.

Here is how the execution code might look like in Go for building a single trie.

```go
witness := GetInitialWitness()
rules := GetSubstitutionRules()
numberOfRulesApplied := 1 // initial state

for numberOfRulesApplied > 0 {
    witness, numberOfRulesApplied := ApplyRules(witness, rules)
}

if len(witness) == 1 {
    trie.root = witness[0]
} else {
    panic("witness execution failed")
}

```


And here is an example of the execution process (we will use the set of rules
form the **Substitution Rules** section of this document):

* **Step 1**. Witness: `(HASH{h1} HASH{h2} BRANCH{0b101} HASH{h3} BRANCH{0b11})`

* **Step 2**. Apply `HASH` substitution rules.
Witness: `(HashNode{h1} HashNode{h2} BRANCH{0b101} HashNode{h3} BRANCH{0b11})`

* **Step 3**. Apply `BRANCH` substitution rules (only once, because `BRANCH{0b11}`
doesn't pass its `GUARD` statements just yet).
Witness: `(BranchNode{0: HashNode{h1} 2:HashNode{h2}} HashNode{h3} BRANCH{0b11})`

* **Step 4**. Apply `BRANCH` substitution rules again.
Witness: `(BranchNode{0: BranchNode{0: HashNode{h1} 2:HashNode{h2}} 1:HashNode{h3}})`

* **Step 5**. No more rules are applicable, the witness contains only one
    element, the execution ends successfully.


## End Criteria

The execution ends when there are no substitution rules applicable for this
witness.

### Building a single trie from the witness

If we are building a single trie from the witness, then the only SUCCESS
execution is when the following are true:

- The execution state MUST match the End Criteria
- There MUST be only one item left in the witness
- This item MUST be one of these types: `LeafNode`, `ExtensionNode`, `BranchNode`
    
In that case, this last item will be the root of the built trie.

Every other end state is considered a FAILURE.


### Building a Forest 

We also can build a forest of tries with this approach, by adding a new
Instruction `NEW_TRIE` and adjusting the success criteria a bit:

- The execution state MUST match the End Criteria;
- The items that are left in the witness MUST follow this pattern:
    `(LeafNode|ExtensionNode|BranchNode NEW_TRIE ... LeafNode|ExtensionNode|BranchNode)`
- Each `LeafNode|ExtensionNode|BranchNode` element root of a trie.

Every other end state is considered a FAILURE.


## Instructions & Parameters

A single instruction consists of substitution rules and parameters.

Each instruction MAY have one or more parameters.
The parameters values MUST be encoded in the witness.

That makes it different from the helper function parameters that MAY come from the stack or MAY come from the witness.


## Building a witness form a trie


## Building a trie from the witness


## Substitution rules

A substitution rule consists of 3 parts: 

`[GUARD] PATTERN |=> RESULT`

- to the left of the `|=>` sign:

    - optional `GUARD` statements;

    - the pattern to match against;

- result, to the right of the `|=>` sign.


### `GUARD`s

Each substitution rule can have zero, one or multiple `GUARD` statements.
Each `GUARD` statement looks like this:

```
GUARD <CONDITION>
```

For a substitution rule to be applicable, the `<CONDITION>` in its `GUARD` statement MUST be true.

If a substitution rule has multiple `GUARD` statements, all of them MUST BE satisfied.

If there are no `GUARD` statements, the substitution rule's applicability is
only defined by the PATTERN.

Example:
```
 GUARD NBITSET(mask) == 2
|---- GUARD STATEMENT ---|

 Node(n0) Node(n1) BRANCH{mask} |=> 
 BranchNode{MAKE_VALUES_ARRAY(mask, n0, n1)}
```

For the example rule to be applicable both facts MUST be true:

1. `mask` contains only 2 bits set to 1 (the rest are set to 0);

2. to the left of `BRANCH` instruction there is at least 2 `Node`s.

Fact (1) comes from the `GUARD` statement.


### PATTERN

`[NodeType(boundVar1)... NodeType(boundVarN)] Instruction[(param1... paramN)]`

A pattern MUST contain a single instruction.
A pattern MAY contain one or more `Node`s to the left of the instruction to
match.
An instruction MAY have one or more parameters.

Pattern matching is happening by the types. `Node` type means any node is
matched, some specific node type will require a specific match.

Pattern can have bound variable names for both matched nodes and instruction
parameters (if present).

Match:

```
HASH{h0} HashNode{h1} HashNode{h2} BRANCH{0b11}
        |------------------- MATCH ------------|

HASH{h0} BranchNode{0: HashNode{h1} 1: HashNode{h2}}
        |----------- SUBSTITUTED -------------------|
```

No match (not enough nodes to the left of the instruction):

```
HASH h0 HASH h1 HashNode{h2} BRANCH{0b11}
```

### Result

`NodeType(HELPER_FUNCTION(arguments))`

The result is a single `Node` statement that replaces the pattern in the
witness if it matches and the guards are passed.

The result MAY contain helper functions or might have in-line computation.
The result MUST have a specific node type. No generic `Node` is allowed.

Helper functions or inline computations might use bound variables from the
pattern. 

Example

```
                             
Node(n0) Node(n1) BRANCH{mask} |=>
BranchNode{MAKE_VALUES_ARRAY(mask, n0, n1)}
                             ^     ^-- ^--- BOUND NODES
                             |---- BOUND INSTRUCTION PARAM
          |------ HELPER CALL ------------|
|----------------- RESULT ------------------|

```

### Bringing it all together


So the full syntax is this:

```
[GUARD <CONDITION> ...] [ NodeType(bound_variable1)... ] INSTRUCTION{(param1 ...)} |=>
Node(<HELPER_FUNCTION_OR_COMPUTATION>)
```

`NodeType` is one of the types of nodes to match. Can also be `Node` to match
any non-nil node.

Substitution rules MUST be non-ambiguous. Even though, there can be multiple
substitution rules applicable to the whole witness at the same time, there MUST
be only one rule that is applicable to a certain position in the witness.

So, the minimal substitution rule is the one for the `HASH` instruction that pushes one hash to the stack:
```
HASH{hashValue} |=> HashNode{hashValue}
```


## Helper functions

Helper functions are functions that are used in GUARDs or substitution rules.

Helper functions MUST be pure.
Helper functions MUST have at least one argument.
Helper functions MAY have variadic parameters: `HELPER_EXAMPLE(arg1, arg2, list...)`.
Helper functions MAY contain recursion.

## Instructions

### `LEAF key raw_value`

**Substitution rules**

Replaces the instruction with a `ValueNode` wrapped with a `LeafNode`.

```
LEAF{key, raw_value} |=> LeafNode{key, ValueNode{raw_value}}
```

### `EXTENSION key`

Wraps a node to the left of the instruction with an `ExtensionNode`.

**Substitution rules**

```
Node(node) EXTENSION{key} |=> ExtensionNode{key, node}
```

### `HASH raw_hash`

Replaces the instruction with a `HashNode`.

**Substitution rules**

```
HASH{hash_value} |=> HashNode{hash_value}
```

### `CODE raw_code`

Replaces the instruction with a `CodeNode`.

```
CODE{raw_code} |=> CodeNode{raw_code}
```

### `ACCOUNT_LEAF key nonce balance has_code has_storage`

Replaces the instruction and, optionally, up to 2 nodes to the left of the
instructon with a single `AccountNode` wrapped with a `LeafNode`.

**Substitution rules**

```
GUARD has_code == true
GUARD has_storage == true

CodeNode(code) Node(storage_hash_node) ACCOUNT_LEAF{key, nonce, balance, has_code, has_storage} |=>
LeafNode{key, AccountNode{nonce, balance, storage_root, code}}

---

GUARD has_code == true
GUARD has_storage == true

HashNode(code) Node(storage_hash_node) ACCOUNT_LEAF{key, nonce, balance, has_code, has_storage} |=>
LeafNode{key, AccountNode{nonce, balance, storage_root, code}}

---

GUARD has_code == false
GUARD has_storage == true

Node(storage_root) ACCOUNT_LEAF{key, nonce, balance, has_code, has_storage} |=>
LeafNode{key, AccountNode{nonce, balance, storage_root, nil}}

---

GUARD has_code == true
GUARD has_storage == false

CodeNode(code) ACCOUNT_LEAF{key, nonce, balance, has_code, has_storage} |=>
LeafNode{key, AccountNode{nonce, balance, nil, code}}

---

GUARD has_code == true
GUARD has_storage == false

HashNode(code) ACCOUNT_LEAF{key, nonce, balance, has_code, has_storage} |=>
LeafNode{key, AccountNode{nonce, balance, nil, nil, code}}

---

GUARD has_code == false
GUARD has_storage == false

ACCOUNT_LEAF{key, nonce, balance, has_code, has_storage} |=>
LeafNode{key, AccountNode{nonce, balance, nil, nil, nil}}

```

### `NEW_TRIE`

No substitution rules. This instruction is used as a "divider" when building
a forest of tries.

### `BRANCH mask`

Replaces `NBITSET(mask)` `Node`s to the left of the instruction with a single
`BranchNode` with these nodes as children according to `mask`.

**Substitution rules**
```

GUARD NBITSET(mask) == 2

Node(n0) Node(n1) BRANCH{mask} |=> 
BranchNode{MAKE_VALUES_ARRAY(mask, n0, n1)}

---

GUARD NBITSET(mask) == 3

Node(n0) Node(n1) Node(n2) BRANCH{mask} |=> 
BranchNode{MAKE_VALUES_ARRAY(mask, n0, n1, n2)}

---

...

---

GUARD NBITSET(mask) == 16

Node(n0) Node(n1) ... Node(n15) BRANCH{mask} |=>
BranchNode{MAKE_VALUES_ARRAY(mask, n0, n1, ..., n15)}
```

## Helper functions

### `MAKE_VALUES_ARRAY`

returns an array of 16 elements, where values from `values` are set to the indices where `mask` has bits set to 1. Every other place has `nil` value there.

**Example**: `MAKE_VALUES_ARRAY(5, [a, b])` returns `[a, nil, b, nil, nil, ..., nil]` (binary representation of 5 is `0000000000000101`)

```
MAKE_VALUES_ARRAY(mask, values...) {
    return MAKE_VALUES_ARRAY(mask, 0, values)
}

MAKE_VALUES_ARRAY(mask, idx, values...) {
    if idx > 16 {
        return []
    }

    if BIT_TEST(mask, idx) {
        return PREPEND(FIRST(values), (MAKE_VALUES_ARRAY mask, INC(idx), REST(values)))
    } else {
        return PREPEND(nil, (MAKE_VALUES_ARRAY mask, INC(idx), values))
    }
}
```


### `NBITSET(number)`

returns number of bits set in the binary representation of `number`.

### `BIT_TEST(number, n)`

`n` MUST NOT be negative.

returns `true` if bit `n` in `number` is set, `false` otherwise.

### `PREPEND(value, array)`

returns a new array with the `value` at index 0 and `array` values starting from index 1

### `INC(value)`

increments `value` by 1

### `FIRST(array)`

returns the first value in the specified array

### `REST(array)`

returns the array w/o the first item


## Validating The Witness

There are a couple of times we can validate the witness corectness.

(1) When reading the binary data:
- if we meet an unknown opcode


## Serialization

The format for serialization of everything except hashes (that we know the
length of) is [CBOR](https://cbor.io). It is RFC-specified and concise.

For hashes we use the optimization of knowing the lengths, so we just read 32
bytes


## Implementer's guide

1. Simple stack machine execution

2. Building hashes

## Alternatives considered
