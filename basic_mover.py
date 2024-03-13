from math import copysign

from entity import Entity


class Basic_mover(Entity):
    def __init__(self, pos: list[int] = None, target: Entity = None, world = None) -> None:
        super().__init__(world, pos, target)

    def next_move(self) -> tuple[int, int, int]:
        if self.target is None:
            return (0, 0, 0)
        if self.target.pos == self.pos:
            return (-1, 0, 0)
        dx = self.target.pos[0] - self.pos[0]
        dy = self.target.pos[1] - self.pos[1]
        
        if (dx == 0 and abs(dy) == 1) or (abs(dx) == 1 and dy == 0):
            return (0, 0, 0)

        if abs(dx) <= abs(dy):
            return (0, copysign(1, dy), 0)
        return (copysign(1, dx), 0, 0)
