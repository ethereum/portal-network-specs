from typing import (
    Any,
    Callable,
    Dict,
    List,
    Optional,
    Tuple,
    TypedDict,
)

from eth_utils import (
    to_int,
    to_checksum_address,
)
from eth_typing import (
    BlockNumber,
    Address,
    ChecksumAddress,
    HexStr,
)
from hexbytes import (
    HexBytes,
)

from web3 import Web3
from web3._utils.compat import (
    Protocol,
)
from web3._utils.rpc_abi import (
    RPC,
)
from web3.method import (
    DeprecatedMethod,
    Method,
    default_root_munger,
)
from web3.module import (
    Module,
)
from web3.types import (
    TxParams,
    BlockIdentifier,
)

from web3.types import RPCEndpoint


class RPC:
    debug_traceBlock = RPCEndpoint("debug_traceBlockByNumber")


class AccessListItem(TypedDict):
    address: ChecksumAddress
    storageKeys: Tuple[int, ...]


class AccessList(TypedDict):
    accessList: Tuple[AccessListItem]
    gasUsed: int


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
    returnValue: HexStr
    structLogs: List[RawTraceEntry]


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




def _block_trace_formatter(raw_trace: RawTrace) -> RawTrace:
    return raw_trace


def block_trace_formatter(module: Module, method: RPCEndpoint) -> Callable[[RawTrace], RawTrace]:
    return _block_trace_formatter


debug_traceBlock: Method[Callable[[BlockIdentifier], RawTrace]] = Method(
    RPC.debug_traceBlock,
    mungers=[default_root_munger],
    result_formatters=block_trace_formatter,
)


class DebugTraceModule(Module):
    trace_block = debug_traceBlock


def attach_to_w3(w3: Web3):
    from web3._utils.module import attach_modules

    modules = {
        'debug_trace': (DebugTraceModule,),
    }
    attach_modules(w3, modules)
