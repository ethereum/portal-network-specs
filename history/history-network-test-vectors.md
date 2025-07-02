# History Network Test Vectors

## Content Id Derivations

Following the testing of the encoding and decoding of the keys, we also test the proper derivation
of the corresponding `content-id`. This is given as both the hex string and corresponding raw U256 integer.

#### Block Body Key

##### Input Parameters

```
block_number = 12345678
```

##### Expected Output

```
content_key = 0x094e61bc0000000000
content_id = 0x614e3d0000000000000000000000000000000000000000000000000000000009
content_id: U256 = 44012581390156707874310974263613699127815223388818970640389075388176810377225
```

#### Receipt Key

##### Input Parameters

```
block_number = 12345678
```

##### Expected Output

```
content_key = 0x0a4e61bc0000000000
content_id = 0x614e3d000000000000000000000000000000000000000000000000000000000a
content_id: U256 = 44012581390156707874310974263613699127815223388818970640389075388176810377226
```

## Content Value

TODO
