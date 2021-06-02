from typing import Iterable

def crc16(*datas: Iterable[int], initial: int = 0) -> int:
    """Computes a CRC-16 checksum over a series of bytes.

    Parameters
    ----------
    datas : Iterable[int]
        A list of data sources, each of which produces a series of bytes.
    initial : int, optional
        The initial CRC sum to start computing from. Can be used to chain CRC sums together.

    Returns
    -------
    int
        The CRC-16 checksum of the input bytes.
    """
    csum = initial & 0xFFFF
    for data in datas:
        for datum in data:
            csum ^= (datum << 8) & 0xFFFF
            for _ in range(8):
                if csum & 0x8000:
                    csum = ((csum << 1) & 0xFFFF) ^ 0x1021
                else:
                    csum = (csum << 1) & 0xFFFF
    return csum
