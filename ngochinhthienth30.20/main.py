import pygame, math, random
from dataclasses import dataclass
from settings import *
from map import build_tiles, build_background, MAP_ROWS
from player import Player
from enemy import Enemy
from bomb import Explosion
import sound
from leaderboard import add_score, get_leaderboard, is_high_score

# ── Init ──────────────────────────────────────────────────────────────────────
pygame.init()
sound.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption(TITLE)
clock  = pygame.time.Clock()

# ── Fonts & Colors ────────────────────────────────────────────────────────────
def _font(sz, bold=True): return pygame.font.SysFont("Courier New", sz, bold=bold)
fT, fB, fM, fS, fH = _font(72), _font(52), _font(32), _font(22, False), _font(28)

C_BG,C_GRID   = (10,10,18),(20,40,20)
C_AMB,C_AMB2  = (255,180,0),(255,120,0)
C_CYAN,C_WHITE = (0,240,220),(255,255,255)
C_GRAY,C_RED  = (120,120,120),(255,50,50)
C_GREEN,C_GOLD = (50,255,120),(255,215,0)

# ── States & Groups ───────────────────────────────────────────────────────────
MENU, PLAYING, LB = 0, 1, 2
g_tiles = pygame.sprite.Group()
g_bombs = pygame.sprite.Group()
g_expl  = pygame.sprite.Group()
g_enemy = pygame.sprite.Group()

bg_surf = None
state   = MENU
sound.play_bgm()
player  = None
win = game_over = score_saved = False
score = tick = 0

# ── Pre-baked surfaces ────────────────────────────────────────────────────────
stars = [(random.randint(0,WIDTH), random.randint(0,HEIGHT), random.uniform(.3,1.)) for _ in range(80)]

scanlines = pygame.Surface((WIDTH,HEIGHT), pygame.SRCALPHA)
for _y in range(0, HEIGHT, 3):
    pygame.draw.line(scanlines, (0,0,0,40), (0,_y), (WIDTH,_y))

_vs = pygame.Surface((80,48), pygame.SRCALPHA)
for _vy in range(48):
    for _vx in range(80):
        _d = min(1., ((_vx/40-1)**2 + (_vy/24-1)**2) * .9)
        _vs.set_at((_vx,_vy), (0,0,0,int(_d*140)))
vignette = pygame.transform.smoothscale(_vs, (WIDTH,HEIGHT))

grid_tile = pygame.Surface((TILE_SIZE,TILE_SIZE), pygame.SRCALPHA)
for _pt in ((0,0),(TILE_SIZE,0)), ((0,0),(0,TILE_SIZE)):
    pygame.draw.line(grid_tile, (*C_GRID,28), *_pt)

overlay = pygame.Surface((WIDTH,HEIGHT), pygame.SRCALPHA)
overlay.fill((0,0,0,190))

# ── Glow-text cache ───────────────────────────────────────────────────────────
_gcache: dict = {}
def gtext(surf, text, font, x, y, col, gcol=None, gr=6, center=True):
    key = (text, id(font), col, gcol, gr)
    if key not in _gcache:
        base = font.render(text, True, col)
        w,h  = base.get_size(); pad = gr+2
        out  = pygame.Surface((w+pad*2, h+pad*2), pygame.SRCALPHA)
        if gcol:
            for r in range(gr, 0, -2):
                gs = font.render(text, True, gcol); gs.set_alpha(max(30,120-r*18))
                for ox,oy in ((-r,-r),(r,-r),(-r,r),(r,r)): out.blit(gs,(pad+ox,pad+oy))
        out.blit(base,(pad,pad)); _gcache[key] = out
    c = _gcache[key]
    rect = c.get_rect(center=(x,y)) if center else c.get_rect(topleft=(x-gr-2,y-gr-2))
    surf.blit(c, rect); return rect

def pbox(surf, rect, col, bw=3):
    pygame.draw.rect(surf, col, rect, bw)
    for cx,cy in [rect.topleft,(rect.right-6,rect.top),(rect.left,rect.bottom-6),(rect.right-6,rect.bottom-6)]:
        pygame.draw.rect(surf, C_WHITE, (cx,cy,6,6))

