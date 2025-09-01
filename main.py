from typing import Type

from core.engine import Engine
from models.cli import settings
from models.player import Player
from players.random_player import RandomPlayer


def main():
	args = settings()
	players: list[Type[Player]] = [RandomPlayer] * args.players_count

	engine = Engine(
		players=players,
		player_count=args.players_count,
		subjects=args.subjects,
		memory_size=args.memory_size,
		conversation_length=args.length,
		seed=args.seed,
	)

	print('Initializing players...')
	print('Running conversation simulation...')

	history, scores = engine.run(players)

	print('\n--- Game Simulation Complete ---')
	print(f'Conversation Length: {len(history)} turns\n')

	print('--- Final Scores ---')
	for uid, score in scores.items():
		print(f'Player {str(uid)[:8]}: {score:.2f}')

	print('\n--- Conversation History ---')
	for i, item in enumerate(history):
		if item:
			print(
				f'Turn {i}: Item ID {str(item.id)[:8]} - Subjects {item.subjects} - Importance {item.importance}'
			)
		else:
			print(f'Turn {i}: No item proposed (Pause)')


if __name__ == '__main__':
	main()
