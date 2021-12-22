from typing import (
    Callable,
    Dict,
    List,
    NamedTuple,
    Iterable,
    Optional,
    Sequence,
    Tuple,
    TypedDict,
)

from toolz import groupby, concat
from eth_utils import (
    to_int,
    to_tuple,
    to_canonical_address,
    decode_hex,
)
from eth_typing import (
    Address,
    ChecksumAddress,
    HexStr,
)
from hexbytes import (
    HexBytes,
)
from eth.vm import mnemonics

from web3 import Web3
from web3.method import (
    Method,
    default_root_munger,
)
from web3.module import (
    Module,
)
from web3.types import (
    BlockIdentifier,
)

from web3.types import RPCEndpoint


class RPC:
    debug_traceBlock = RPCEndpoint("debug_traceBlockByNumber")


class RawTraceEntry(TypedDict, total=False):
    depth: int
    error: str
    gas: int
    gasCost: int
    memory: List[HexStr]
    op: str
    pc: int
    stack: List[HexStr]
    storage: Dict[HexStr, HexStr]


class RawTrace(TypedDict):
    gas: int
    failed: bool
    returnValue: HexStr
    structLogs: List[RawTraceEntry]


class RawTraceResult(TypedDict):
    result: RawTrace


class TraceEntry(NamedTuple):
    pc: int
    op: str
    gas: int
    gasCost: int
    depth: int
    stack: Tuple[HexBytes, ...]


class Trace(NamedTuple):
    gas: int
    failed: bool
    returnValue: HexBytes
    structLogs: Tuple[TraceEntry, ...]


def _block_trace_formatter(raw_traces: Sequence[RawTraceResult]) -> Tuple[Trace, ...]:
    return tuple(
        Trace(
            gas=rt['result']['gas'],
            failed=rt['result']['failed'],
            returnValue=HexBytes(decode_hex(rt['result']['returnValue'])),
            structLogs=tuple(
                TraceEntry(
                    pc=sl['pc'],
                    op=sl['op'],
                    gas=sl['gas'],
                    gasCost=sl['gasCost'],
                    depth=sl['depth'],
                    stack=tuple(
                        to_int(hexstr=item) for item in sl['stack']
                    ),
                ) for sl in rt['result']['structLogs']
            ),
        ) for rt in raw_traces
    )


def block_trace_formatter(module: Module, method: RPCEndpoint) -> Callable[[RawTrace], RawTrace]:
    return _block_trace_formatter


debug_traceBlock: Method[Callable[[BlockIdentifier], RawTrace]] = Method(
    RPC.debug_traceBlock,
    mungers=[default_root_munger],
    result_formatters=block_trace_formatter,
)


class DebugTraceModule(Module):
    trace_block = debug_traceBlock


class AccountAccessList(NamedTuple):
    address: ChecksumAddress
    slots: Tuple[int, ...]


AccessList = Tuple[AccountAccessList, ...]


class StateAccess(NamedTuple):
    address: Address
    slot: Optional[int] = None


class TxMeta(NamedTuple):
    sender: Address
    to: Optional[Address]
    value: int
    data: bytes
    gas: int
    gas_price: int
    nonce: int