# ── Particles ─────────────────────────────────────────────────────────────────
@dataclass
class P:
    x:float; y:float; vx:float; vy:float; life:int; ml:int; col:tuple; sz:int

_psurfs: dict = {}
parts: list[P] = []

def spark(x, y, col):
    parts.append(P(x,y, random.uniform(-1.5,1.5), random.uniform(-2.5,-.5),
                   random.randint(30,70), 70, col, random.randint(2,5)))

def draw_parts(surf):
    alive = []
    for p in parts:
        p.x+=p.vx; p.y+=p.vy; p.life-=1
        if p.life<=0: continue
        alive.append(p)
        if p.sz not in _psurfs:
            s=pygame.Surface((p.sz*2,p.sz*2),pygame.SRCALPHA)
            pygame.draw.circle(s,(*p.col,255),(p.sz,p.sz),p.sz); _psurfs[p.sz]=s
        _psurfs[p.sz].set_alpha(int(255*p.life/p.ml))
        surf.blit(_psurfs[p.sz],(int(p.x)-p.sz,int(p.y)-p.sz))
    parts.clear(); parts.extend(alive)

# ── Floating bg bombs ─────────────────────────────────────────────────────────
class BgBomb:
    def __init__(self): self.surf=None; self.reset()
    def reset(self):
        self.x=random.uniform(0,WIDTH); self.y=random.uniform(HEIGHT+20,HEIGHT+200)
        self.vy=random.uniform(-.4,-.9); self.vx=random.uniform(-.3,.3)
        self.size=random.randint(12,28); alpha=random.randint(20,60)
        d=self.size*2+4; s=pygame.Surface((d,d),pygame.SRCALPHA)
        pygame.draw.circle(s,(*C_AMB2,alpha),(self.size+2,self.size+2),self.size)
        pygame.draw.line(s,(*C_AMB,alpha),(self.size+2,2),(self.size+6,-2),2)
        self.surf=s
    def tick(self, surf):
        self.x+=self.vx; self.y+=self.vy
        if self.y<-50: self.reset(); return
        surf.blit(self.surf,(int(self.x)-self.size,int(self.y)-self.size))

bg_bombs = [BgBomb() for _ in range(18)]

# ── Background draw ───────────────────────────────────────────────────────────
def draw_bg():
    screen.fill(C_BG)
    t = tick*.015
    for sx,sy,spd in stars:
        b=int((.5+.5*math.sin(t*spd*3+sx))*180+40)
        pygame.draw.circle(screen,(int(200*b/220),int(220*b/220),min(255,b+35)),(sx,sy),max(1,int(1+spd*1.5)))
    off=int((tick*.4)%TILE_SIZE)
    for gx in range(-off,WIDTH+TILE_SIZE,TILE_SIZE):
        for gy in range(-off,HEIGHT+TILE_SIZE,TILE_SIZE): screen.blit(grid_tile,(gx,gy))
    for b in bg_bombs: b.tick(screen)


