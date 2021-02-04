from typing import Iterable

def crc16(*datas: Iterable[int], initial: int = 0) -> int:
    csum = initial
    for data in datas:
        for datum in data:
            csum ^= datum << 8
            for _ in range(8):
                if csum & 0x8000:
                    csum = (csum << 1) ^ 0x1021
                else:
                    csum <<= 1
    return csum