CALL_OPS = {
    mnemonics.CALL,
    mnemonics.CALLCODE,
    mnemonics.STATICCALL,
    mnemonics.DELEGATECALL,
}
BENIGN_OPS = {
    # Arithmetic
    mnemonics.STOP,
    mnemonics.ADD,
    mnemonics.MUL,
    mnemonics.SUB,
    mnemonics.DIV,
    mnemonics.SDIV,
    mnemonics.MOD,
    mnemonics.SMOD,
    mnemonics.ADDMOD,
    mnemonics.MULMOD,
    mnemonics.EXP,
    mnemonics.SIGNEXTEND,
    mnemonics.SHL,
    mnemonics.SHR,
    mnemonics.SAR,
    # Comparisons
    mnemonics.LT,
    mnemonics.GT,
    mnemonics.SLT,
    mnemonics.SGT,
    mnemonics.EQ,
    mnemonics.ISZERO,
    mnemonics.AND,
    mnemonics.OR,
    mnemonics.XOR,
    mnemonics.NOT,
    mnemonics.BYTE,
    # SHA
    mnemonics.SHA3,
    # Environment
    mnemonics.ADDRESS,
    mnemonics.CALLER,
    # BLOCK
    mnemonics.COINBASE,
    mnemonics.TIMESTAMP,
    mnemonics.NUMBER,
    mnemonics.DIFFICULTY,
    mnemonics.GASLIMIT,
    mnemonics.BASEFEE,
    # PC
    mnemonics.PC,
    # Memory
    mnemonics.MSTORE,
    mnemonics.MSTORE8,
    mnemonics.MLOAD,
    mnemonics.MSIZE,
    # System
    mnemonics.CALLVALUE,
    mnemonics.CALLDATALOAD,
    mnemonics.CALLDATASIZE,
    mnemonics.CALLDATACOPY,
    mnemonics.RETURNDATASIZE,
    mnemonics.RETURNDATACOPY,
    mnemonics.GAS,
    mnemonics.JUMP,
    mnemonics.JUMPI,
    mnemonics.JUMPDEST,
    mnemonics.STOP,
    mnemonics.RETURN,
    mnemonics.REVERT,
    # DUP
    mnemonics.DUP1,
    mnemonics.DUP2,
    mnemonics.DUP3,
    mnemonics.DUP4,
    mnemonics.DUP5,
    mnemonics.DUP6,
    mnemonics.DUP7,
    mnemonics.DUP8,
    mnemonics.DUP9,
    mnemonics.DUP10,
    mnemonics.DUP11,
    mnemonics.DUP12,
    mnemonics.DUP13,
    mnemonics.DUP14,
    mnemonics.DUP15,
    mnemonics.DUP16,
    # LOG
    mnemonics.LOG0,
    mnemonics.LOG1,
    mnemonics.LOG2,
    mnemonics.LOG3,
    mnemonics.LOG4,
    # POP
    mnemonics.POP,
    # PUSH
    mnemonics.PUSH1,
    mnemonics.PUSH2,
    mnemonics.PUSH3,
    mnemonics.PUSH4,
    mnemonics.PUSH5,
    mnemonics.PUSH6,
    mnemonics.PUSH7,
    mnemonics.PUSH8,
    mnemonics.PUSH9,
    mnemonics.PUSH10,
    mnemonics.PUSH11,
    mnemonics.PUSH12,
    mnemonics.PUSH13,
    mnemonics.PUSH14,
    mnemonics.PUSH15,
    mnemonics.PUSH16,
    mnemonics.PUSH17,
    mnemonics.PUSH18,
    mnemonics.PUSH19,
    mnemonics.PUSH20,
    mnemonics.PUSH21,
    mnemonics.PUSH22,
    mnemonics.PUSH23,
    mnemonics.PUSH24,
    mnemonics.PUSH25,
    mnemonics.PUSH26,
    mnemonics.PUSH27,
    mnemonics.PUSH28,
    mnemonics.PUSH29,
    mnemonics.PUSH30,
    mnemonics.PUSH31,
    mnemonics.PUSH32,
    # SWAP
    mnemonics.SWAP1,
    mnemonics.SWAP2,
    mnemonics.SWAP3,
    mnemonics.SWAP4,
    mnemonics.SWAP5,
    mnemonics.SWAP6,
    mnemonics.SWAP7,
    mnemonics.SWAP8,
    mnemonics.SWAP9,
    mnemonics.SWAP10,
    mnemonics.SWAP11,
    mnemonics.SWAP12,
    mnemonics.SWAP13,
    mnemonics.SWAP14,
    mnemonics.SWAP15,
    mnemonics.SWAP16,
}
READ_OPS = {
    mnemonics.SLOAD,
}
WRITE_OPS = {
    mnemonics.SSTORE,
}


class CallContext(NamedTuple):
    sender: Address
    storage: Address
    self: Address
    code: Address
    value: int


@to_tuple
def get_access_events(
        tx_meta: TxMeta,
        trace: Trace) -> Iterable[StateAccess]:
    yield StateAccess(tx_meta.sender)

    if tx_meta.to is None:
        assert False
    else:
        yield StateAccess(tx_meta.to)

    context = CallContext(
        sender=tx_meta.sender,
        self=tx_meta.to,
        storage=tx_meta.to,
        code=tx_meta.to,
        value=tx_meta.value,
    )

    stack = []

    for idx, entry in enumerate(trace.structLogs):
        while entry.depth <= len(stack):
            context = stack.pop()

        if entry.op in BENIGN_OPS:
            continue
        elif entry.op in READ_OPS:
            if entry.op == mnemonics.SLOAD:
                yield StateAccess(context.storage, entry.stack[-1])
            else:
                assert False, f"not handled: op={entry.op}"
        elif entry.op in WRITE_OPS:
            assert False, f"not handled: op={entry.op}"
        elif entry.op in CALL_OPS:
            if entry.op == mnemonics.DELEGATECALL:
                _, code_address_as_int, _, _, _, _ = entry.stack[-6:]
                code_address = code_address_as_int.to_bytes(20, 'big')
                stack.append(context)
                context = CallContext(
                    sender=context.sender,
                    self=context.self,
                    storage=context.storage,
                    code=code_address,
                    value=context.value,
                )
                yield StateAccess(code_address)
            else:
                assert False, f"not handled: op={entry.op}"
        else:
            raise ValueError(f"Unsupported opcode: op={entry.op}")


def get_block_access_list(
        w3: Web3,
        block_identifier: BlockIdentifier,
        trace: Optional[Trace] = None) -> AccessList:
    if trace is None:
        trace = w3.debug_trace.trace_block(block_identifier)
    block = w3.eth.get_block(block_identifier, full_transactions=True)

    tx_metas = tuple(
        TxMeta(
            sender=to_canonical_address(tx['from']),
            to=to_canonical_address(tx['to']),
            value=tx['to'],
            data=tx['input'],
            gas=tx['gas'],
            gas_price=tx['gasPrice'],
            nonce=tx['nonce'],
        ) for tx in block['transactions']
    )
    access_events_by_tx = tuple(
        get_access_events(tx_meta, tx_trace)
        for tx_meta, tx_trace
        in zip(tx_metas, trace)
    )
    block_access_events = tuple(concat(access_events_by_tx))
    access_event_groups = groupby('address', block_access_events)
    access_list: AccessList = tuple(
        AccountAccessList(
            address=address,
            slots=tuple(sorted({event.slot for event in events}))
        )
        for address, events
        in sorted(access_event_groups.items())
    )
    return access_list


def attach_to_w3(w3: Web3):
    from web3._utils.module import attach_modules

    modules = {
        'debug_trace': (DebugTraceModule,),
    }
    attach_modules(w3, modules)
