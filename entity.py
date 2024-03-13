from random import randint
from time import time

import pygame


class Entity:
    entities = []
    normal_entities = entities
    other_world_entities = []
    dream_entities = other_world_entities
    spawned_entities = []
    default_world = None
    player = None
    other_world_player = None
    awake = True
    
    def __init__(
        self,
        world = None,
        pos: list[int] = None,
        target = None,
        move_speed: int | float = 1,
        health: int = 8
    ) -> None:
        self.alive = True
        if pos is None:
            self.pos = [0, 0, 1]
        else:
            self.pos = pos
        self.origin = self.pos
        self.inter_offset = [0, 0, 0]
        self.walking = False
        self.last_move = time()
        self.real_last_move = self.last_move
        self.move_speed = move_speed
        self.default_move_speed = move_speed
        self.solid = True
        self.step_time = 0.02
        self.view_distance = 16
        
        if world is None:
            if self.default_world is None:
                raise Exception('No world is set!')
            self.world = self.default_world
        else:
            self.world = world
        self.target = target
        
        self.max_health = health
        self.health = health
        
        self.colour = (randint(0, 255), randint(0, 255), randint(0, 255))  #DEBUG
        
    def illegal_pos(self, pos: tuple[int, int, int] | list[int]) -> bool:
        if not self.awake and tuple(pos[:2]) not in self.world.seen_blocks:
            return True
        solids = tuple(pos[:2]) in self.world.solids.get(pos[2], [])
        if solids:
            return True
        ent = any((entity.pos == list(pos) and entity.solid for entity in (*self.entities, self.player) if entity is not self))
        if ent:
            return True
        if self.target == None:
            return False
        return list(pos) == self.target.pos

    def move(self, dst: tuple[int, int, int] | list[int]):
        pos = [a + b for a, b in zip(self.pos, dst)]
        self.last_move = time()
        self.real_last_move = self.last_move
        if self.illegal_pos(pos):
            return
        self.inter_offset = [a + b/2 for a, b in zip(self.pos, dst)]
        self.pos = pos
        self.walking = True
    
    def kill(self):
        if not self.alive:
            return
        self.alive = False
        if self in self.entities:
            self.entities.remove(self)
    
    def damage(self, damage: int):
        if self.health is None:
            return
        self.health -= damage
        if self.health <= 0:
            self.kill()
    
    def get_tex(self) -> pygame.Surface:
        surf = pygame.Surface((1, 1))
        surf.fill(self.colour)
        return surf
    
    def target_in_range(self) -> bool:
        if self.target is None:
            return False
        return self.view_distance**2 > (self.pos[0] - self.target.pos[0])**2 + (self.pos[1] - self.target.pos[1])**2

    def if_moved(self, dst: tuple[int, int, int] | list[int]) -> list[int]:
        return [a + b for a, b in zip(self.pos, dst)]

    @classmethod
    def propagate_movement(cls, awake: bool = True):
        # lol = False  #DEBUG
        for entity in cls.entities:
            if not hasattr(entity, 'next_move') or (not awake and tuple(entity.pos[:2]) not in entity.world.seen_blocks):
                continue
            next_move = entity.next_move()
            if time() - entity.real_last_move < entity.move_speed:
                continue
            entity.move(next_move)
        #     if hasattr(entity, 'lo'):  #DEBUG
        #         lol = True
        # if lol:
        #     print('-----')
