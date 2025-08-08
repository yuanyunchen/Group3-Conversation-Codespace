from dataclasses import dataclass


@dataclass
class Item:
	importance: float
	subjects: list[int]
