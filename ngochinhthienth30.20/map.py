import pygame, math, random
from settings import *

MAP_DATA = [
    [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
    [1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1],
    [1,0,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,0,1],
    [1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1],
    [1,0,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,0,1],
    [1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1],
    [1,0,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,0,1],
    [1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1],
    [1,0,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,0,1],
    [1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1],
    [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
]
MAP_ROWS = len(MAP_DATA)

_rng = random.Random(42)
_cc = lambda r,g,b: (max(0,min(255,int(r))), max(0,min(255,int(g))), max(0,min(255,int(b))))
_lc = lambda a,b,t: _cc(a[0]+(b[0]-a[0])*t, a[1]+(b[1]-a[1])*t, a[2]+(b[2]-a[2])*t)
def _surf(T): return pygame.Surface((T,T), pygame.SRCALPHA)
def _aline(s,c,a,p1,p2,w=1): pygame.draw.line(s, (*c,a), p1, p2, w)

def _make_solid(T=TILE_SIZE):
    s = _surf(T)
    for y in range(T): pygame.draw.line(s, _lc((72,78,95),(38,42,55),y/T), (0,y),(T,y))
    M, h = (22,25,33), T//2
    for y in (0, h-1, T-2): pygame.draw.rect(s, M, (0,y,T,2))
    for r in range(2):
        for x in range(0, T+h, h):
            bx = x - T//4 + (T//4 if r else 0)
            if 0 < bx < T: pygame.draw.rect(s, M, (bx, r*h, 2, h))
    for r in range(2):
        oy, bh = r*h+2, h-4
        for bx in range(0, T, h):
            for _ in range(5):
                px = _rng.randint(max(0,bx+2), min(T-1,bx+h-3))
                py = _rng.randint(oy, max(oy,oy+bh-1)) if bh>0 else oy
                n = _rng.randint(-12,12); c = s.get_at((px,py))
                s.set_at((px,py), _cc(c[0]+n, c[1]+n, c[2]+n))
    hl = _surf(T)
    _aline(hl,(140,150,170),100,(0,0),(T,0)); _aline(hl,(120,130,155),70,(0,0),(0,T))
    for i in range(4): _aline(hl,(120,130,155),80-i*18,(i,0),(0,i))
    sh = _surf(T)
    _aline(sh,(0,0,0),90,(0,T-1),(T,T-1)); _aline(sh,(0,0,0),70,(T-1,0),(T-1,T))
    s.blit(hl,(0,0)); s.blit(sh,(0,0))
    return s

def _make_breakable(T=TILE_SIZE):
    s = _surf(T)
    for y in range(T): pygame.draw.line(s, _lc((185,115,45),(145,82,22),y/T), (0,y),(T,y))
    gs = _surf(T)
    for gx in range(0,T,5):
        w = int(math.sin(gx*.6)*2)
        _aline(gs,(155,88,25),55,(gx,w),(gx,T+w))
    s.blit(gs,(0,0))
    h = T//2
    pygame.draw.rect(s, (100,58,14), (2,h-1,T-4,2))
    xs = _surf(T)
    _aline(xs,(95,52,12),210,(3,3),(T-3,T-3),3); _aline(xs,(95,52,12),210,(T-3,3),(3,T-3),3)
    s.blit(xs,(0,0))
    for nx,ny in [(5,5),(T-6,5),(5,T-6),(T-6,T-6),(T//2,h)]:
        pygame.draw.circle(s,(55,38,10),(nx,ny),3); pygame.draw.circle(s,(225,195,120),(nx-1,ny-1),1)
    hl = _surf(T)
    _aline(hl,(255,200,120),90,(2,1),(T-2,1)); _aline(hl,(255,200,120),50,(1,2),(1,T-2))
    s.blit(hl,(0,0))
    pygame.draw.rect(s,(72,42,8),(0,0,T,T),2)
    sh = _surf(T)
    _aline(sh,(0,0,0),110,(0,T-1),(T,T-1)); _aline(sh,(0,0,0),85,(T-1,0),(T-1,T))
    s.blit(sh,(0,0))
    return s

def _make_floor(ci, ri, T=TILE_SIZE):
    s = _surf(T)
    bc = (22,68,22) if (ci+ri)%2==0 else (26,78,26)
    s.fill(bc)
    gw = _surf(T)
    for r in range(T//2, 0, -3):
        a = int(14*(1-r/(T/2))); col = _cc(bc[0]+10, bc[1]+14, bc[2]+10)
        pygame.draw.circle(gw, (*col,a), (T//2,T//2), r)
    s.blit(gw,(0,0))
    lr = random.Random(ci*100+ri)
    for _ in range(3):
        bx,by = lr.randint(3,T-4), lr.randint(3,T-4)
        fc = _cc(bc[0]+lr.randint(-3,10), bc[1]+lr.randint(6,20), bc[2]+lr.randint(-3,4))
        s.set_at((bx,by),fc)
        if by>1: s.set_at((bx,by-1),_cc(fc[0],fc[1]+8,fc[2]))
    if ri>0 and MAP_DATA[ri-1][ci]==1:
        for i in range(6): _aline(s,(0,0,0),40-i*6,(0,i),(T,i))
    d = _surf(T); pygame.draw.circle(d,(*_cc(bc[0]-8,bc[1]-8,bc[2]-8),80),(0,0),2)
    s.blit(d,(0,0))
    return s

class Tile(pygame.sprite.Sprite):
    def __init__(self, x, y, tile_type):
        super().__init__()
        self.tile_type = tile_type
        self.image = _make_solid() if tile_type=="solid" else _make_breakable()
        self.rect = self.image.get_rect(topleft=(x*TILE_SIZE, y*TILE_SIZE))

def build_background():
    T,W,H = TILE_SIZE, WIDTH, MAP_ROWS*TILE_SIZE
    s = pygame.Surface((W,H), pygame.SRCALPHA)
    for ri,row in enumerate(MAP_DATA):
        for ci in range(len(row)): s.blit(_make_floor(ci,ri),(ci*T,ri*T))
    sh = pygame.Surface((W,H), pygame.SRCALPHA)
    for ri,row in enumerate(MAP_DATA):
        for ci,v in enumerate(row):
            if v!=1: continue
            sx,sy = ci*T, ri*T
            if ci+1<len(row) and row[ci+1]!=1:
                for i in range(6): _aline(sh,(0,0,0),55-i*8,(sx+T+i,sy+2),(sx+T+i,sy+T))
            if ri+1<len(MAP_DATA) and MAP_DATA[ri+1][ci]!=1:
                for i in range(5): _aline(sh,(0,0,0),50-i*8,(sx+2,sy+T+i),(sx+T,sy+T+i))
    s.blit(sh,(0,0))
    vig = pygame.Surface((W,H), pygame.SRCALPHA)
    for i in range(20): pygame.draw.rect(vig,(0,0,0,int(i*3.5)),(i,i,W-i*2,H-i*2),1)
    s.blit(vig,(0,0))
    grid = pygame.Surface((W,H), pygame.SRCALPHA)
    for y in range(0,H,T): _aline(grid,(0,0,0),28,(0,y),(W,y))
    for x in range(0,W,T): _aline(grid,(0,0,0),28,(x,0),(x,H))
    s.blit(grid,(0,0))
    return s

def build_tiles():
    g = pygame.sprite.Group()
    for ri,row in enumerate(MAP_DATA):
        for ci,v in enumerate(row):
            if v in (1,2): g.add(Tile(ci, ri, "solid" if v==1 else "breakable"))
    return g

