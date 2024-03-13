from random import randint
from time import time

from entity import Entity


class Animal(Entity):
    def __init__(self, world=None, pos: list[int] = None, target=None, health: int = 4) -> None:
        super().__init__(world, pos, target, 3, health)
        self.move_speed = 0.8
        self.run_away_speed = 0.3
        self.run_away_length = 20
        self.moves = randint(4, 9)
        self.last_move = time() + randint(5, 13)
        self.damaged = False
        self.next = None
        self.healing = 1

    def damage(self, damage: int):
        self.last_move = -1
        self.moves = self.run_away_length
        self.move_speed = self.run_away_speed
        self.damaged = True
        super().damage(damage)

    def kill(self):
        self.player.heal(self.healing)
        return super().kill()

    def move(self, dst: tuple[int, int, int] | list[int]):
        super().move(dst)
        self.moves -= 1
        self.next = None
        if not self.damaged:
            self.move_speed = randint(7, 12) / 10
        if self.moves <= 0:
            if self.damaged:
                self.move_speed = 0.8
                self.damaged = False
            self.moves = randint(4, 9)
            self.last_move = time() + randint(6, 13)

    def next_move(self):
        if self.next is not None:
            return self.next
        self.next = (randint(-1, 1), randint(-1, 1), 0)
        return self.next
