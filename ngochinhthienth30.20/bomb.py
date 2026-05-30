import pygame, os
from settings import *

_BOMB_PATH = os.path.join(os.path.dirname(__file__), "assets", "bomb.png")

class Bomb(pygame.sprite.Sprite):
    _img = None
    def __init__(self, x, y):
        super().__init__()
        if Bomb._img is None:
            try: Bomb._img = pygame.image.load(_BOMB_PATH).convert_alpha()
            except:
                s = pygame.Surface((TILE_SIZE,TILE_SIZE),pygame.SRCALPHA)
                pygame.draw.circle(s,RED,(TILE_SIZE//2,TILE_SIZE//2),TILE_SIZE//2-4)
                Bomb._img = s
        self.image = Bomb._img
        self.rect = self.image.get_rect(topleft=(x,y))
        self.timer = 3*FPS
        self.passable = True
        self.player_has_left = False

    def update(self):
        self.timer -= 1
        if self.timer <= 0: self.kill(); return True
        return False
    def draw(self, surface): surface.blit(self.image, self.rect)

class Explosion(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        T = TILE_SIZE
        self.image = pygame.Surface((T,T), pygame.SRCALPHA)
        pygame.draw.rect(self.image, ORANGE, (0,0,T,T))
        pygame.draw.rect(self.image, (255,255,0), (8,8,T-16,T-16))
        self.rect = self.image.get_rect(topleft=(x,y))
        self.timer = int(0.5*FPS)
    def update(self):
        self.timer -= 1
        if self.timer <= 0: self.kill()