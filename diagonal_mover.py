from math import copysign

from entity import Entity


class Diagonal_mover(Entity):
    def __init__(self, world=None, pos: list[int] = None, target=None, move_speed: int | float = 1, health: int = 8) -> None:
        super().__init__(world, pos, target, move_speed, health)
        
    def on_line(self):
        if self.target is None:
            return False
        x = self.pos[0] - self.target.pos[0]
        y = self.pos[1] - self.target.pos[1]
        return abs(x) == abs(y)

    def next_move(self) -> tuple[int, int, int]:
        if self.target is None:
            return (0, 0, 0)
        if sum(self.pos) % 2 != sum(self.target.pos) % 2:
            # print(sum(self.pos), sum(self.target.pos) % 2)
            return (0, 0, 0)
        if self.pos == self.target.pos:
            if self.illegal_pos(self.if_moved((1, 1, 0))):
                return (1, 1, 0)
            if self.illegal_pos(self.if_moved((1, -1, 0))):
                return (1, -1, 0)
            if self.illegal_pos(self.if_moved((-1, 1, 0))):
                return (-1, 1, 0)
            if self.illegal_pos(self.if_moved((-1, -1, 0))):
                return (-1, -1, 0)
        dx = self.target.pos[0] - self.pos[0]
        dy = self.target.pos[1] - self.pos[1]
        if self.on_line():
            return (copysign(1, dx), copysign(1, dy), 0)
        return (
            copysign(1, dx) * (1 if abs(dx) > abs(dy) else -1),
            copysign(1, dy) * (1 if abs(dy) > abs(dx) else -1),
            0
        )
