ACCUMULATOR_EPOCH_SIZE = 8192  # 2**13
MAX_HISTORICAL_EPOCHS = 1048576  # 2**20


from remerkleable.complex import Container, List
from remerkleable.byte_arrays import Bytes32
from remerkleable.basic import uint256


class HeaderMeta(Container):
    hash: Bytes32
    difficulty: uint256

EpochAccumulator = List[HeaderMeta, ACCUMULATOR_EPOCH_SIZE]
AccumulatorHistory = List[Bytes32, MAX_HISTORICAL_EPOCHS]

class Accumulator(Container):
    history: AccumulatorHistory
    epoch: EpochAccumulator
