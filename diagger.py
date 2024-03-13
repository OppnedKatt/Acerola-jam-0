from math import floor
from time import time

import pygame

import asset_handler
from diagonal_mover import Diagonal_mover


class Diagger(Diagonal_mover):
    textures = [
        asset_handler.get_texture('objects', 'diagger', 'tr.png'),
        asset_handler.get_texture('objects', 'diagger', 'br.png'),
        asset_handler.get_texture('objects', 'diagger', 'bl.png'),
        asset_handler.get_texture('objects', 'diagger', 'tl.png'),
        asset_handler.get_texture('objects', 'diagger', 'none.png')
    ]
    
    def __init__(self, pos: list[int] = None, target=None, world=None) -> None:
        super().__init__(world, pos, target, 0.6)
        self.colour = (120, 120, 120)
        self.charging = False
        self.charge_time = 3
        self.flying = False
        self.fly_direction = (0, 0, 0)
        self.on_cooldown = False

    def illegal_pos(self, pos: tuple[int, int, int] | list[int]) -> bool:
        if not self.awake and tuple(pos[:2]) not in self.world.seen_blocks:
            return True
        return tuple(pos[:2]) in self.world.solids.get(pos[2], [])

    def next_move(self) -> tuple[int, int, int]:
        if self.on_cooldown and time() > self.real_last_move:
            self.on_cooldown = False
        if self.flying:
            return self.fly_direction
        if not self.charging and not self.flying and not self.on_cooldown and self.on_line():
            self.charging = True
            self.real_last_move = time() + self.charge_time
            self.fly_direction = super().next_move()
        elif self.charging and not self.on_line():
            self.charging = False
            self.real_last_move = time()
        return super().next_move()

    def move(self, dst: tuple[int, int, int] | list[int]):
        if self.on_cooldown:
            return
        if self.charging and self.on_line():
            self.flying = True
            self.charging = False
            self.move_speed = 0.1
        if self.flying and self.illegal_pos(self.if_moved(dst)):
            self.flying = False
            self.move_speed = self.default_move_speed
            self.real_last_move = time() + 2
            self.on_cooldown = True
            return
        super().move(dst)
        force = list(dst)
        force[0] *= 2
        force[1] *= 2
        hit = False
        for entity in (*self.entities, self.player):
            if entity.pos != self.pos or self is entity:
                continue
            if entity.health is not None:
                entity.damage(4)
            if entity.solid:
                entity.move(dst if entity.illegal_pos(entity.if_moved(force)) else force)
            hit = True
        if hit:
            self.flying = False
            self.move_speed = self.default_move_speed
            self.real_last_move = time() + 4
            self.on_cooldown = True

    def get_tex(self) -> pygame.Surface:
        movement = self.next_move()
        if self.on_cooldown:
            # movement = self.fly_direction
            movement = (0, 0, 0)
        
        if movement == (1, 1, 0):
            tex = self.textures[0]
        elif movement == (1, -1, 0):
            tex = self.textures[1]
        elif movement == (-1, -1, 0):
            tex = self.textures[2]
        elif movement == (-1, 1, 0):
            tex = self.textures[3]
        else:
            # tex = self.textures[floor(time()*3) % 4]
            tex = self.textures[4]
        
        if self.charging:
            grad = min(80, max(0, 80 * max(0, 1 - (self.real_last_move - time()) / self.charge_time)**1.5))
            tex = tex.copy()
            grad_surf = pygame.Surface(tex.get_size()).convert_alpha()
            grad_surf.fill((grad, 0, 0, 255))
            tex.blit(grad_surf, (0, 0), special_flags=pygame.BLEND_ADD)
        
        return tex
