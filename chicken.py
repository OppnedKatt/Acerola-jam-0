from math import floor
from time import time

import pygame

import asset_handler
from animal import Animal
from entity import Entity


class Chicken(Animal):
    textures = [
        asset_handler.get_texture('objects', 'chicken', 'right.png'),
        asset_handler.get_texture('objects', 'chicken', 'left.png')
    ]
      
    def __init__(self, pos: list[int], world=None) -> None:
        super().__init__(world, pos, health=2)
        self.colour = (230, 230, 230)
        self.run_away_speed = 0.2
        self.run_away_length = 40
        self.has_egg = True

    def damage(self, damage: int):
        if self.has_egg:
            self.entities.append(Egg(self.pos.copy(), self.world))
            self.has_egg = False
        super().damage(damage)
    
    def get_tex(self) -> pygame.Surface:
        if self.next_move()[0] < 0:
            return self.textures[1]
        return self.textures[0]

class Egg(Entity):
    textures = [
        asset_handler.get_texture('objects', 'chicken', 'egg.png'),
        asset_handler.get_texture('objects', 'chicken', 'stage1.png'),
        asset_handler.get_texture('objects', 'chicken', 'stage2.png'),
        asset_handler.get_texture('objects', 'chicken', 'stage3.png'),
    ]
    
    def __init__(self, pos: list[int], world=None) -> None:
        super().__init__(world, pos, move_speed=15, health=3)

    def move(self, *_):
        self.entities.append(Chicken(self.pos.copy(), self.world))
        super().kill()
    
    def next_move(self):
        return (0, 0, 0)

    def get_tex(self):
        slot = max(0, min(3, floor((time() - self.last_move) / self.move_speed * 4)))
        return self.textures[slot]
