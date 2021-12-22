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
                        decode_hex(item) for item in sl['stack']
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
    "CALL",
}
BENIGN_OPS = {
    "STOP",
}
READ_OPS = {
    "SLOAD",
}
WRITE_OPS = {
    "SSTORE",
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
        trace_entries: Sequence[TraceEntry]) -> Iterable[StateAccess]:
    yield StateAccess(tx_meta.sender)
    if tx_meta.to is None:
        assert False
    else:
        yield StateAccess(tx_meta.to)

    call_context = CallContext(
        self=tx_meta.to,
        storage=tx_meta.to,
        code=tx_meta.to,
        value=tx_meta.value,
    )

    for entry in trace_entries:
        if entry.op in BENIGN_OPS:
            continue
        elif entry.op in READ_OPS:
            assert False
        elif entry.op in WRITE_OPS:
            assert False
        elif entry.op in CALL_OPS:
            assert False
        else:
            raise ValueError(f"Unsupported opcode: op={entry.op}")


def get_block_access_list(w3: Web3, block_identifier: BlockIdentifier) -> AccessList:
    block_trace = w3.debug_trace.trace_block(block_identifier)
    block = w3.eth.get_block(block_identifier, full_transactions=True)

    tx_metas = tuple(
        TxMeta(
            sender=to_canonical_address(tx['from']),
            to=to_canonical_address(tx['to']),
            value=tx['to'],
            data=tx['input'],
            gas=tx['gas'],
            gas_priice=tx['gasPrice'],
            nonce=tx['nonce'],
        ) for tx in block['transactions']
    )
    access_events_by_tx = tuple(
        get_access_events(tx_meta, tx_trace)
        for tx_meta, tx_trace
        in zip(tx_metas, block_trace['results'])
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
