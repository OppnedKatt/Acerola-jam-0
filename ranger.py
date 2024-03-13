from math import copysign

from entity import Entity


class Ranger(Entity):
    def __init__(self, world = None, pos: list[int] = None, target: Entity = None, wanted_distance: int = 4) -> None:
        super().__init__(world, pos, target)
        self.wanted_distance = wanted_distance

    def next_move(self) -> tuple[int, int, int]:
        if self.target is None or not self.target_in_range():
            return (0, 0, 0)
        hor = abs(self.target.pos[0] - self.pos[0])
        ver = abs(self.target.pos[1] - self.pos[1])
        move_ver = bool(sum(self.pos) % 2)
        movement = [0, 0, 0]
        last = False

        if self.wanted_distance in (ver, hor) and (not hor or not ver):
            movement = (0, 0, 0)

        elif not hor and not ver:
            movement = (
                -1 if self.pos[0] % 2 else 1,
                1 if self.pos[1] % 2 else -1,
                0
            )
        elif not hor or not ver:
            move_ver = not hor
            sign = 1 if self.pos[move_ver] < self.target.pos[move_ver] else -1
            movement[move_ver] = copysign(1, abs(self.pos[move_ver] - self.target.pos[move_ver]) - self.wanted_distance) * sign

        elif hor <= ver:
            move_ver = False
            last = True
        elif ver < hor:
            move_ver = True
            last = True
        if last:
            sign = 1 if self.pos[move_ver] < self.target.pos[move_ver] else -1
            movement[move_ver] = sign
        
        if self.illegal_pos([a + b for a, b in zip(self.pos, movement)]):
            if not hor or not ver:
                return (0, 0, 0)
            movement[0], movement[1] = movement[1], movement[0]
            if not self.illegal_pos([a + b for a, b in zip(self.pos, movement)]):
                return movement
            movement[0] *= -1
            movement[1] *= -1
            if not self.illegal_pos([a + b for a, b in zip(self.pos, movement)]):
                return movement
            movement[0], movement[1] = movement[1], movement[0]
            
        return movement
