from math import copysign

import asset_handler
from entity import Entity
from ranger import Ranger


class Spitwar(Ranger):
    def __init__(self, pos: list[int], target: Entity, world = None) -> None:
        self.default_wanted_distance = 6
        super().__init__(world, pos, target, self.default_wanted_distance)
        self.fireball = None
        self.colour = (40, 120, 10)  #DEBUG
        self.move_speed = 0.6
        # self.lo = 1  #DEBUG
        
    def move(self, dst: tuple[int, int, int] | list[int]):
        if tuple(dst) == (0, 0, 0) and self.fireball is None and self.target_in_range():
            print(self.fireball, self.real_last_move)
            fire_move = (
                1 if self.pos[0] - self.target.pos[0] else 0,
                1 if self.pos[1] - self.target.pos[1] else 0,
                0
            )
            fire_move = [copysign(d, -1 if t < s else 1) for d, t, s in zip(fire_move, self.target.pos, self.pos)]
            self.fireball = Fireball(self, self.world, self.pos, fire_move)
            self.move_speed = 0.4
            self.entities.append(self.fireball)
            self.wanted_distance = self.default_wanted_distance + 2
            self.fireball.move(self.fireball.next_move())
            dst = fire_move.copy()
            dst[0] *= -1
            dst[1] *= -1
            return super().move(dst)

        super().move(dst)


class Fireball(Entity):
    textures = [
        asset_handler.get_texture('objects', 'fireball', 'right.png'),
        asset_handler.get_texture('objects', 'fireball', 'down.png'),
        asset_handler.get_texture('objects', 'fireball', 'left.png'),
        asset_handler.get_texture('objects', 'fireball', 'up.png')
    ]
    
    def __init__(
        self,
        owner: Spitwar = None,
        world=None,
        pos: list[int] = None,
        dir: tuple[int, int, int] | tuple[int] = (0, -1, 0)
    ) -> None:
        super().__init__(world, pos, move_speed = 0.15, health = None)
        self.dir = dir
        if owner is not None:
            self.life = 2*owner.wanted_distance - 1
        else:
            self.life = 10
        self.owner = owner
        self.solid = False
        self.force = 2
        self.insta_kill = False
        # self.lo = 1  #DEBUG

    def next_move(self) -> tuple[int, int, int]:
        return self.dir

    def move(self, dst: tuple[int, int, int] | list[int]):
        self.life -= 1
        if self.life <= 0:
            self.kill()

        if self.illegal_pos(self.if_moved(dst)):
            self.kill()
        super().move(dst)
        
        for entity in (*self.entities, self.player):
            if entity.pos == self.pos and entity != self.owner and not isinstance(entity, Fireball):
                self.kill()
                if self.insta_kill:
                    entity.damage(entity.health)
                else:
                    entity.damage(self.force)

    def illegal_pos(self, pos: tuple[int, int, int] | list[int]) -> bool:
        if not self.awake and tuple(pos[:2]) not in self.world.seen_blocks:
            return True
        return tuple(pos[:2]) in self.world.solids.get(pos[2], [])

    def kill(self):
        if self.owner is not None:
            self.owner.fireball = None
            self.owner.wanted_distance = self.owner.default_wanted_distance
            self.owner.move_speed = self.owner.default_move_speed
        super().kill()
    
    def get_tex(self):
        if self.dir[0] == -1:
            return self.textures[2]
        if self.dir[0] == 1:
            return self.textures[0]
        if self.dir[1] == -1:
            return self.textures[1]
        if self.dir[1] == 1:
            return self.textures[3]
        return super().get_tex()
