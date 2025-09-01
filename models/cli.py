import argparse
from dataclasses import dataclass


@dataclass
class Settings:
	players_count: int
	subjects: int
	memory_size: int
	length: int
	seed: int


def settings() -> Settings:
	"""
	Parses command-line arguments and returns a validated Settings object.
	"""
	parser = argparse.ArgumentParser(description='Run a conversation game simulation.')
	parser.add_argument('--players_count', type=int, default=5, help='Number of players.')
	parser.add_argument('--subjects', type=int, default=20, help='Number of subjects.')
	parser.add_argument(
		'--memory_size', type=int, default=10, help="Size of each player's memory bank."
	)
	parser.add_argument(
		'--length', type=int, default=10, help='Number of turns in the conversation.'
	)
	parser.add_argument(
		'--seed', type=int, default=91, help='Seed for the random number generator.'
	)

	args = parser.parse_args()
	return Settings(**vars(args))
