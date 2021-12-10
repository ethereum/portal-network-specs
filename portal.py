from dataclasses import dataclass, field
from typing import Sequence, Tuple, Union
import itertools
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


UTP_PACKET_MIN_SIZE = 150
UTP_PACKET_MAX_SIZE = 1024


@dataclass(eq=True)
class Meter:
    packets: int = 0
    bytes: int = 0

    def add_packet(self, num_bytes: int) -> None:
        self.packets += 1
        self.bytes += num_bytes


@dataclass(eq=True)
class UDPMeter:
    # number of inbound bytes
    inbound: Meter = field(default_factory=Meter)

    # number of outbound bytes
    outbound: Meter = field(default_factory=Meter)

    def __str__(self) -> str:
        return f"packets={self.num_packets:n}  inbound={humanize_bytes(self.inbound)}  outbound={humanize_bytes(self.outbound)}"


def _compute_utp_transfer(payload_size: int, packet_payload_size: int) -> Tuple[UDPMeter, UDPMeter]:
    initiator = UDPMeter()
    recipient = UDPMeter()

    # SYN to initiate stream
    initiator.outbound.add_packet(20)
    recipient.inbound.add_packet(20)

    # ACK to acknowledge stream setup
    recipient.outbound.add_packet(20)
    initiator.inbound.add_packet(20)

    # Data packets
    total_data_packets = max(1, int(math.ceil(payload_size / packet_payload_size)))

    # 20 bytes of overhead per packet
    initiator.outbound.packets += total_data_packets
    initiator.outbound.bytes += (total_data_packets - 1) * (packet_payload_size + 20)
    initiator.outbound.bytes += payload_size % packet_payload_size + 20

    # acks from the recipient for the data packets
    initiator.inbound.packets += total_data_packets
    initiator.inbound.bytes += total_data_packets * 20

    # receipt of the data packets
    recipient.inbound.packets += total_data_packets
    recipient.inbound.bytes += (total_data_packets - 1) * (packet_payload_size + 20)
    recipient.inbound.bytes += payload_size % packet_payload_size + 20

    # acks sent for data packets
    recipient.outbound.packets += total_data_packets
    recipient.outbound.bytes += total_data_packets * 20

    # FIN to close the stream
    initiator.outbound.add_packet(20)
    recipient.inbound.add_packet(20)

    # ACK to acknowledge the stream is closed
    recipient.outbound.add_packet(20)
    initiator.inbound.add_packet(20)

    return initiator, recipient


def compute_utp_tranfer_worst(payload_size: int) -> Tuple[UDPMeter, UDPMeter]:
    return _compute_utp_transfer(payload_size, UTP_PACKET_MIN_SIZE)


def compute_utp_tranfer_best(payload_size: int) -> Tuple[UDPMeter, UDPMeter]:
    return _compute_utp_transfer(payload_size, UTP_PACKET_MAX_SIZE)


def render_utp_stats_row(payload_name: str, payload_size: int) -> str:
    initiator_w, recipient_w = compute_utp_tranfer_worst(payload_size)
    initiator_b, recipient_b = compute_utp_tranfer_best(payload_size)

    return (
        payload_name,
        f"{initiator_b.inbound.packets:n} - {initiator_w.inbound.packets:n}",
        f"{initiator_b.outbound.packets:n} - {initiator_w.outbound.packets:n}",
        f"{initiator_b.inbound.bytes:n} - {initiator_w.inbound.bytes:n}",
        f"{initiator_b.outbound.bytes:n} - {initiator_w.outbound.bytes:n}",
        f"{recipient_b.inbound.packets:n} - {recipient_w.inbound.packets:n}",
        f"{recipient_b.outbound.packets:n} - {recipient_w.outbound.packets:n}",
        f"{recipient_b.inbound.bytes:n} - {recipient_w.inbound.bytes:n}",
        f"{recipient_b.outbound.bytes:n} - {recipient_w.outbound.bytes:n}",
    )


MINUTE = 60
HOUR = MINUTE * 60
DAY = HOUR * 24
WEEK = DAY * 7
MONTH = int(DAY * 365 / 12)
YEAR = 365 * DAY


BANDWIDTH_TIME_PERIODS = (
    ('minute', MINUTE),
    ('hour', HOUR),
    ('day', DAY),
    ('week', WEEK),
    ('month', MONTH),
    ('year', YEAR),
)


def _render_rates(rates: Sequence[Union[int, float]], seconds_per_period: int) -> str:
    return ' - '.join((
    ))



def render_bandwidth_usage_stats(rates: Sequence[Union[int, float]], periods: Sequence[Tuple[str, int]] = BANDWIDTH_TIME_PERIODS) -> str:
    header = ("Period", "Bandwidth")
    rows = tuple(
        (
            period,
            ' - '.join((
                humanize_bytes(int(bytes_per_second * seconds_per_period))
                for bytes_per_second in rates
            )),
        )
        for period, seconds_per_period in periods
    )
    table = snakemd.generator.Table(header, rows)
    return table.render()


UTP_PAYLOADS = (
    ("Header", 540),
    ("Header+AccumulatorProof", 1254),
)


