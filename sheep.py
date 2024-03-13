import pygame

import asset_handler
from animal import Animal


class Sheep(Animal):
    textures = [
        asset_handler.get_texture('objects', 'sheep', 'right.png'),
        asset_handler.get_texture('objects', 'sheep', 'left.png')
    ]
    
    def __init__(self, pos: list[int], world=None) -> None:
        super().__init__(world, pos, health=4)
        self.colour = (250, 250, 250)
        self.run_away_speed = 0.4
        self.healing = 2

    def get_tex(self) -> pygame.Surface:
        if self.next_move()[0] < 0:
            return self.textures[1]
        return self.textures[0]