# ── Screens ───────────────────────────────────────────────────────────────────
def draw_menu():
    draw_bg()
    cy = HEIGHT//2-80
    pulse = math.sin(tick*.07)
    tc = (255, max(80,int(160+pulse*60)), 0)
    gtext(screen,"BOMBERMAN",fT,WIDTH//2+3,cy+3,(60,20,0))
    gtext(screen,"BOMBERMAN",fT,WIDTH//2,cy,tc,C_AMB2,10)
    gtext(screen,"● ARCADE EDITION ●",fS,WIDTH//2,cy+56,C_CYAN,C_CYAN,4)
    lx,ly = WIDTH//2-170, cy+76
    pygame.draw.line(screen,C_AMB,(lx,ly),(lx+340,ly),2)
    for px2 in (lx-4,lx+336): pygame.draw.rect(screen,C_AMB,(px2,ly-3,8,6))
    sc = C_WHITE if (tick//22)%2==0 else C_GREEN
    gtext(screen,"[ SPACE ]  START GAME",fM,WIDTH//2,HEIGHT//2+20,sc,C_GREEN,5)
    gtext(screen,"[ L ]      LEADERBOARD",fM,WIDTH//2,HEIGHT//2+70,C_AMB,C_AMB2,5)
    gtext(screen,"[ ESC ]    QUIT",fM,WIDTH//2,HEIGHT//2+115,C_GRAY)
    gtext(screen,"© 2024  BOMBERMAN GAME",fS,WIDTH//2,HEIGHT-22,C_GRAY)
    screen.blit(scanlines,(0,0)); screen.blit(vignette,(0,0))
    if random.random()<.15:
        spark(random.randint(WIDTH//2-200,WIDTH//2+200),cy+20,random.choice([C_AMB,C_AMB2,C_CYAN,C_WHITE]))
    draw_parts(screen)

def draw_leaderboard():
    draw_bg()
    pw,ph = 480,340; px,py = WIDTH//2-240,HEIGHT//2-170
    pan=pygame.Surface((pw,ph),pygame.SRCALPHA); pan.fill((8,20,8,210)); screen.blit(pan,(px,py))
    pbox(screen,pygame.Rect(px,py,pw,ph),C_AMB)
    gtext(screen,"HIGH SCORES",fB,WIDTH//2,py+38,C_GOLD,C_AMB2,8)
    pygame.draw.line(screen,C_AMB,(px+20,py+66),(px+pw-20,py+66),2)
    for i,e in enumerate(get_leaderboard()):
        rc=[C_GOLD,C_WHITE,C_AMB,C_CYAN,C_GRAY][i]
        gtext(screen,f"#{i+1}  {e['name']:<10}  {e['score']:>6}",fM,WIDTH//2,py+90+i*44,rc,rc if i<3 else None,3)
    bc = C_WHITE if (tick//25)%2==0 else C_GRAY
    gtext(screen,"[ SPACE ] or [ ESC ] to go back",fS,WIDTH//2,py+ph-24,bc)
    screen.blit(scanlines,(0,0)); screen.blit(vignette,(0,0)); draw_parts(screen)

def draw_gameover():
    screen.blit(overlay,(0,0))
    cx,cy = WIDTH//2,HEIGHT//2
    msg,col,gc = ("YOU WIN!",C_GREEN,C_GREEN) if win else ("GAME OVER",C_RED,C_RED)
    gtext(screen,msg,fB,cx,cy-80,col,gc,int(6+abs(math.sin(tick*.06))*8))
    pw,ph = 320,120; px2,py2 = cx-160,cy-30
    pan=pygame.Surface((pw,ph),pygame.SRCALPHA); pan.fill((10,20,10,200)); screen.blit(pan,(px2,py2))
    pbox(screen,pygame.Rect(px2,py2,pw,ph),C_AMB,2)
    gtext(screen,"SCORE",fS,cx,py2+22,C_GRAY)
    gtext(screen,f"{score:06d}",fM,cx,py2+58,C_GOLD,C_AMB,5)
    if score_saved:
        hc = C_AMB if (tick//18)%2==0 else C_GOLD
        gtext(screen,"★ NEW HIGH SCORE! ★",fM,cx,cy+115,hc,C_AMB2,6)
        if random.random()<.25:
            spark(cx+random.randint(-120,120),cy+100,random.choice([C_GOLD,C_AMB,C_WHITE]))
    gtext(screen,"[ R ] RESTART   [ ESC ] MENU",fS,cx,cy+155,C_GRAY)
    screen.blit(scanlines,(0,0)); draw_parts(screen)

def draw_hud():
    hy = MAP_ROWS*TILE_SIZE
    pygame.draw.rect(screen,(5,10,5),(0,hy,WIDTH,HEIGHT-hy))
    pygame.draw.line(screen,C_AMB,(0,hy),(WIDTH,hy),2)
    screen.blit(fH.render(f"SCORE  {score:06d}",True,C_GOLD),(12,hy+8))
    screen.blit(fH.render("BOMBS ",True,C_AMB),(WIDTH-210,hy+8))
    rem = player.max_bombs-len(g_bombs)
    for i in range(player.max_bombs):
        bx=WIDTH-90+i*26; by=hy+20; c=C_AMB if i<rem else C_GRAY
        pygame.draw.circle(screen,c,(bx,by),8)
        pygame.draw.line(screen,c,(bx+4,by-7),(bx+8,by-11),2)

# ── Game logic ────────────────────────────────────────────────────────────────
def reset():
    global bg_surf, score_saved
    for g in (g_tiles,g_bombs,g_expl,g_enemy): g.empty()
    g_tiles.add(*build_tiles()); bg_surf=build_background()
    g_enemy.add(Enemy(3,3,g_tiles), Enemy(16,7,g_tiles))
    score_saved=False; return Player()

def hit(rect):
    global score
    tmp=pygame.sprite.Sprite(); tmp.rect=rect
    killed=pygame.sprite.spritecollide(tmp,g_enemy,True); score+=len(killed)*100
    if killed: sound.play('enemy_die')
    for b in pygame.sprite.spritecollide(tmp,g_bombs,False): b.timer=0

def explode(ex,ey):
    sound.play('explosion')
    g_expl.add(Explosion(ex,ey)); hit(pygame.Rect(ex,ey,TILE_SIZE,TILE_SIZE))
    for dx,dy in ((TILE_SIZE,0),(-TILE_SIZE,0),(0,TILE_SIZE),(0,-TILE_SIZE)):
        nx,ny=ex+dx,ey+dy; r=pygame.Rect(nx,ny,TILE_SIZE,TILE_SIZE); blocked=False
        for t in g_tiles:
            if r.colliderect(t.rect):
                if t.tile_type=="solid": blocked=True
                elif t.tile_type=="breakable":
                    t.kill(); g_expl.add(Explosion(nx,ny)); hit(r); blocked=True
                break
        if not blocked: g_expl.add(Explosion(nx,ny)); hit(r)

# ── Main loop ─────────────────────────────────────────────────────────────────
running=True
while running:
    tick+=1
    for ev in pygame.event.get():
        if ev.type==pygame.QUIT: running=False
        elif ev.type==pygame.KEYDOWN:
            k=ev.key
            if k==pygame.K_ESCAPE:
                if state==MENU: running=False
                else: state=MENU if state in (LB,PLAYING) else MENU; sound.play_bgm()
                continue
            if state==MENU:
                if k==pygame.K_SPACE:
                    player=reset(); state,score,win,game_over=PLAYING,0,False,False; sound.stop_bgm()
                elif k==pygame.K_l or ev.unicode.lower()=='l': state=LB
            elif state==LB:
                if k in (pygame.K_SPACE, pygame.K_ESCAPE) or ev.unicode==' ': state=MENU; sound.play_bgm()
            elif state==PLAYING:
                if not game_over and k==pygame.K_SPACE and len(g_bombs)<player.max_bombs:
                    nb=player.drop_bomb()
                    if not any(b.rect.topleft==nb.rect.topleft for b in g_bombs): g_bombs.add(nb); sound.play('bomb_place')
                elif game_over and (k==pygame.K_r or ev.unicode.lower()=='r'):
                    player=reset(); game_over,win,score=False,False,0; sound.stop_bgm()

    if state==MENU: draw_menu()
    elif state==LB:  draw_leaderboard()
    elif state==PLAYING:
        screen.fill((15,35,15))
        if bg_surf: screen.blit(bg_surf,(0,0))
        g_tiles.draw(screen)
        if not game_over:
            done=[(b.rect.x,b.rect.y) for b in list(g_bombs) if b.update()]
            for b in g_bombs: b.draw(screen)
            for ex,ey in done: explode(ex,ey)
            g_expl.update(); g_expl.draw(screen)
            g_enemy.update(g_bombs); g_enemy.draw(screen)
            player.update(g_tiles,g_bombs); player.draw(screen)
            if pygame.sprite.spritecollideany(player,g_enemy) or \
               pygame.sprite.spritecollideany(player,g_expl): game_over=True; sound.play('player_die')
            if not g_enemy: win,game_over=True,True; sound.play('win')
            if game_over and not score_saved and is_high_score(score):
                add_score(score,"Player"); score_saved=True
            draw_hud()
        else:
            g_expl.draw(screen); g_enemy.draw(screen)
            if player: player.draw(screen)
            draw_hud(); draw_gameover()

    pygame.display.flip()
    clock.tick(FPS)

pygame.quit()