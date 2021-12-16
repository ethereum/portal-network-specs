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
    eth_createAccessList = RPCEndpoint("eth_createAccessList")


class RawAccessListItem(TypedDict):
    address: HexStr
    storageKeys: List[HexStr]


class RawAccessList(TypedDict):
    accessList: List[RawAccessListItem]
    gasUsed: HexStr


class AccessListItem(TypedDict):
    address: ChecksumAddress
    storageKeys: Tuple[int, ...]


class AccessList(TypedDict):
    accessList: Tuple[AccessListItem]
    gasUsed: int


def _access_list_formatter(raw_access_list: RawAccessList) -> AccessList:
    return AccessList(
        accessList=tuple(
            AccessListItem(
                address=to_checksum_address(item['address']),
                storageKeys=tuple(to_int(hexstr=storage_key) for storage_key in item['storageKeys']),
            ) for item in raw_access_list['accessList']
        ),
        gasUsed=to_int(hexstr=raw_access_list['gasUsed']),
    )


def access_list_formatter(module: Module, method: RPCEndpoint) -> Callable[[RawAccessList], AccessList]:
    return _access_list_formatter


eth_createAccessList: Method[Callable[[TxParams, Optional[BlockIdentifier]], HexStr]] = Method(
    RPC.eth_createAccessList,
    mungers=[default_root_munger],
    result_formatters=access_list_formatter,
)


class AccessListModule(Module):
    create_access_list = eth_createAccessList


def attach_to_w3(w3: Web3):
    from web3._utils.module import attach_modules

    modules = {
        'access_list': (AccessListModule,),
    }
    attach_modules(w3, modules)
