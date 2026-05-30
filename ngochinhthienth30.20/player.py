import pygame, os
from settings import *
from bomb import Bomb

_IMG_PATH = os.path.join(os.path.dirname(__file__), "assets", "player.png")
CORNER = 10   # pixel threshold để tự trượt qua góc

class Player(pygame.sprite.Sprite):
    _img = None
    def __init__(self):
        super().__init__()
        if Player._img is None:
            try: Player._img = pygame.image.load(_IMG_PATH).convert_alpha()
            except:
                s = pygame.Surface((TILE_SIZE,TILE_SIZE),pygame.SRCALPHA); s.fill(WHITE)
                Player._img = s
        self.image = Player._img
        self.rect = self.image.get_rect(topleft=(TILE_SIZE, TILE_SIZE))
        self.speed = 3
        self.max_bombs = 3

    def update(self, tiles, bombs=None):
        keys = pygame.key.get_pressed()
        dx = (keys[pygame.K_RIGHT] - keys[pygame.K_LEFT]) * self.speed
        dy = (keys[pygame.K_DOWN]  - keys[pygame.K_UP])   * self.speed
        self.rect.x += dx; self._collide(dx, 0, tiles, bombs)
        self.rect.y += dy; self._collide(0, dy, tiles, bombs)
        if bombs:
            for b in bombs:
                if not self.rect.colliderect(b.rect):
                    b.player_has_left = True; b.passable = False
        self.rect.clamp_ip(pygame.Rect(0, 0, WIDTH, 11*TILE_SIZE))

    def _collide(self, dx, dy, tiles, bombs):
        obstacles = list(tiles) + ([b for b in bombs if not b.passable] if bombs else [])
        for obj in obstacles:
            if not self.rect.colliderect(obj.rect):
                continue
            r = obj.rect

            if dx > 0:
                # đang đi phải — thử corner correction lên/xuống
                ov_top    = self.rect.bottom - r.top
                ov_bottom = r.bottom - self.rect.top
                if 0 < ov_top <= CORNER:
                    self.rect.bottom = r.top        # trượt lên
                elif 0 < ov_bottom <= CORNER:
                    self.rect.top = r.bottom        # trượt xuống
                else:
                    self.rect.right = r.left

            elif dx < 0:
                ov_top    = self.rect.bottom - r.top
                ov_bottom = r.bottom - self.rect.top
                if 0 < ov_top <= CORNER:
                    self.rect.bottom = r.top
                elif 0 < ov_bottom <= CORNER:
                    self.rect.top = r.bottom
                else:
                    self.rect.left = r.right

            elif dy > 0:
                # đang đi xuống — thử corner correction trái/phải
                ov_left  = self.rect.right - r.left
                ov_right = r.right - self.rect.left
                if 0 < ov_left <= CORNER:
                    self.rect.right = r.left
                elif 0 < ov_right <= CORNER:
                    self.rect.left = r.right
                else:
                    self.rect.bottom = r.top

            elif dy < 0:
                ov_left  = self.rect.right - r.left
                ov_right = r.right - self.rect.left
                if 0 < ov_left <= CORNER:
                    self.rect.right = r.left
                elif 0 < ov_right <= CORNER:
                    self.rect.left = r.right
                else:
                    self.rect.top = r.bottom

    def drop_bomb(self):
        return Bomb((self.rect.centerx//TILE_SIZE)*TILE_SIZE,
                    (self.rect.centery//TILE_SIZE)*TILE_SIZE)
    def draw(self, surface): surface.blit(self.image, self.rect)