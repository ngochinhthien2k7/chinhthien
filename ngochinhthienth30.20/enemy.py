import pygame, random, os
from settings import *

_ENEMY_PATH = os.path.join(os.path.dirname(__file__), "assets", "enemy.png")

class Enemy(pygame.sprite.Sprite):
    _img = None
    def __init__(self, x, y, tiles):
        super().__init__()
        if Enemy._img is None:
            try: Enemy._img = pygame.image.load(_ENEMY_PATH).convert_alpha()
            except:
                s = pygame.Surface((TILE_SIZE,TILE_SIZE)); s.fill(GREEN)
                Enemy._img = s
        self.image = Enemy._img
        self.rect = self.image.get_rect(topleft=(x*TILE_SIZE, y*TILE_SIZE))
        self.speed = 2
        self.direction = random.randint(0,3)
        self.tiles = tiles
        self.change_timer = 0
        self.change_interval = FPS*2

    def update(self, bombs=None):
        ox, oy = self.rect.x, self.rect.y
        dirs = [(self.speed,0),(-self.speed,0),(0,self.speed),(0,-self.speed)]
        dx, dy = dirs[self.direction % 4] if self.direction < 4 else (0,0)
        # map direction index to delta
        deltas = {0:(self.speed,0),1:(0,-self.speed),2:(0,self.speed),3:(-self.speed,0)}
        dx,dy = deltas[self.direction]
        self.rect.x += dx; self.rect.y += dy
        blocked = any(self.rect.colliderect(t.rect) for t in self.tiles)
        if bombs: blocked = blocked or any(not b.passable and self.rect.colliderect(b.rect) for b in bombs)
        if blocked or self.rect.left<0 or self.rect.right>WIDTH or self.rect.top<0 or self.rect.bottom>11*TILE_SIZE:
            self.rect.x,self.rect.y = ox,oy
            choices = [d for d in range(4) if d!=self.direction]
            self.direction = random.choice(choices)
        self.change_timer += 1
        if self.change_timer >= self.change_interval:
            self.change_timer = 0; self.direction = random.randint(0,3)
