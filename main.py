from core.engine import Engine
from players.random_player import RandomPlayer

# Engine
#
# [Players]
#
# Game loop


def main():
	engine = Engine(players=4, memory_size=10, conversation_length=10, subjects=5)

	for snapshot in engine.snapshots:
		player = RandomPlayer(snapshot=snapshot, conversation_length=engine.conversation_length)
		print(player)


if __name__ == '__main__':
	main()
