import pygame

from entity import Entity


class Player(Entity):
    go_to_dream = None
    return_from_dream = None
    
    def __init__(self, world = None, pos: list[int] = None) -> None:
        super().__init__(world, pos, move_speed=0.2)
        self.heart_drawer = None
        self.dreamer = False
        
    def damage(self, damage: int):
        super().damage(damage)
        if not self.heart_drawer is None:
            self.heart_drawer()

    def heal(self, hp: int):
        self.health = min(self.max_health, self.health + hp)
        if not self.heart_drawer is None:
            self.heart_drawer()
        
    def kill(self):
        if not self.dreamer:
            self.health = 1
            self.go_to_dream()
            return
    
    def get_tex(self) -> pygame.Surface:
        surf = pygame.Surface((8, 8)).convert_alpha()
        surf.fill(self.colour)
        surf.fill((0, 0, 0, 0))
        pygame.draw.rect(
            surf, self.colour,
            pygame.Rect(1, 1, 6, 6)
        )
        return surf