def render_utp_stats(payloads: Sequence[Tuple[str, int]] = UTP_PAYLOADS) -> str:
    header = ("Payload", "Initiator: packets-in", "I: packets-out", "I: bytes-in", "I: bytes-out", "Recipient: packets-in", "R: packets-out", "R: bytes-in", "R: bytes-out")

    rows = tuple(
        render_utp_stats_row(payload_name, payload_size)
        for payload_name, payload_size in payloads
    )
    table = snakemd.generator.Table(header, rows)
    return table.render()



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


import numpy as np
from web3 import Web3


PERCENTILES = (1, 5, 10, 20, 30, 40, 50, 60, 70, 80, 85, 90, 95, 97, 98, 99, 100)


def analize_block_size_stats(w3: Web3, from_block: int, sample_size: int, percentiles: Sequence[int] = PERCENTILES) -> None:
    sizes = tuple(
        w3.eth.getBlock(block_number)["size"]
        for block_number
        in range(from_block, max(0, from_block - sample_size), -1)
    )
    header = ("Percentile", "Size", "Size-Bytes")
    size_percentiles = tuple(
        np.percentile(sizes, percentile)
        for percentile
        in percentiles
    )
    median = np.median(sizes)
    average = np.average(sizes)
    rows = (
        ("median", humanize_bytes(int(median)), f"{median:n}"),
        ("average", humanize_bytes(int(average)), f"{average:n}"),
    ) + tuple(
        (str(label), humanize_bytes(int(percentile)), f"{percentile:n}")
        for label, percentile
        in zip(percentiles, size_percentiles)
    )
    table = snakemd.generator.Table(header, rows)
    print("#################### BODY SIZES #######################")
    print(table.render())


import rlp
from rlp_sedes import retrieve_receipts_bundle


def analize_receipt_bundle_size_stats(w3: Web3, from_block: int, sample_size: int, percentiles: Sequence[int] = PERCENTILES) -> None:
    sizes = tuple(
        len(rlp.encode(retrieve_receipts_bundle(w3, block_number)))
        for block_number
        in range(from_block, max(0, from_block - sample_size), -1)
    )
    header = ("Percentile", "Size", "Size-Bytes")
    size_percentiles = tuple(
        np.percentile(sizes, percentile)
        for percentile
        in percentiles
    )
    median = np.median(sizes)
    average = np.average(sizes)
    rows = (
        ("median", humanize_bytes(int(median)), f"{median:n}"),
        ("average", humanize_bytes(int(average)), f"{average:n}"),
    ) + tuple(
        (str(label), humanize_bytes(int(percentile)), f"{percentile:n}")
        for label, percentile
        in zip(percentiles, size_percentiles)
    )
    table = snakemd.generator.Table(header, rows)
    print("#################### RECEIPT BUNDLE SIZES #######################")
    print(table.render())


def derive_average_storage_size(num_nodes: int, replication_factor: int, base_storage: int = TB) -> int:
    total_storage = base_storage * replication_factor
    storage_per_node = total_storage // num_nodes
    return storage_per_node


NODE_SIZES = (100, 250, 500, 1000, 5000, 10000, 50000, 100000, 500000, 1000000)
REPLICATION_FACTORS = (5, 10, 20)

def render_average_storage_size_stats(node_sizes: Sequence[int] = NODE_SIZES, replication_factors: Sequence[int] = REPLICATION_FACTORS) -> str:
    header = ("nodes / replication", "storage")
    rows = tuple(
        (f"{num_nodes} / {replication}", humanize_bytes(derive_average_storage_size(num_nodes, replication)))
        for num_nodes, replication
        in itertools.product(NODE_SIZES, REPLICATION_FACTORS)
    )
    table = snakemd.generator.Table(header, rows)
    return table.render()


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


def do_rendering():
    locale.setlocale(locale.LC_ALL, '')
    routing_table_stats = render_routing_table_stats()
    accumulator_stats = render_accumulator_stats()
    utp_stats = render_utp_stats()
    print("\n############## ROUTING TABLE #####################\n\n")
    print(routing_table_stats)
    print("\n############## ACCUMULATOR #####################\n\n")
    print(accumulator_stats)
    print("\n############## UTP #####################\n\n")
    print(utp_stats)
    print("\n############## Header Gossip #####################\n\n")
    print("Inbound (worst)")
    print(render_bandwidth_usage_stats(((1168 / 13), (2448 / 13))))
    print("Outbound (worst)")
    print(render_bandwidth_usage_stats(((11568 / 13), (12686 / 13))))
    print("Inbound (average)")
    print(render_bandwidth_usage_stats(((748 / 13), (908 / 13))))
    print("Outbound (average)")
    print(render_bandwidth_usage_stats(((2230 / 13), (2370 / 13))))
    print("#################### STORAGE REQUIREMENTS #######################")
    print(render_average_storage_size_stats())
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


@pytest.mark.parametrize(
    'payload_size,packet_data_size,initiator_expected,recipient_expected',
    (
        (100, 1000, UDPMeter(Meter(3, 60), Meter(3, 160)), UDPMeter(Meter(3, 160), Meter(3, 60))),
    ),
)
def test_utp_stream_projections(payload_size, packet_data_size, initiator_expected, recipient_expected):
    initiator_actual, recipient_actual = _compute_utp_transfer(payload_size, packet_data_size)
    assert initiator_actual == initiator_expected
    assert recipient_actual == recipient_expected
