import pygame, os

_BASE = os.path.join(os.path.dirname(__file__), "assets", "sounds")
_sfx  = {}
_bgm_playing = None

def _path(name): return os.path.join(_BASE, name+".wav")

def init():
    """Gọi sau pygame.init()"""
    try:
        pygame.mixer.init(frequency=44100, size=-16, channels=1, buffer=512)
        for name in ("bomb_place","explosion","enemy_die","player_die","walk","win"):
            try: _sfx[name] = pygame.mixer.Sound(_path(name))
            except: pass
        # Volume mặc định
        if "explosion"  in _sfx: _sfx["explosion"].set_volume(0.8)
        if "bomb_place" in _sfx: _sfx["bomb_place"].set_volume(0.6)
        if "walk"       in _sfx: _sfx["walk"].set_volume(0.15)
    except Exception as e:
        print(f"[sound] init failed: {e}")

def play(name):
    if name in _sfx: _sfx[name].play()

def play_bgm():
    global _bgm_playing
    try:
        bgm = _path("bgm")
        if os.path.exists(bgm) and _bgm_playing != "bgm":
            pygame.mixer.music.load(bgm)
            pygame.mixer.music.set_volume(0.35)
            pygame.mixer.music.play(-1)   # loop mãi
            _bgm_playing = "bgm"
    except: pass

def stop_bgm():
    global _bgm_playing
    try: pygame.mixer.music.stop(); _bgm_playing = None
    except: pass