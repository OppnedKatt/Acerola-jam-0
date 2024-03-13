from time import time

import pygame

import asset_handler
from basic_mover import Basic_mover
from entity import Entity


class Frog(Basic_mover):
    def __init__(self, pos: list[int] = None, target: Entity = None, world=None) -> None:
        super().__init__(pos, target, world)
        self.tongue: Tongue = None
        self.spit_dir = (1, 0, 0)
        self.forced_move = None
        self.colour = (30, 250, 50)
    
    def next_move(self) -> tuple[int, int, int]:
        if self.forced_move is not None:
            return self.forced_move
        if not self.target_in_range():
            return (0, 0, 0)
        movement = super().next_move()
        if movement == (0, 0, 0) and self.target is not None:
            dx = self.target.pos[0] - self.pos[0]
            dy = self.target.pos[1] - self.pos[1]
            self.spit_dir = (dx, dy, 0)
            self.forced_move = (0, 0, 0)
            self.last_move = time()
            return (0, 0, 0)
        return movement

    def move(self, dst: tuple[int, int, int] | list[int]):
        if self.tongue is not None:
            return
        if self.forced_move is not None:
            self.tongue = Tongue(self, [a + b for a, b in zip(self.pos, self.spit_dir)], self.spit_dir)
            self.entities.append(self.tongue)
            self.forced_move = None
        return super().move(dst)
    
    def kill(self):
        if self.tongue is not None:
            self.tongue.kill()
        super().kill()
        
class Tongue(Entity):
    textures = [
        asset_handler.get_texture('objects', 'frog', 'tongue_right.png'),
        asset_handler.get_texture('objects', 'frog', 'tongue_down.png'),
        asset_handler.get_texture('objects', 'frog', 'tongue_left.png'),
        asset_handler.get_texture('objects', 'frog', 'tongue_up.png')
    ]
    
    def __init__(self, owner: Frog, pos: list[int], direction: tuple[int, int, int]) -> None:
        super().__init__(owner.world, pos, None, 1, None)
        self.owner = owner
        self.direction = direction
        self.colour = (230, 120, 120)
        self.solid = False
        for entity in (*self.entities, self.player):
            if entity.pos == self.pos:
                entity.damage(1)
        
        #TODO: Calc tex
        # self.tex = 

    def next_move(self) -> tuple[int, int, int]:
        return (0, 0, 0)

    def move(self, dst: tuple[int, int, int] | list[int]):
        self.kill()

    def kill(self):
        self.owner.tongue = None
        super().kill()
    
    def damage(self, damage: int):
        self.owner.damage(damage)

    def get_tex(self) -> pygame.Surface:
        if self.direction == (0, -1, 0):
            return self.textures[1]
        if self.direction == (-1, 0, 0):
            return self.textures[2]
        if self.direction == (0, 1, 0):
            return self.textures[3]
        return self.textures[0]
