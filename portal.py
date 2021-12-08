from dataclasses import dataclass
from typing import Sequence, Tuple
import math


def get_bucket_size(total_network_size: int, bucket_idx: int) -> int:
    return min(16, int(total_network_size / 2**bucket_idx))

def get_routing_table_size(total_network_size: int) -> int:
    return sum(
        get_bucket_size(total_network_size, bucket_idx)
        for bucket_idx in range(1, 256)
    )


import locale

import snakemd

KB = 1024
MB = KB * 1024
GB = MB * 1024
TB = GB * 1024


def humanize_bytes(num_bytes: int) -> str:
    if num_bytes > TB:
        return f"{num_bytes / TB:0.1f}TB"
    elif num_bytes > GB:
        return f"{num_bytes / GB:0.1f}GB"
    elif num_bytes > MB:
        return f"{num_bytes / MB:0.1f}MB"
    elif num_bytes > KB:
        return f"{num_bytes / KB:0.1f}KB"
    else:
        return f"{num_bytes:n}B"


NETWORK_SIZES = (1000, 10000, 20000, 50000, 100000, 500000, 1000000)


def render_routing_table_stats(network_sizes: Sequence[int] = NETWORK_SIZES) -> str:
    """
    Render the markdown table with expected size of the routing table for
    different network sizes.
    """
    header = ("Network Size", "Routing Table Size", "Log2")
    rows = tuple(
        (f"{network_size:n}", f"{get_routing_table_size(network_size):n}", f"{math.log2(get_routing_table_size(network_size)):n}")
        for network_size in network_sizes
    )
    table = snakemd.generator.Table(header, rows)
    return table.render()


from accumulator import ACCUMULATOR_EPOCH_SIZE, MAX_HISTORICAL_EPOCHS


BLOCK_HEIGHTS = (100000, 1000000, 10000000, 15000000, 30000000)


def render_accumulator_stats(block_heights: Sequence[int] = BLOCK_HEIGHTS, epoch_size: int = ACCUMULATOR_EPOCH_SIZE) -> str:
    header = ("Block Number", "Accumulator History Size", "Accumulator Max Size")
    full_epoch_size = epoch_size * 64
    base_sizes = tuple(32 * block_number // epoch_size for block_number in block_heights)
    rows = tuple(
        (f"{block_number:n}", f"{humanize_bytes(base_size)}", f"{humanize_bytes(base_size + full_epoch_size)}")
        for block_number, base_size
        in zip(block_heights, base_sizes)
    )
    table = snakemd.generator.Table(header, rows)
    return table.render()


@dataclass
class StorageProfile:
    growth_bytes_per_block: int


"""
+-----------------+--------------------+------------+------------+
|    DATABASE     |      CATEGORY      |    SIZE    |   ITEMS    |
+-----------------+--------------------+------------+------------+
| Key-Value store | Headers            | 52.23 MiB  |      94400 |
| Key-Value store | Bodies             | 6.20 GiB   |      94400 |
| Key-Value store | Receipt lists      | 4.87 GiB   |      94400 |
| Key-Value store | Difficulties       | 7.69 MiB   |     113640 |
| Key-Value store | Block number->hash | 6.51 MiB   |     109104 |
| Key-Value store | Block hash->number | 537.96 MiB |   13758336 |
| Key-Value store | Transaction index  | 43.82 GiB  | 1306888848 |
| Key-Value store | Bloombit index     | 2.41 GiB   |    6878494 |
| Key-Value store | Contract codes     | 2.63 GiB   |     473682 |
| Key-Value store | Trie nodes         | 187.73 GiB | 1258886228 |
| Key-Value store | Trie preimages     | 547.13 KiB |       8893 |
| Key-Value store | Account snapshot   | 7.09 GiB   |  156232303 |
| Key-Value store | Storage snapshot   | 41.46 GiB  |  580708609 |
| Key-Value store | Clique snapshots   | 0.00 B     |          0 |
| Key-Value store | Singleton metadata | 8.11 MiB   |         13 |
| Ancient store   | Headers            | 6.02 GiB   |   13663937 |
| Ancient store   | Bodies             | 176.86 GiB |   13663937 |
| Ancient store   | Receipt lists      | 87.64 GiB  |   13663937 |
| Ancient store   | Difficulties       | 214.53 MiB |   13663937 |
| Ancient store   | Block number->hash | 495.18 MiB |   13663937 |
| Light client    | CHT trie nodes     | 0.00 B     |          0 |
| Light client    | Bloom trie nodes   | 0.00 B     |          0 |
+-----------------+--------------------+------------+------------+
|                         TOTAL        | 568.01 GIB |            |
+-----------------+--------------------+------------+------------+
"""


def get_header_gossip_network_storage_range() -> Tuple[int, int]:
    ...

def get_average_storage_requirements(network_sizes: Sequence[int]) -> str:
    header_gossip_bounds = get_header_gossip_network_storage_range()


def do_rendering():
    locale.setlocale(locale.LC_ALL, '')
    routing_table_stats = render_routing_table_stats()
    accumulator_stats = render_accumulator_stats()
    print("\n############## ROUTING TABLE #####################\n\n")
    print(routing_table_stats)
    print("\n############## ACCUMULATOR #####################\n\n")
    print(accumulator_stats)
    print("\n****************** FIN ***************************\n")


if __name__ == '__main__':
    do_rendering()


import pytest


@pytest.mark.parametrize(
    'total_network_size,bucket_idx,expected',
    (
        (16, 1, 8),
        (16, 2, 4),
        (16, 3, 2),
        (16, 4, 1),
        (16, 5, 0),
    ),
)
def test_get_bucket_size(total_network_size, bucket_idx, expected):
    actual = get_bucket_size(total_network_size, bucket_idx)
    assert actual == expected


@pytest.mark.parametrize(
    'num_bytes,expected',
    (
        (0, "0B"),
    ),
)
def test_humanize_bytes(num_bytes, expected):
    actual = humanize_bytes(num_bytes)
    assert actual == expected
