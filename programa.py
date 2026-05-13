#teste
import os
import pygame
import sys
import math
import random

# ============================================================
#  CONFIGURAÇÕES GERAIS
# ============================================================
SCREEN_W, SCREEN_H = 1000, 600
FPS        = 60
GRAVITY    = 0.5
GROUND_Y   = 480
BALL_RADIUS = 30

BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
PERSONAGENS_DIR = os.path.join(BASE_DIR, "Personagens")
PLAYER1_IMAGE_PATH = os.path.join(ASSETS_DIR, "player1.png")
PLAYER2_IMAGE_PATH = os.path.join(ASSETS_DIR, "player2.png")
HAALAND_IMAGE_PATH = os.path.join(ASSETS_DIR, "haaland.png")
MBAPPE_IMAGE_PATH = os.path.join(ASSETS_DIR, "Mbappe.png")
YAMAL_IMAGE_PATH = os.path.join(ASSETS_DIR, "yAMAL.png")
KANE_IMAGE_PATH = os.path.join(ASSETS_DIR, "kane.png")
RONY_IMAGE_PATH = os.path.join(ASSETS_DIR, "rony.png")
PEDRO_RAUL_IMAGE_PATH = os.path.join(ASSETS_DIR, "pedro raul.png")
CEDRIC_IMAGE_PATH = os.path.join(ASSETS_DIR, "cedric.png")
# Novas imagens vindas da pasta Personagens
APODI_IMAGE_PATH   = os.path.join(PERSONAGENS_DIR, "Apodi.png")
TOGURO_IMAGE_PATH  = os.path.join(PERSONAGENS_DIR, "Toguro.png")
RAPOSAO_IMAGE_PATH = os.path.join(PERSONAGENS_DIR, "Raposao.png")
DITADOR_HAT_PATH   = os.path.join(PERSONAGENS_DIR, "Chapeu ditador.png")

def _portrait_path(filename):
    return os.path.join(ASSETS_DIR, filename)

# ─── Paleta Retro/Pixel ──────────────────────────────────────
BLACK        = (  0,   0,   0)
WHITE        = (255, 255, 255)
BG_DARK      = (  6,   6,  18)
BG_MID       = ( 14,  14,  40)
BG_GRID      = ( 18,  18,  50)
FIELD_DARK   = ( 16,  68,  26)
FIELD_LITE   = ( 22,  86,  34)
LINE_COL     = (170, 205, 170)
GOAL_SILVER  = (185, 190, 210)
GOAL_DARK    = ( 90,  95, 115)
NET_COL      = ( 70,  80, 105)
YELLOW       = (255, 220,   0)
GOLD         = (230, 160,   0)
RED          = (220,  35,  35)
LIGHT_RED    = (255, 110, 110)
BLUE         = ( 30,  70, 210)
LIGHT_BLUE   = (110, 150, 255)
GREEN_NEON   = (  0, 210,  70)
ORANGE       = (255, 115,   0)
CYAN         = (  0, 195, 215)
PURPLE       = ( 95,  15, 175)
DARK_GRAY    = ( 45,  45,  60)
GRAY         = (115, 115, 135)
PIXEL_SHADOW = ( 18,  18,  36)
STADIUM_COL  = ( 22,  22,  55)
CROWD_COL    = ( 28,  28,  65)

# ─── Goleiras ────────────────────────────────────────────────
GOAL_W      = 70                      # Profundidade visual do gol
GOAL_H      = 230                     # Altura do gol (mais alto p/ destaque)
GOAL_Y      = GROUND_Y - GOAL_H
POST_THICK  = 6                       # Espessura visual da trave
DEPTH_TOP   = 14                      # Quanto o "fundo" do gol é mais baixo (perspectiva)

# ─── Controles ───────────────────────────────────────────────
CONTROLS_P1 = {"left": pygame.K_a, "right": pygame.K_d, "jump": pygame.K_w, "kick": pygame.K_q, "ability": pygame.K_e}
CONTROLS_P2 = {"left": pygame.K_LEFT, "right": pygame.K_RIGHT, "jump": pygame.K_UP, "kick": pygame.K_SEMICOLON, "ability": pygame.K_RSHIFT}

# ─── Scanline surface (pre-built) ────────────────────────────
_SCANLINE_SURF = None

def get_scanline_surf():
    global _SCANLINE_SURF
    if _SCANLINE_SURF is None:
        _SCANLINE_SURF = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        for y in range(0, SCREEN_H, 3):
            pygame.draw.rect(_SCANLINE_SURF, (0, 0, 0, 55), (0, y, SCREEN_W, 1))
    return _SCANLINE_SURF


# ============================================================
#  FONTES
# ============================================================
def build_fonts():
    candidates = ["couriernew", "courier", "lucidaconsole",
                  "freemono", "dejavusansmono", "monospace"]
    best = None
    for c in candidates:
        try:
            f = pygame.font.SysFont(c, 14, bold=True)
            if f:
                best = c
                break
        except Exception:
            pass

    def mk(size):
        if best:
            return pygame.font.SysFont(best, size, bold=True)
        return pygame.font.Font(None, size + 4)

    return mk(15), mk(22), mk(36), mk(62)   # sm, md, lg, xl


# ============================================================
#  PIXEL-SPRITE DE PERSONAGEM
# ============================================================
CELL = 6

SPRITE_ROWS = [
    "  HHHH  ",
    " HHHHHH ",
    " H L LH ",
    " HHHHHH ",
    "  HHHH  ",
    "  BBBB  ",
    " BBBBBB ",
    "BBBBBBBB",
    " BBBBBB ",
    "  LL RR ",
    "  LL RR ",
    " LLL RRR",
]

def draw_pixel_sprite(surface, cx, cy, colors, scale=1):
    c  = CELL * scale
    tw = 8 * c
    th = len(SPRITE_ROWS) * c
    sx = cx - tw // 2
    sy = cy - th // 2
    for ri, row in enumerate(SPRITE_ROWS):
        for ci2, ch in enumerate(row):
            if ch == " ":
                continue
            col = colors.get(ch, BLACK)
            pygame.draw.rect(surface, col, (sx + ci2 * c, sy + ri * c, c - 1, c - 1))

def dark(color, amount=50):
    return tuple(max(0, v - amount) for v in color)


# ============================================================
#  PERSONAGENS
# ============================================================
def _spr(head, body, foot):
    return {"H": head, "B": body, "L": foot, "R": foot}

CHARACTERS = [
    {"name": "CR7",        "color": GOLD,            "light": YELLOW,
     "sprite":   _spr(YELLOW,           GOLD,            (180, 130, 0)),
     "image":    PLAYER1_IMAGE_PATH,
     "portrait": PLAYER1_IMAGE_PATH},

    {"name": "MESSI",      "color": LIGHT_BLUE,      "light": (185, 220, 255),
     "sprite":   _spr((185, 220, 255),  LIGHT_BLUE,      (40, 80, 200)),
     "image":    PLAYER2_IMAGE_PATH,
     "portrait": PLAYER2_IMAGE_PATH},

    {"name": "MBAPPE",     "color": (60, 80, 200),   "light": (140, 170, 255),
     "sprite":   _spr((140, 170, 255),  (60, 80, 200),   (20, 30, 130)),
     "image":    MBAPPE_IMAGE_PATH,
     "portrait": MBAPPE_IMAGE_PATH},

    {"name": "HAALAND",    "color": (140, 220, 230), "light": (200, 240, 250),
     "sprite":   _spr((200, 240, 250),  (140, 220, 230), (40, 130, 170)),
     "image":    HAALAND_IMAGE_PATH,
     "portrait": HAALAND_IMAGE_PATH},

    {"name": "YAMAL",      "color": RED,             "light": LIGHT_RED,
     "sprite":   _spr(LIGHT_RED,        RED,             (140, 20, 20)),
     "image":    YAMAL_IMAGE_PATH,
     "portrait": YAMAL_IMAGE_PATH},

    {"name": "KANE",       "color": (210, 215, 225), "light": (240, 240, 250),
     "sprite":   _spr((240, 240, 250),  (210, 215, 225), (110, 115, 135)),
     "image":    KANE_IMAGE_PATH,
     "portrait": KANE_IMAGE_PATH},

    {"name": "RONY",       "color": (10, 130, 50),   "light": GREEN_NEON,
     "sprite":   _spr(GREEN_NEON,       (10, 130, 50),   (5, 70, 25)),
     "image":    RONY_IMAGE_PATH,
     "portrait": RONY_IMAGE_PATH},

    {"name": "PEDRO RAUL", "color": (45, 45, 55),    "light": (180, 180, 195),
     "sprite":   _spr((180, 180, 195),  (45, 45, 55),    (15, 15, 25)),
     "image":    PEDRO_RAUL_IMAGE_PATH,
     "portrait": PEDRO_RAUL_IMAGE_PATH},

    {"name": "APODI",      "color": (30, 130, 50),   "light": (90, 210, 110),
     "sprite":   _spr((90, 210, 110),   (30, 130, 50),   (15, 80, 30)),
     "image":    APODI_IMAGE_PATH,
     "portrait": APODI_IMAGE_PATH},

    {"name": "CEDRIC",     "color": PURPLE,          "light": (170, 90, 235),
     "sprite":   _spr((170, 90, 235),   PURPLE,          (55, 5, 115)),
     "image":    CEDRIC_IMAGE_PATH,
     "portrait": CEDRIC_IMAGE_PATH},

    {"name": "TOGURO",     "color": (40, 40, 50),    "light": (170, 170, 185),
     "sprite":   _spr((170, 170, 185),  (40, 40, 50),    (15, 15, 25)),
     "image":    TOGURO_IMAGE_PATH,
     "portrait": TOGURO_IMAGE_PATH},

    {"name": "RAPOSAO",    "color": (210, 50, 40),   "light": (255, 130, 100),
     "sprite":   _spr((255, 130, 100),  (210, 50, 40),   (130, 20, 15)),
     "image":    RAPOSAO_IMAGE_PATH,
     "portrait": RAPOSAO_IMAGE_PATH},
]


# ─── Cache de portraits (carregado sob demanda) ─────────────
_PORTRAIT_CACHE = {}

def get_portrait(path, size=(130, 150)):
    """Carrega o retrato, recortando o fundo transparente e mantendo o
    aspect ratio do conteúdo dentro da caixa pedida (size)."""
    if not path:
        return None
    key = (path, size)
    if key not in _PORTRAIT_CACHE:
        try:
            if not os.path.exists(path):
                _PORTRAIT_CACHE[key] = None
                return None
            img = pygame.image.load(path).convert_alpha()
            # Recorta os pixels totalmente transparentes ao redor — sem isso,
            # arquivos com bastante "padding" ficam com a figura minúscula
            # depois do smoothscale.
            bbox = img.get_bounding_rect()
            if bbox.w > 0 and bbox.h > 0:
                img = img.subsurface(bbox).copy()
            iw, ih = img.get_size()
            tw, th = size
            # Escala mantendo proporção, encaixando dentro de (tw, th)
            ratio = min(tw / iw, th / ih)
            new_w = max(1, int(iw * ratio))
            new_h = max(1, int(ih * ratio))
            _PORTRAIT_CACHE[key] = pygame.transform.smoothscale(img, (new_w, new_h))
        except Exception:
            _PORTRAIT_CACHE[key] = None
    return _PORTRAIT_CACHE[key]


_HAT_CACHE = [None]
def get_dictator_hat(target_h=60):
    """Chapéu de ditador escalado, com fundo branco-ish removido."""
    if _HAT_CACHE[0] is not None:
        return _HAT_CACHE[0]
    if not os.path.exists(DITADOR_HAT_PATH):
        return None
    try:
        raw = pygame.image.load(DITADOR_HAT_PATH).convert()
        w, h = raw.get_size()
        # Pixels claros (perto do branco) viram transparentes
        surf = pygame.Surface((w, h), pygame.SRCALPHA)
        for x in range(w):
            for y in range(h):
                r, g, b, _ = raw.get_at((x, y))
                if r > 235 and g > 235 and b > 235:
                    continue  # deixa transparente
                surf.set_at((x, y), (r, g, b, 255))
        bbox = surf.get_bounding_rect()
        if bbox.w > 0:
            surf = surf.subsurface(bbox).copy()
        iw, ih = surf.get_size()
        tw = int(iw * target_h / ih)
        _HAT_CACHE[0] = pygame.transform.smoothscale(surf, (tw, target_h))
    except Exception:
        _HAT_CACHE[0] = None
    return _HAT_CACHE[0]
# desc habilidades
def draw_ability_tooltip(surface, char_name, rect, f_sm):
        ABILITY_DESCRIPTIONS = {
            "CR7":        "Chute turbinado",
            "MESSI":      "Dribla com a bola",
            "MBAPPE":     "Bola teletransporta",
            "HAALAND":    "Gigante",
            "YAMAL":      "Super Velocidade",
            "KANE":       "Furacão",
            "RONY":       "Bicicleta",
            "PEDRO RAUL": "Super Pulo",
            "APODI":      "Fica muito mais rápido.",
            "CEDRIC":     "Apenas Cedric Soares",
            "TOGURO":     "SABOR!",
            "RAPOSAO":    "Garras",
        }
        desc = ABILITY_DESCRIPTIONS.get(char_name, "")
        if not desc:
            return
        lbl = f_sm.render(f"SKILL: {desc}", False, CYAN)
        surface.blit(lbl, (rect.centerx - lbl.get_width() // 2, rect.bottom + 70))

# ============================================================
#  PARTÍCULAS
# ============================================================
class Particle:
    def __init__(self, x, y, vx, vy, color, life):
        self.x, self.y   = float(x), float(y)
        self.vx, self.vy = vx, vy
        self.color = color
        self.life  = self.max_life = float(life)

    def update(self):
        self.x  += self.vx
        self.y  += self.vy
        self.vy += 0.28
        self.vx *= 0.97
        self.life -= 1

    @property
    def alive(self):
        return self.life > 0

    def draw(self, surface):
        ratio = self.life / self.max_life
        sz    = max(2, int(8 * ratio))
        pygame.draw.rect(surface, self.color,
                         (int(self.x) - sz // 2, int(self.y) - sz // 2, sz, sz))


def burst(x, y, base_color, n=60):
    palette = [base_color, YELLOW, WHITE, GOLD, (255, 255, 100), (255, 200, 50)]
    pts = []
    for _ in range(n):
        vx  = random.uniform(-9, 9)
        vy  = random.uniform(-13, -2)
        col = random.choice(palette)
        lf  = random.randint(25, 65)
        pts.append(Particle(x, y, vx, vy, col, lf))
    return pts


# ============================================================
#  CLASSE JOGADOR
# ============================================================
class Player:
    WIDTH  = int(50 * 1.5 * 2*1.2)   # 150
    HEIGHT = int(70 * 1.5*1.2)        # 105
    SPEED  = 5
    JUMP_FORCE    = -13
    KICK_RADIUS   = 90
    KICK_FORCE    = 8
    KICK_DURATION = 15
    COLL_W_FACTOR = 0.68
    COLL_H_FACTOR = 0.94
    ABILITY_COOLDOWN = 1200  # 20 s × 60 fps
    ABILITY_DURATION = 180   # 3 s × 60 fps

    def __init__(self, x, y, char_data, controls, facing_right=True):
        self.x, self.y   = float(x), float(y)
        self.vx = self.vy = 0.0
        self.color        = char_data["color"]
        self.light_color  = char_data["light"]
        self.sprite_cols  = char_data["sprite"]
        self.char_name    = char_data["name"]
        self.controls     = controls
        self.facing_right = facing_right
        self.on_ground    = False
        self.kicking      = False
        self.kick_timer   = 0
        self.score        = 0
        self.image        = None
        self.ability_cooldown = 0
        self.ability_armed    = False
        self.ability_timer    = 0
        self.scale            = 1.0
        self.float_timer      = 0
        self.speed_mult       = 1.0
        self.frozen_timer        = 0        # Raposão: oponente travado
        self.super_jump_timer    = 0        # Pedro Raul: pulo turbinado + queda rápida
        self.upside_down_timer   = 0        # Rony: vira de cabeça pra baixo
        self.hat_timer           = 0        # Mbappé: chapéu de ditador
        self.auto_goal_armed     = False    # (não usado mais)
        self.invert_timer        = 0        # Cedric: controles invertidos
        self.rony_spin_timer     = 0        # Rony: voa no ar + girando 360°

        ip = char_data.get("image")
        if ip and os.path.exists(ip):
            try:
                img = pygame.image.load(ip).convert_alpha()
                # Recorta a área não-transparente — sem isso, arquivos PNG
                # com tamanhos diferentes ficam com escalas visuais distintas
                # no jogo (uns gigantes, outros pequenos).
                bbox = img.get_bounding_rect()
                if bbox.w > 0 and bbox.h > 0:
                    img = img.subsurface(bbox).copy()
                tw, th = img.get_size()
                # Encaixa na altura do player; largura proporcional, sem
                # ultrapassar a largura do rect.
                target_h = self.HEIGHT
                target_w = int(tw * target_h / th)
                if target_w > self.WIDTH:
                    target_w = self.WIDTH
                    target_h = int(th * target_w / tw)
                self.image = pygame.transform.smoothscale(img, (target_w, target_h))
            except Exception:
                pass

    @property
    def rect(self):
        return pygame.Rect(self.x, self.y, self.WIDTH, self.HEIGHT)

    @property
    def collision_rect(self):
        eff_w = int(self.WIDTH  * self.scale)
        eff_h = int(self.HEIGHT * self.scale)
        cw    = int(eff_w * self.COLL_W_FACTOR)
        ch    = int(eff_h * self.COLL_H_FACTOR)
        cx    = int(self.x + self.WIDTH / 2 - cw / 2)
        cy    = int(self.y + self.HEIGHT - ch)
        return pygame.Rect(cx, cy, cw, ch)

    @property
    def foot_center(self):
        eff_w  = self.WIDTH  * self.scale
        eff_h  = self.HEIGHT * self.scale
        draw_x = self.x + self.WIDTH  / 2 - eff_w / 2
        draw_y = self.y + self.HEIGHT - eff_h
        fx     = draw_x + eff_w * (0.7 if self.facing_right else 0.3)
        fy     = draw_y + eff_h * 0.85
        return (fx, fy)

    def _clamp_ground(self):
        if self.y + self.HEIGHT >= GROUND_Y:
            self.y = GROUND_Y - self.HEIGHT
            if self.vy > 0:
                self.vy = 0
            self.on_ground = True

    def handle_input(self, keys):
        # Raposão: oponente fica travado, ignora movimento/pulo/chute
        if self.frozen_timer > 0:
            self.vx *= 0.5
            return

        spd = self.SPEED * self.speed_mult
        # Cedric: troca left <-> right durante invert_timer
        if self.invert_timer > 0:
            left_key, right_key = self.controls["right"], self.controls["left"]
        else:
            left_key, right_key = self.controls["left"], self.controls["right"]

        if keys[left_key]:
            self.vx = -spd
            self.facing_right = False
        elif keys[right_key]:
            self.vx = spd
            self.facing_right = True
        else:
            self.vx *= 0.75

        if keys[self.controls["jump"]] and self.on_ground:
            jump = self.JUMP_FORCE * (1.6 if self.super_jump_timer > 0 else 1.0)
            self.vy = jump
            self.on_ground = False

        if keys[self.controls["kick"]] and not self.kicking:
            self.kicking    = True
            self.kick_timer = self.KICK_DURATION

        ak = self.controls.get("ability")
        if (ak and keys[ak] and not self.ability_armed
                and self.ability_timer == 0 and self.ability_cooldown == 0):
            self.ability_armed    = True
            self.ability_cooldown = self.ABILITY_COOLDOWN

    def update(self):
        # Rony spin: travado no ar, sem gravidade nem movimento horizontal
        if self.rony_spin_timer > 0:
            self.rony_spin_timer -= 1
            self.vx = 0.0
            self.vy = 0.0
            self.on_ground = False
            if self.frozen_timer       > 0: self.frozen_timer       -= 1
            if self.super_jump_timer   > 0: self.super_jump_timer   -= 1
            if self.upside_down_timer  > 0: self.upside_down_timer  -= 1
            if self.hat_timer          > 0: self.hat_timer          -= 1
            if self.invert_timer       > 0: self.invert_timer       -= 1
            if self.ability_cooldown   > 0: self.ability_cooldown   -= 1
            if self.kicking:
                self.kick_timer -= 1
                if self.kick_timer <= 0:
                    self.kicking = False
            return

        if self.float_timer > 0:
            self.float_timer -= 1
            self.vy += GRAVITY * 0.22
            if self.vy < -7:
                self.vy = -7
            self.on_ground = False
        elif self.super_jump_timer > 0:
            # Pedro Raul: queda acelerada quando está descendo
            self.vy += GRAVITY * (2.2 if self.vy > 0 else 1.0)
        else:
            self.vy += GRAVITY

        self.x += self.vx
        self.y += self.vy

        if self.float_timer > 0:
            if self.y < 10:
                self.y = 10.0
                if self.vy < 0:
                    self.vy = 0
            if self.y + self.HEIGHT >= GROUND_Y:
                self.y = float(GROUND_Y - self.HEIGHT)
                self.vy = -5
        else:
            self._clamp_ground()

        if self.ability_cooldown > 0:
            self.ability_cooldown -= 1

        # Timers das habilidades novas
        if self.frozen_timer       > 0: self.frozen_timer       -= 1
        if self.super_jump_timer   > 0: self.super_jump_timer   -= 1
        if self.upside_down_timer  > 0: self.upside_down_timer  -= 1
        if self.hat_timer          > 0: self.hat_timer          -= 1
        if self.invert_timer       > 0: self.invert_timer       -= 1

        if self.x < 0:
            self.x = 0.0
        if self.x + self.WIDTH > SCREEN_W:
            self.x = float(SCREEN_W - self.WIDTH)

        if self.kicking:
            self.kick_timer -= 1
            if self.kick_timer <= 0:
                self.kicking = False

    def try_kick_ball(self, ball):
        if not self.kicking:
            return False
        fx, fy = self.foot_center
        dist = math.hypot(ball.x - fx, ball.y - fy)
        if dist < self.KICK_RADIUS + BALL_RADIUS:
            dist = max(dist, 1)
            dx = (ball.x - fx) / dist
            dy = (ball.y - fy) / dist
            ball.vx = dx * self.KICK_FORCE + (self.SPEED if self.facing_right else -self.SPEED)
            ball.vy = dy * self.KICK_FORCE - 2
            return True
        return False

    def collide_with_player(self, other):
        r1, r2 = self.collision_rect, other.collision_rect
        if not r1.colliderect(r2):
            return
        ov   = (r1.right - r2.left) if self.x < other.x else (r2.right - r1.left)
        push = ov / 2
        if self.x < other.x:
            self.x -= push; other.x += push
        else:
            self.x += push; other.x -= push
        self._clamp_ground()
        other._clamp_ground()

    def _draw_aura(self, surface, x, y, w, h):
        if not self.ability_armed and self.ability_timer == 0:
            return
        t     = pygame.time.get_ticks()
        pulse = 0.5 + 0.5 * math.sin(t * 0.005)
        if self.ability_timer > 0:
            alpha = int(190 + 65 * pulse)
            col   = (255, 200, 0)
            rings = 4
        else:
            alpha = int(130 + 120 * pulse)
            col   = (255, 255, 100)
            rings = 3
        pad  = 20
        aw   = w + pad * 2
        ah   = h + pad * 2
        glow = pygame.Surface((aw, ah), pygame.SRCALPHA)
        for i in range(rings, 0, -1):
            a  = max(0, alpha - (rings - i) * 55)
            ep = i * (pad // max(rings, 1))
            pygame.draw.ellipse(glow, (*col, a),
                                (pad - ep, pad - ep, w + ep * 2, h + ep * 2), 3)
        surface.blit(glow, (x - pad, y - pad))

    def _draw_hurricane_effect(self, surface, cx, cy, w, h):
        t     = pygame.time.get_ticks()
        ratio = self.float_timer / 240.0
        pcx   = cx + w // 2
        pcy   = cy + h // 2
        cols  = [(100, 190, 255), (160, 230, 255), (220, 245, 255)]
        for i in range(18):
            a  = math.radians(t * 0.65 + i * 20)
            rx = int((w * 0.65 + 14 * math.sin(t * 0.005 + i * 0.9)) * ratio)
            ry = int((h * 0.35 + 8  * math.sin(t * 0.007 + i * 0.7)) * ratio)
            px = pcx + int(rx * math.cos(a))
            py = pcy + int(ry * math.sin(a))
            sz = max(2, int((4 + 3 * math.sin(t * 0.012 + i)) * ratio))
            pygame.draw.rect(surface, cols[i % 3], (px - sz // 2, py - sz // 2, sz, sz))

    def draw(self, surface):
        w, h   = self.WIDTH, self.HEIGHT
        t_k    = self.kick_timer / self.KICK_DURATION if self.kicking else 0.0

        eff_w  = int(w * self.scale)
        eff_h  = int(h * self.scale)
        draw_x = int(self.x + w / 2 - eff_w / 2)
        draw_y = int(self.y + h - eff_h)

        self._draw_aura(surface, draw_x, draw_y, eff_w, eff_h)
        if self.float_timer > 0:
            self._draw_hurricane_effect(surface, draw_x, draw_y, eff_w, eff_h)

        if self.image:
            iw0, ih0 = self.image.get_size()
            iw       = max(1, int(iw0 * self.scale))
            ih       = max(1, int(ih0 * self.scale))
            img      = (self.image if (iw, ih) == (iw0, ih0)
                        else pygame.transform.smoothscale(self.image, (iw, ih)))
            if not self.facing_right:
                img = pygame.transform.flip(img, True, False)
            # Rony: vira de ponta-cabeça (flip vertical)
            if self.upside_down_timer > 0:
                img = pygame.transform.flip(img, False, True)
            # Centraliza horizontalmente; alinha "pés" no chão do player
            blit_x = int(self.x + w / 2 - iw / 2)
            blit_y = int(self.y + h - ih)
            # Rony spin: rotação 360° contínua
            if self.rony_spin_timer > 0:
                progress = 1.0 - (self.rony_spin_timer / 120.0)
                spin_deg = progress * 360.0       # giro completo em 2 s
                rot_img  = pygame.transform.rotate(img, spin_deg)
                rect_r   = rot_img.get_rect(center=(blit_x + iw // 2,
                                                    blit_y + ih // 2))
                surface.blit(rot_img, rect_r.topleft)
            else:
                surface.blit(img, (blit_x, blit_y))

            # Mbappé: chapéu de ditador sobre a cabeça
            if self.hat_timer > 0:
                hat = get_dictator_hat()
                if hat is not None:
                    hw, hh = hat.get_size()
                    hat_x = blit_x + iw // 2 - hw // 2
                    hat_y = blit_y - hh + 12
                    surface.blit(hat, (hat_x, hat_y))
        else:
            self._draw_retro(surface, draw_x, draw_y, eff_w, eff_h)

        if self.kicking:
            kx  = int(self.foot_center[0])
            ky  = int(self.foot_center[1])
            rad = int(16 + 18 * (1.0 - t_k))
            col = YELLOW if t_k > 0.5 else ORANGE
            for ang in range(0, 360, 24):
                a  = math.radians(ang)
                px = kx + int(rad * math.cos(a)) - 3
                py = ky + int(rad * math.sin(a)) - 3
                pygame.draw.rect(surface, col, (px, py, 6, 6))

    def _draw_retro(self, surface, x, y, w, h):
        c  = self.color
        lc = self.light_color
        P  = 5

        hx = x + w // 4
        hy = y
        hw = w // 2
        hh = h // 3
        pygame.draw.rect(surface, lc,       (hx,       hy,      hw,    hh))
        pygame.draw.rect(surface, c,        (hx,       hy,      P,     hh))
        pygame.draw.rect(surface, c,        (hx+hw-P,  hy,      P,     hh))
        pygame.draw.rect(surface, c,        (hx,       hy,      hw,    P))
        pygame.draw.rect(surface, c,        (hx,       hy+hh-P, hw,    P))

        eo = hw // 3 if self.facing_right else -hw // 3
        ex = hx + hw // 2 + eo - P
        ey = hy + hh // 2 - P // 2
        pygame.draw.rect(surface, BLACK, (ex, ey, P*2, P*2))
        pygame.draw.rect(surface, WHITE, (ex + P, ey, P, P))

        bx = x + w // 4 + P
        by = hy + hh
        bw = hw - P * 2
        bh = int(h * 0.38)
        pygame.draw.rect(surface, c,  (bx, by, bw, bh))
        pygame.draw.rect(surface, lc, (bx, by, P,  bh))

        lw = bw // 3
        lh = h - (hh + bh)
        pygame.draw.rect(surface, c, (bx,           by + bh, lw, lh))
        pygame.draw.rect(surface, c, (bx + bw - lw, by + bh, lw, lh))
        dc = dark(c, 50)
        pygame.draw.rect(surface, dc, (bx - P,            by + bh + lh - P, lw + P*2, P))
        pygame.draw.rect(surface, dc, (bx + bw - lw - P,  by + bh + lh - P, lw + P*2, P))


# ============================================================
#  CLASSE BOLA
# ============================================================
class Ball:
    FRICTION = 0.80
    BOUNCE   = 0.80

    def __init__(self, x, y):
        self.reset(x, y)
        self.image = None

    def reset(self, x, y):
        self.x, self.y = float(x), float(y)
        self.vx = self.vy = 0.0
        self.angle     = 0.0
        self.locked_to = None
        self.flame_timer = 0

    def update(self, players=()):
        if self.flame_timer > 0:
            self.flame_timer -= 1

        if self.locked_to is not None:
            p = self.locked_to
            self.x     = p.x + p.WIDTH * (0.68 if p.facing_right else 0.32)
            self.y     = p.y + p.HEIGHT * 0.72
            self.vx    = p.vx
            self.vy    = p.vy
            self.angle += p.vx * 1.5
            return

        # ─── Substeps para evitar tunneling em chutes fortes ──────
        # Garante que a bola se mova no máximo ~BALL_RADIUS/2 por sub-step.
        speed     = math.hypot(self.vx, self.vy)
        max_step  = max(8.0, BALL_RADIUS * 0.6)
        n_steps   = max(1, min(10, int(speed / max_step) + 1))
        dt        = 1.0 / n_steps
        for _ in range(n_steps):
            self._step_move(dt)
            for p in players:
                self.collide_with_player(p)

    def _step_move(self, dt):
        self.vy    += GRAVITY * 0.50 * dt
        self.x     += self.vx * dt
        self.y     += self.vy * dt
        self.angle += self.vx * 1.5 * dt

        if self.y + BALL_RADIUS >= GROUND_Y:
            self.y  = GROUND_Y - BALL_RADIUS
            self.vy = -abs(self.vy) * self.BOUNCE
            self.vx *= self.FRICTION ** dt
            if abs(self.vy) < 1.2:
                self.vy = 0

        if self.y - BALL_RADIUS <= 0:
            self.y  = float(BALL_RADIUS)
            self.vy = abs(self.vy) * self.BOUNCE

        # ─── Parede acima do gol (não deixa a bola "passar por cima") ──
        if self.x - BALL_RADIUS <= GOAL_W and self.y + BALL_RADIUS < GOAL_Y:
            self.x  = GOAL_W + BALL_RADIUS
            self.vx = abs(self.vx) * self.BOUNCE

        if self.x + BALL_RADIUS >= SCREEN_W - GOAL_W and self.y + BALL_RADIUS < GOAL_Y:
            self.x  = SCREEN_W - GOAL_W - BALL_RADIUS
            self.vx = -abs(self.vx) * self.BOUNCE

        # ─── Travessão (crossbar): canto superior do gol ───────────────
        for corner_x, sign in ((GOAL_W, 1), (SCREEN_W - GOAL_W, -1)):
            dx = self.x - corner_x
            dy = self.y - GOAL_Y
            if sign * dx >= -POST_THICK:
                dist_sq = dx*dx + dy*dy
                r = BALL_RADIUS + POST_THICK // 2
                if dist_sq < r * r and dist_sq > 0.01:
                    dist = math.sqrt(dist_sq)
                    nx = dx / dist
                    ny = dy / dist
                    overlap = r - dist
                    self.x += nx * overlap
                    self.y += ny * overlap
                    vn = self.vx * nx + self.vy * ny
                    if vn < 0:
                        self.vx -= 2 * vn * nx * self.BOUNCE
                        self.vy -= 2 * vn * ny * self.BOUNCE

        # ─── Travessão (parte horizontal dentro do gol) ────────────────
        if self.x < GOAL_W and self.y - BALL_RADIUS < GOAL_Y:
            self.y  = float(GOAL_Y + BALL_RADIUS)
            self.vy = abs(self.vy) * self.BOUNCE
        if self.x > SCREEN_W - GOAL_W and self.y - BALL_RADIUS < GOAL_Y:
            self.y  = float(GOAL_Y + BALL_RADIUS)
            self.vy = abs(self.vy) * self.BOUNCE

        # ─── Fundo da rede (impede bola de sair pela borda) ────────────
        if self.x - BALL_RADIUS <= 0:
            self.x  = float(BALL_RADIUS)
            self.vx = abs(self.vx) * self.BOUNCE * 0.4
        if self.x + BALL_RADIUS >= SCREEN_W:
            self.x  = float(SCREEN_W - BALL_RADIUS)
            self.vx = -abs(self.vx) * self.BOUNCE * 0.4

    def collide_with_player(self, player):
        rect = player.collision_rect
        cx   = max(rect.left, min(self.x, rect.right))
        cy   = max(rect.top,  min(self.y, rect.bottom))
        dx, dy  = self.x - cx, self.y - cy
        dist_sq = dx * dx + dy * dy

        if dist_sq == 0:
            if not rect.collidepoint(self.x, self.y):
                return
            distances = {
                "l": self.x - rect.left, "r": rect.right  - self.x,
                "t": self.y - rect.top,  "b": rect.bottom - self.y,
            }
            side = min(distances, key=distances.get)
            maps = {"l": (-1, 0, "l"), "r": (1, 0, "r"), "t": (0, -1, "t"), "b": (0, 1, "b")}
            nx, ny, k = maps[side]
            overlap = BALL_RADIUS + distances[k]
        elif dist_sq < BALL_RADIUS * BALL_RADIUS:
            dist = math.sqrt(dist_sq)
            nx, ny  = dx / dist, dy / dist
            overlap = BALL_RADIUS - dist
        else:
            return

        self.x += nx * overlap
        self.y += ny * overlap
        if self.y + BALL_RADIUS > GROUND_Y:
            self.y  = GROUND_Y - BALL_RADIUS
            self.vy = -abs(self.vy) * self.BOUNCE

        dot = (self.vx - player.vx) * nx + (self.vy - player.vy) * ny
        if dot < 0:
            self.vx -= dot * nx * 1.4
            self.vy -= dot * ny * 1.4

    def draw(self, surface):
        ix, iy = int(self.x), int(self.y)
        r      = BALL_RADIUS

        if self.flame_timer > 0:
            t     = pygame.time.get_ticks()
            ratio = self.flame_timer / 180.0
            flame_colors = [(255, 60, 0), (255, 140, 0), (255, 220, 0),
                            (255, 100, 0), (255, 200, 50), (255, 40, 0)]
            for i in range(12):
                a  = math.radians(t * 0.55 + i * 30)
                ri = r + int(7 + 9 * math.sin(t * 0.007 + i * 1.05))
                fx = ix + int(ri * math.cos(a))
                fy = iy + int(ri * math.sin(a))
                sz = max(2, int((5 + 4 * math.sin(t * 0.013 + i * 0.85)) * ratio))
                col = flame_colors[i % len(flame_colors)]
                pygame.draw.rect(surface, col, (fx - sz // 2, fy - sz // 2, sz, sz))

        if self.image:
            rot  = pygame.transform.rotate(self.image, -self.angle)
            rect = rot.get_rect(center=(ix, iy))
            surface.blit(rot, rect)
            return

        pygame.draw.circle(surface, WHITE,     (ix, iy), r)
        pygame.draw.circle(surface, DARK_GRAY, (ix, iy), r, 3)

        pts5 = []
        for i in range(5):
            a = math.radians(self.angle + 18 + i * 72)
            pts5.append((ix + int(r*0.38*math.cos(a)), iy + int(r*0.38*math.sin(a))))
        pygame.draw.polygon(surface, DARK_GRAY, pts5)

        for i in range(5):
            a  = math.radians(self.angle + i * 72)
            bx = ix + int(r * 0.58 * math.cos(a))
            by = iy + int(r * 0.58 * math.sin(a))
            patch = []
            for j in range(5):
                aa = math.radians(self.angle * 0.25 + i * 72 + 36 + j * 72)
                patch.append((bx + int(8*math.cos(aa)), by + int(8*math.sin(aa))))
            pygame.draw.polygon(surface, BLACK, patch)


# ============================================================
#  INTRO STATE
# ============================================================
class IntroState:
    BLINK = 36

    def __init__(self):
        self.timer  = 0
        self.stars  = [(random.randint(0, SCREEN_W-1),
                        random.randint(0, int(SCREEN_H * 0.65)),
                        random.randint(80, 255),
                        random.choice([1, 1, 1, 2]))
                       for _ in range(160)]
        self.ball_x  = SCREEN_W // 2
        self.ball_y  = float(SCREEN_H // 2 + 60)
        self.ball_vy = -3.0
        self.ball_a  = 0.0
        self.shoots  = []
        self.next_sh = 90

    def _maybe_shoot(self):
        self.next_sh -= 1
        if self.next_sh <= 0:
            self.next_sh = random.randint(60, 180)
            sy = random.randint(10, int(SCREEN_H * 0.4))
            self.shoots.append([float(random.randint(0, SCREEN_W)),
                                 float(sy), random.uniform(6, 14),
                                 random.uniform(1.5, 3.5), 30])

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                pygame.quit(); sys.exit()
            return True
        return False

    def update(self):
        self.timer  += 1
        self.ball_vy += 0.38
        self.ball_y  += self.ball_vy
        self.ball_a  += 4.0
        ground = SCREEN_H - 65
        if self.ball_y + 22 >= ground:
            self.ball_y  = float(ground - 22)
            self.ball_vy = -abs(self.ball_vy) * 0.72
            if abs(self.ball_vy) < 1.5:
                self.ball_vy = -8.0
        self._maybe_shoot()
        self.shoots = [[s[0]+s[2], s[1]+s[3], s[2], s[3], s[4]-1]
                       for s in self.shoots if s[4] > 0]

    def draw(self, surface, f_sm, f_md, f_lg, f_xl):
        surface.fill(BG_DARK)

        for sx, sy, br, sz in self.stars:
            br2 = max(60, min(255, br + (random.randint(-30, 30) if random.random() < 0.03 else 0)))
            pygame.draw.rect(surface, (br2, br2, br2), (sx, sy, sz, sz))

        for s in self.shoots:
            ratio = s[4] / 30.0
            ws    = int(s[2] * 3 * ratio)
            col   = (int(255*ratio), int(255*ratio), int(200*ratio))
            pygame.draw.rect(surface, col, (int(s[0])-ws, int(s[1]), ws, 2))

        ground_y = SCREEN_H - 65
        pygame.draw.rect(surface, FIELD_DARK, (0, ground_y, SCREEN_W, SCREEN_H - ground_y))
        for stripe in range(0, SCREEN_W, 80):
            pygame.draw.rect(surface, FIELD_LITE, (stripe, ground_y, 40, SCREEN_H - ground_y))
        pygame.draw.rect(surface, GREEN_NEON, (0, ground_y, SCREEN_W, 3))

        dtg      = ground_y - (self.ball_y + 22)
        sw       = max(6, int(28 * (1.0 - dtg / 250)))
        pygame.draw.ellipse(surface, (0, 35, 10), (self.ball_x - sw, ground_y - 4, sw*2, 8))

        r  = 22
        bx = int(self.ball_x)
        by = int(self.ball_y)
        pygame.draw.circle(surface, WHITE,     (bx, by), r)
        pygame.draw.circle(surface, DARK_GRAY, (bx, by), r, 3)
        for i in range(5):
            a   = math.radians(self.ball_a + i * 72)
            cx2 = bx + int(r * 0.55 * math.cos(a))
            cy2 = by + int(r * 0.55 * math.sin(a))
            pts = [(cx2 + int(5*math.cos(math.radians(self.ball_a + i*72 + 36 + j*72))),
                    cy2 + int(5*math.sin(math.radians(self.ball_a + i*72 + 36 + j*72))))
                   for j in range(5)]
            pygame.draw.polygon(surface, BLACK, pts)

        # Título
        for txt_str, f, col, y_pos in [
            ("COPA",   f_xl, YELLOW,     70),
            ("CABEÇA", f_xl, WHITE,     150),
        ]:
            t  = f.render(txt_str, False, col)
            ts = f.render(txt_str, False, PIXEL_SHADOW)
            ox = SCREEN_W // 2 - t.get_width() // 2
            surface.blit(ts, (ox + 4, y_pos + 4))
            surface.blit(t,  (ox,     y_pos))

        # Underbar
        cabeca = f_xl.render("CABEÇA", False, WHITE)
        bar_x  = SCREEN_W // 2 - cabeca.get_width() // 2
        pygame.draw.rect(surface, GREEN_NEON,
                         (bar_x,     150 + cabeca.get_height() + 4, cabeca.get_width(),   4))
        pygame.draw.rect(surface, YELLOW,
                         (bar_x + 4, 150 + cabeca.get_height() + 9, cabeca.get_width()-8, 2))

        # Subtítulo
        sub  = f_md.render("jogo é jogo e treino é treino", True, GREEN_NEON)
        sub_s= f_md.render("jogo é jogo e treino é treino", True, PIXEL_SHADOW)
        sxp  = SCREEN_W // 2 - sub.get_width() // 2
        surface.blit(sub_s, (sxp + 2, 245 + 2))
        surface.blit(sub,   (sxp,     245))

        if self.timer > 50 and (self.timer // self.BLINK) % 2 == 0:
            pt = f_md.render("PRESS  ENTER  TO  START", False, WHITE)
            surface.blit(pt, (SCREEN_W//2 - pt.get_width()//2, SCREEN_H - 48))

        pygame.draw.rect(surface, YELLOW, (6, 6, SCREEN_W-12, SCREEN_H-12), 4)
        pygame.draw.rect(surface, GOLD,   (12, 12, SCREEN_W-24, SCREEN_H-24), 1)
        for ccx, ccy in [(6,6),(SCREEN_W-10,6),(6,SCREEN_H-10),(SCREEN_W-10,SCREEN_H-10)]:
            pygame.draw.rect(surface, WHITE, (ccx, ccy, 4, 4))

        surface.blit(get_scanline_surf(), (0, 0))


# ============================================================
#  CHAR SELECT STATE
# ============================================================
class CharSelectState:
    BLINK = 34


    def __init__(self):
        self.p1_idx   = 0
        self.p2_idx   = 1
        self.p1_ready = False
        self.p2_ready = False
        self.timer    = 0
        self.p1_flash = 0
        self.p2_flash = 0
        self.anim     = 0.0

    def handle_event(self, event):
        if event.type != pygame.KEYDOWN:
            return None
        if event.key == pygame.K_ESCAPE:
            pygame.quit(); sys.exit()

        n = len(CHARACTERS)

        if not self.p1_ready:
            if event.key == pygame.K_a:
                self.p1_idx   = (self.p1_idx - 1) % n; self.p1_flash = 12
            elif event.key == pygame.K_d:
                self.p1_idx   = (self.p1_idx + 1) % n; self.p1_flash = 12
            elif event.key in (pygame.K_w, pygame.K_q):
                self.p1_ready = True; self.p1_flash = 25

        if not self.p2_ready:
            if event.key == pygame.K_LEFT:
                self.p2_idx   = (self.p2_idx - 1) % n; self.p2_flash = 12
            elif event.key == pygame.K_RIGHT:
                self.p2_idx   = (self.p2_idx + 1) % n; self.p2_flash = 12
            elif event.key in (pygame.K_UP, pygame.K_SEMICOLON):
                self.p2_ready = True; self.p2_flash = 25

        if event.key == pygame.K_r:
            self.p1_ready = self.p2_ready = False

        if event.key == pygame.K_RETURN and self.p1_ready and self.p2_ready:
            return GameState(self.p1_idx, self.p2_idx)

        return None

    def update(self):
        self.timer += 1
        self.anim  += 2.5
        if self.p1_flash > 0: self.p1_flash -= 1
        if self.p2_flash > 0: self.p2_flash -= 1

    def _panel(self, surface, rect, idx, label, ready, flash, f_sm, f_md):
        
        ch   = CHARACTERS[idx]
        tint = tuple(min(28, ch["color"][i] // 6) for i in range(3))
        bg   = tuple(8 + tint[i] for i in range(3))
        bg   = (bg[0], bg[1], max(bg[2], 18))
        pygame.draw.rect(surface, bg, rect)

        for gx in range(rect.left, rect.right, 20):
            pygame.draw.rect(surface, BG_GRID, (gx, rect.top, 1, rect.height))
        for gy in range(rect.top, rect.bottom, 20):
            pygame.draw.rect(surface, BG_GRID, (rect.left, gy, rect.width, 1))

        border_col = WHITE if flash > 0 else (GREEN_NEON if ready else ch["color"])
        pygame.draw.rect(surface, border_col, rect, 4)
        for ac_x, ac_y in [(rect.left,rect.top),(rect.right-4,rect.top),
                            (rect.left,rect.bottom-4),(rect.right-4,rect.bottom-4)]:
            pygame.draw.rect(surface, WHITE, (ac_x, ac_y, 4, 4))

        lbl = f_sm.render(label, False, WHITE)
        surface.blit(lbl, (rect.centerx - lbl.get_width()//2, rect.top + 10))

        bob       = int(3 * math.sin(math.radians(self.anim)))
        # Caixa fixa do retrato — sempre desenhada com o mesmo tamanho em
        # todos os personagens (a imagem é centralizada e bottom-aligned).
        BOX_W, BOX_H = 130, 130
        portrait  = get_portrait(ch.get("portrait"), size=(BOX_W, BOX_H))
        box_x     = rect.centerx - BOX_W // 2
        box_y     = rect.top + 28 + bob

        if portrait is not None:
            pw, ph = portrait.get_size()
            # Centraliza horizontal; alinha pela base
            ptx = box_x + (BOX_W - pw) // 2
            pty = box_y + (BOX_H - ph)
            halo = pygame.Surface((BOX_W + 24, BOX_H + 24), pygame.SRCALPHA)
            pygame.draw.rect(halo, (*ch["color"], 70),
                             (0, 0, BOX_W + 24, BOX_H + 24))
            surface.blit(halo, (box_x - 12, box_y - 12))
            surface.blit(portrait, (ptx, pty))
            # Moldura sempre na CAIXA fixa, não na imagem
            pygame.draw.rect(surface, ch["color"], (box_x, box_y, BOX_W, BOX_H), 3)
            pygame.draw.rect(surface, WHITE,        (box_x, box_y, BOX_W, BOX_H), 1)
            for cx, cy in [(box_x-2, box_y-2), (box_x+BOX_W-2, box_y-2),
                           (box_x-2, box_y+BOX_H-2), (box_x+BOX_W-2, box_y+BOX_H-2)]:
                pygame.draw.rect(surface, WHITE, (cx, cy, 4, 4))
            arrow_y = box_y + BOX_H // 2
        else:
            spr_y = rect.top + 110 + bob
            halo  = pygame.Surface((80, 80), pygame.SRCALPHA)
            pygame.draw.ellipse(halo, (*ch["color"], 45), (0, 0, 80, 80))
            surface.blit(halo, (rect.centerx - 40, spr_y - 40))
            draw_pixel_sprite(surface, rect.centerx, spr_y, ch["sprite"], scale=2)
            arrow_y = spr_y

        name_col = YELLOW if flash > 0 else ch["light"]
        nm   = f_md.render(ch["name"], False, name_col)
        nm_s = f_md.render(ch["name"], False, PIXEL_SHADOW)
        ny   = rect.top + 168
        surface.blit(nm_s, (rect.centerx - nm.get_width()//2 + 2, ny + 2))
        surface.blit(nm,   (rect.centerx - nm.get_width()//2,     ny))

        if not ready:
            for arrow_txt, ax in [("<", rect.left+8), (">", rect.right-22)]:
                at = f_md.render(arrow_txt, False, ch["color"])
                surface.blit(at, (ax, arrow_y - at.get_height()//2))
        draw_ability_tooltip(surface, ch["name"], rect, f_sm)
        st_rect = pygame.Rect(rect.left+8, rect.bottom-38, rect.width-16, 28)
        if ready:
            pygame.draw.rect(surface, (0, 80, 20), st_rect)
            pygame.draw.rect(surface, GREEN_NEON,  st_rect, 2)
            st = f_sm.render("READY!", False, GREEN_NEON)
        else:
            pygame.draw.rect(surface, (40, 40, 60), st_rect)
            pygame.draw.rect(surface, GRAY,         st_rect, 2)
            blink = (self.timer // self.BLINK) % 2 == 0
            st = f_sm.render("PRESS W / UP" if blink else "TO CONFIRM", False, GRAY)
        surface.blit(st, (rect.centerx - st.get_width()//2, st_rect.top +6))

    def _dots(self, surface, panel_cx, dot_y, sel_idx):
        gap   = 20
        total = len(CHARACTERS) * gap
        sx    = panel_cx - total // 2
        for i, ch in enumerate(CHARACTERS):
            dx  = sx + i * gap
            col = ch["color"] if i == sel_idx else DARK_GRAY
            pygame.draw.rect(surface, col,   (dx, dot_y, 14, 14))
            if i == sel_idx:
                pygame.draw.rect(surface, WHITE, (dx, dot_y, 14, 14), 2)

    def draw(self, surface, f_sm, f_md, f_lg):
        surface.fill(BG_DARK)
        for gx in range(0, SCREEN_W, 40):
            pygame.draw.rect(surface, BG_GRID, (gx, 0, 1, SCREEN_H))
        for gy in range(0, SCREEN_H, 40):
            pygame.draw.rect(surface, BG_GRID, (0, gy, SCREEN_W, 1))

        pygame.draw.rect(surface, BG_MID,  (0, 0, SCREEN_W, 52))
        pygame.draw.rect(surface, YELLOW,  (0, 50, SCREEN_W, 3))

        title   = f_lg.render("SELECT  YOUR  CHAMPION", False, YELLOW)
        title_s = f_lg.render("SELECT  YOUR  CHAMPION", False, PIXEL_SHADOW)
        tx = SCREEN_W//2 - title.get_width()//2
        surface.blit(title_s, (tx+3, 12))
        surface.blit(title,   (tx,   9))

        vs   = f_lg.render("VS", False, RED)
        vx   = SCREEN_W//2 - vs.get_width()//2
        vy   = SCREEN_H//2 - vs.get_height()//2 + 10
        vbox = pygame.Rect(vx-14, vy-8, vs.get_width()+28, vs.get_height()+16)
        pygame.draw.rect(surface, (50, 0, 0), vbox)
        pygame.draw.rect(surface, RED,        vbox, 3)
        pygame.draw.rect(surface, (255, 80, 80), (vbox.left+3, vbox.top+3, vbox.width-6, 2))
        surface.blit(vs, (vx, vy))

        PW, PH = 340, 240
        PY      = 68
        p1_rect = pygame.Rect(30, PY, PW, PH)
        p2_rect = pygame.Rect(SCREEN_W-30-PW, PY, PW, PH)

        self._panel(surface, p1_rect, self.p1_idx, "PLAYER 1", self.p1_ready, self.p1_flash, f_sm, f_md)
        self._panel(surface, p2_rect, self.p2_idx, "PLAYER 2", self.p2_ready, self.p2_flash, f_sm, f_md)

        self._dots(surface, p1_rect.centerx, p1_rect.bottom+12, self.p1_idx)
        self._dots(surface, p2_rect.centerx, p2_rect.bottom+12, self.p2_idx)

        bottom_y = SCREEN_H - 36
        if self.p1_ready and self.p2_ready:
            if (self.timer // 26) % 2 == 0:
                go = f_md.render("PRESS  ENTER  TO  FIGHT!", False, YELLOW)
                surface.blit(go, (SCREEN_W//2 - go.get_width()//2, bottom_y))
        else:
            hint = f_sm.render("R = RESET SELECTION", False, DARK_GRAY)
            surface.blit(hint, (SCREEN_W//2 - hint.get_width()//2, bottom_y+6))

        pygame.draw.rect(surface, YELLOW, (4, 4, SCREEN_W-8, SCREEN_H-8), 3)
        surface.blit(get_scanline_surf(), (0, 0))


# ============================================================
#  GAME STATE
# ============================================================
class GameState:
    MAX_SCORE   = 5
    RESET_DELAY = 90

    def __init__(self, p1_idx=0, p2_idx=1):
        self.p1_idx   = p1_idx
        self.p2_idx   = p2_idx
        c1 = CHARACTERS[p1_idx]
        c2 = CHARACTERS[p2_idx]
        self.player1  = Player(200, GROUND_Y - Player.HEIGHT, c1, CONTROLS_P1, True)
        self.player2  = Player(750, GROUND_Y - Player.HEIGHT, c2, CONTROLS_P2, False)
        self.ball     = Ball(SCREEN_W//2, GROUND_Y - 200)
        self.reset_timer = 0
        self.game_over   = False
        self.winner      = None
        self.particles   = []
        self.flash       = 0
        self.goal_by     = None
        # Efeitos visuais das habilidades novas
        self.sabor_timer  = 0     # Toguro: texto "SABOR" na tela
        self.claw_timer   = 0     # Raposão: garra arranhando a tela
        self.claw_facing_right = True
        self._field      = self._make_field()

    # ── Field surface ──────────────────────────────────────────
    def _make_field(self):
        surf = pygame.Surface((SCREEN_W, SCREEN_H))

        # ─── Céu / fundo do estádio (gradiente) ────────────────
        sky_h = 50
        for y in range(sky_h):
            t = y / sky_h
            r = int(8  + 14 * t)
            g = int(8  + 18 * t)
            b = int(28 + 38 * t)
            pygame.draw.line(surf, (r, g, b), (0, y), (SCREEN_W, y))

        # Estrelinhas no céu
        rng = random.Random(1337)   # determinístico para não tremer
        for _ in range(70):
            sx = rng.randint(0, SCREEN_W-1)
            sy = rng.randint(0, sky_h-1)
            sb = rng.randint(120, 220)
            pygame.draw.rect(surf, (sb, sb, sb), (sx, sy, 1, 1))

        # ─── Refletores (estádio) ──────────────────────────────
        for lx in [80, 250, 500, 750, 920]:
            pygame.draw.rect(surf, (40, 40, 55), (lx-2, sky_h, 4, 10))
            pygame.draw.rect(surf, (55, 60, 78), (lx-22, sky_h - 8, 44, 10))
            pygame.draw.rect(surf, (90, 95, 115),(lx-22, sky_h - 8, 44, 2))
            for li in range(4):
                pygame.draw.rect(surf, (255, 250, 200),
                                 (lx - 19 + li*9, sky_h - 6, 7, 4))
            # Brilho difuso
            glow = pygame.Surface((110, 80), pygame.SRCALPHA)
            for r in range(40, 0, -2):
                a = int(70 * (r / 40))
                pygame.draw.circle(glow, (255, 245, 180, a // 5), (55, 35), r)
            surf.blit(glow, (lx - 55, sky_h - 30))

        # ─── Arquibancada em 3 níveis ──────────────────────────
        crowd_top = sky_h + 12
        crowd_bot = GROUND_Y - GOAL_H - 30
        tier_h    = (crowd_bot - crowd_top) // 3

        crowd_palette = [
            (210, 60, 60), (60, 80, 210), (230, 200, 50),
            (60, 180, 60), (220, 220, 220), (180, 80, 200),
            (40, 40, 40), (210, 110, 30), (40, 200, 220),
        ]
        for tier in range(3):
            ty1 = crowd_top + tier * tier_h
            ty2 = ty1 + tier_h - 5
            shade = 0.5 + 0.18 * tier
            tier_bg = (int(20*shade), int(20*shade), int(48*shade))
            pygame.draw.rect(surf, tier_bg, (0, ty1, SCREEN_W, tier_h - 5))

            for cx in range(0, SCREEN_W, 5):
                for cy in range(ty1+2, ty2-1, 4):
                    if rng.random() > 0.32:
                        base = crowd_palette[rng.randint(0, len(crowd_palette)-1)]
                        fade = 0.45 + 0.18 * tier
                        c = tuple(int(v * fade) for v in base)
                        pygame.draw.rect(surf, c, (cx, cy, 3, 2))
            pygame.draw.rect(surf, (3, 3, 10), (0, ty2, SCREEN_W, 4))

        # ─── Placas de publicidade (cima do campo) ─────────────
        ad_y = crowd_bot - 4
        ad_h = 22
        pygame.draw.rect(surf, (5, 5, 15), (0, ad_y, SCREEN_W, ad_h))
        ad_palette = [(220, 50, 50), (50, 100, 220), (240, 200, 0),
                      (50, 180, 80), (180, 80, 180), (210, 110, 30),
                      (40, 200, 220), (240, 240, 240)]
        ad_count = 8
        ad_w = SCREEN_W // ad_count
        for i in range(ad_count):
            ax = i * ad_w
            ac = ad_palette[i % len(ad_palette)]
            pygame.draw.rect(surf, ac, (ax+2, ad_y+3, ad_w-4, ad_h-6))
            pygame.draw.rect(surf, (255, 255, 255, 80),
                             (ax+2, ad_y+3, ad_w-4, 2))

        # ─── Gramado (verde vivo, sem listras) ─────────────────
        field_top   = ad_y + ad_h
        GRASS_BASE  = (54, 175, 78)
        GRASS_OUT   = (40, 150, 62)        # faixa "fora do campo" (abaixo da linha de fundo)

        pygame.draw.rect(surf, GRASS_BASE,
                         (0, field_top, SCREEN_W, SCREEN_H - field_top))

        # Faixa um pouco mais escura abaixo da linha de fundo
        pygame.draw.rect(surf, GRASS_OUT,
                         (0, GROUND_Y + 4, SCREEN_W, SCREEN_H - GROUND_Y - 4))

        # Textura sutil (pontinhos discretos)
        for _ in range(900):
            gx = rng.randint(0, SCREEN_W - 1)
            gy = rng.randint(field_top, SCREEN_H - 1)
            gc = rng.choice([(48, 165, 72), (62, 188, 88),
                             (52, 172, 76), (44, 155, 65)])
            pygame.draw.rect(surf, gc, (gx, gy, 2, 2))

        # ─── Goleiras estilo wireframe ─────────────────────────
        self._draw_goal(surf, is_left=True,  rng=rng)
        self._draw_goal(surf, is_left=False, rng=rng)

        return surf

    def _draw_goal(self, surf, is_left, rng=None):
        """Goleira aberta com travessão, traves e mesh em branco."""
        if is_left:
            front_x = GOAL_W                 # poste frontal (lado do campo)
            back_x  = 4                      # poste do fundo (borda da tela)
        else:
            front_x = SCREEN_W - GOAL_W
            back_x  = SCREEN_W - 4

        f_top = (front_x, GOAL_Y)
        f_bot = (front_x, GROUND_Y)
        b_top = (back_x,  GOAL_Y + DEPTH_TOP)
        b_bot = (back_x,  GROUND_Y - 2)

        NET_LIGHT  = (245, 248, 255)
        NET_SHADOW = (170, 180, 200)
        POST_FILL  = (250, 250, 252)
        POST_EDGE  = (140, 150, 175)

        # ── Sombra leve no piso do gol (gramado mais escuro) ──
        floor_poly = [
            (f_bot[0], GROUND_Y - 4),
            (b_bot[0], b_bot[1] - 4),
            (b_bot[0], b_bot[1] + 6),
            (f_bot[0], GROUND_Y + 6),
        ]
        pygame.draw.polygon(surf, (35, 130, 55), floor_poly)

        # ── Mesh interna (rede aberta, em branco translúcido) ──
        net_surf = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)

        # Linhas verticais (do topo frontal -> topo traseiro, parametrizadas)
        n_v = 8
        for i in range(1, n_v):
            t = i / n_v
            tx = f_top[0] + (b_top[0] - f_top[0]) * t
            ty = f_top[1] + (b_top[1] - f_top[1]) * t
            bx = f_bot[0] + (b_bot[0] - f_bot[0]) * t
            by = f_bot[1] + (b_bot[1] - f_bot[1]) * t
            pygame.draw.line(net_surf, (*NET_SHADOW, 180),
                             (int(tx), int(ty)), (int(bx), int(by)), 1)

        # Linhas horizontais (parametrizadas em altura)
        n_h = 10
        for i in range(1, n_h):
            t = i / n_h
            ly = f_top[1] + (f_bot[1] - f_top[1]) * t
            ry = b_top[1] + (b_bot[1] - b_top[1]) * t
            pygame.draw.line(net_surf, (*NET_SHADOW, 180),
                             (front_x, int(ly)), (back_x, int(ry)), 1)

        surf.blit(net_surf, (0, 0))

        # ── Linhas-guia 3D (topo e base do gol, mais visíveis) ──
        pygame.draw.line(surf, NET_LIGHT, f_top, b_top, 2)
        pygame.draw.line(surf, NET_LIGHT, f_bot, b_bot, 2)

        # ── Travessão frontal (barra horizontal grossa) ────────
        cb_h = 8
        pygame.draw.rect(surf, POST_FILL,
                         (min(front_x, back_x) - 2 if not is_left else back_x,
                          GOAL_Y - cb_h // 2,
                          (GOAL_W if is_left else GOAL_W) + 4, cb_h))
        # (re-desenho mais simples: travessão como linha grossa)
        pygame.draw.line(surf, POST_FILL,
                         (f_top[0], GOAL_Y), (b_top[0], GOAL_Y + DEPTH_TOP), 5)
        pygame.draw.line(surf, POST_EDGE,
                         (f_top[0], GOAL_Y + 3),
                         (b_top[0], GOAL_Y + DEPTH_TOP + 3), 1)

        # ── Trave frontal (poste vertical destacado) ───────────
        if is_left:
            post_rect = pygame.Rect(front_x - POST_THICK, GOAL_Y,
                                    POST_THICK, GOAL_H)
            edge_x = front_x - 1
        else:
            post_rect = pygame.Rect(front_x, GOAL_Y, POST_THICK, GOAL_H)
            edge_x = front_x

        pygame.draw.rect(surf, POST_FILL, post_rect)
        pygame.draw.rect(surf, POST_EDGE, (edge_x, GOAL_Y, 1, GOAL_H))

        # ── Trave traseira (mais fina, na borda da tela) ───────
        if is_left:
            back_post = pygame.Rect(0, GOAL_Y + DEPTH_TOP, 4, GOAL_H - DEPTH_TOP + 2)
        else:
            back_post = pygame.Rect(SCREEN_W - 4, GOAL_Y + DEPTH_TOP, 4, GOAL_H - DEPTH_TOP + 2)
        pygame.draw.rect(surf, POST_FILL, back_post)

        # ── Tufos de grama na base do gol ──────────────────────
        if rng is not None:
            tuft_y = GROUND_Y - 2
            tuft_xs = range(min(front_x, back_x) - 6,
                            max(front_x, back_x) + 8, 8)
            for tx in tuft_xs:
                jitter = rng.randint(-2, 2)
                base_col = (28, 110, 45)
                tip_col  = (60, 200, 90)
                pygame.draw.rect(surf, base_col, (tx + jitter, tuft_y, 4, 6))
                pygame.draw.rect(surf, tip_col,  (tx + jitter + 1, tuft_y - 2, 2, 4))

    def check_goal(self):
        bx = self.ball.x
        # Gol só conta quando a bola passa COMPLETAMENTE da trave
        if bx + BALL_RADIUS <= GOAL_W:
            self.player2.score += 1
            self.goal_by = 2
            self.particles += burst(GOAL_W//2, (GOAL_Y+GROUND_Y)//2, CHARACTERS[self.p2_idx]["color"])
            self.flash = 22
            return True
        if bx - BALL_RADIUS >= SCREEN_W - GOAL_W:
            self.player1.score += 1
            self.goal_by = 1
            self.particles += burst(SCREEN_W-GOAL_W//2, (GOAL_Y+GROUND_Y)//2, CHARACTERS[self.p1_idx]["color"])
            self.flash = 22
            return True
        return False

    def update(self, keys):
        if self.game_over:
            return
        if self.flash > 0:
            self.flash -= 1

        if self.reset_timer > 0:
            self.reset_timer -= 1
            for p in self.particles: p.update()
            self.particles = [p for p in self.particles if p.alive]
            if self.reset_timer == 0:
                self._reset_positions()
            return

        self.player1.handle_input(keys)
        self.player2.handle_input(keys)
        self.player1.update()
        self.player2.update()

        # ── Habilidades especiais ─────────────────────────────
        # Decremento dos efeitos visuais (texto, garra)
        if self.sabor_timer > 0: self.sabor_timer -= 1
        if self.claw_timer  > 0: self.claw_timer  -= 1

        for player in (self.player1, self.player2):
            opp = self.player2 if player is self.player1 else self.player1

            if player.ability_timer > 0:
                player.ability_timer -= 1
                if player.ability_timer == 0:
                    player.ability_armed = False
                    if player.char_name == "RONY" and self.ball.locked_to is player:
                        # Final do show: bola é arremessada direto pro gol adversário
                        self.ball.locked_to = None
                        target_x = SCREEN_W - GOAL_W // 2 if player is self.player1 else GOAL_W // 2
                        target_y = GOAL_Y + GOAL_H * 0.5
                        dx       = target_x - self.ball.x
                        dy       = target_y - self.ball.y
                        dist     = max(math.hypot(dx, dy), 1.0)
                        speed_   = 30.0
                        self.ball.vx = dx / dist * speed_
                        self.ball.vy = dy / dist * speed_
                        self.ball.flame_timer = 180
                    elif self.ball.locked_to is player:     # Messi: solta bola
                        self.ball.locked_to = None
                        self.ball.vx = player.vx * 1.5 + (7 if player.facing_right else -7)
                        self.ball.vy = -8
                    if player.char_name == "HAALAND":
                        player.scale = 1.0
                    if player.char_name in ("YAMAL", "APODI"):
                        player.speed_mult = 1.0
                    if player.char_name == "CEDRIC":        # destrava controles
                        self.player1.invert_timer = 0
                        self.player2.invert_timer = 0
            elif player.char_name == "MESSI" and player.ability_armed:
                prect = player.collision_rect
                if math.hypot(self.ball.x - prect.centerx,
                              self.ball.y - prect.centery) < prect.width * 0.65 + BALL_RADIUS:
                    player.ability_timer = Player.ABILITY_DURATION
                    self.ball.locked_to  = player
            elif player.char_name == "HAALAND" and player.ability_armed:
                player.scale         = 1.5
                player.ability_timer = 300
                player.ability_armed = False
            elif player.char_name == "YAMAL" and player.ability_armed:
                player.speed_mult    = 2.0
                player.ability_timer = 300
                player.ability_armed = False
            elif player.char_name == "KANE" and player.ability_armed:
                player.ability_armed = False
                opp.float_timer = 240
                opp.vy          = -6

            # ─── HABILIDADES NOVAS ────────────────────────────
            elif player.char_name == "APODI" and player.ability_armed:
                # Apodi: muito mais rápido por 5 s
                player.speed_mult    = 3.0
                player.ability_timer = 300
                player.ability_armed = False
            elif player.char_name == "TOGURO" and player.ability_armed:
                # Toguro: aparece "SABOR" + oponente voa por 5 s
                player.ability_armed = False
                player.ability_timer = 300
                opp.float_timer = 300
                opp.vy          = -8
                self.sabor_timer = 120          # texto "SABOR" ~2 s
            elif player.char_name == "RAPOSAO" and player.ability_armed:
                # Raposão: garra na tela + oponente travado por 5 s
                player.ability_armed = False
                player.ability_timer = 300
                opp.frozen_timer = 300
                opp.vx           = 0
                self.claw_timer  = 90
                self.claw_facing_right = player.facing_right
            elif player.char_name == "MBAPPE" and player.ability_armed:
                # Mbappé: chapéu de ditador + bola teleporta para o pé
                player.ability_armed = False
                player.ability_timer = 180
                player.hat_timer     = 180
                # Bola "vai para o pé"
                fx, fy = player.foot_center
                self.ball.locked_to = None
                self.ball.x  = float(fx)
                self.ball.y  = float(fy - BALL_RADIUS)
                self.ball.vx = 0.0
                self.ball.vy = 0.0
            elif player.char_name == "RONY" and player.ability_armed:
                # Rony: voa, vira de ponta cabeça, gira 360°,
                # bola gruda nele e ao final é arremessada direto para o gol.
                player.ability_armed = False
                spin_dur             = 120          # 2 segundos de show
                player.ability_timer    = spin_dur
                player.upside_down_timer = spin_dur
                player.rony_spin_timer   = spin_dur
                # Tira do chão e fixa em altura elevada
                player.vx = 0.0
                player.vy = 0.0
                player.y  = float(GROUND_Y - Player.HEIGHT - 180)
                # Bola gruda nele
                self.ball.locked_to = player
                self.ball.vx = 0.0
                self.ball.vy = 0.0
            elif player.char_name == "PEDRO RAUL" and player.ability_armed:
                # Pedro Raul: bola sobe + super pulo + queda acelerada (5 s)
                player.ability_armed = False
                player.ability_timer = 300
                player.super_jump_timer = 300
                # Lança a bola para cima
                self.ball.locked_to = None
                self.ball.vy = -22
            elif player.char_name == "CEDRIC" and player.ability_armed:
                # Cedric: inverte controles de ambos por 5 s
                player.ability_armed = False
                player.ability_timer = 300
                self.player1.invert_timer = 300
                self.player2.invert_timer = 300

        # Colisão bola↔jogador agora roda dentro dos substeps do update,
        # evitando que a bola atravesse os personagens em chutes fortes.
        self.ball.update((self.player1, self.player2))

        self.player1.collide_with_player(self.player2)
        if self.ball.locked_to is None:
            hit1 = self.player1.try_kick_ball(self.ball)
            hit2 = self.player2.try_kick_ball(self.ball)
            # CR7: potencializa o próximo chute
            if hit1 and self.player1.char_name == "CR7" and self.player1.ability_armed:
                self.ball.vx *= 2.6
                self.ball.vy  = min(self.ball.vy * 2.0, -14)
                self.player1.ability_armed = False
                self.ball.flame_timer = 180
            if hit2 and self.player2.char_name == "CR7" and self.player2.ability_armed:
                self.ball.vx *= 2.6
                self.ball.vy  = min(self.ball.vy * 2.0, -14)
                self.player2.ability_armed = False
                self.ball.flame_timer = 180


        for p in self.particles: p.update()
        self.particles = [p for p in self.particles if p.alive]

        if self.check_goal():
            self.reset_timer = self.RESET_DELAY
            if self.player1.score >= self.MAX_SCORE:
                self.game_over = True; self.winner = 1
            elif self.player2.score >= self.MAX_SCORE:
                self.game_over = True; self.winner = 2

    def _reset_positions(self):
        self.player1.x, self.player1.y = 200.0, float(GROUND_Y - Player.HEIGHT)
        self.player1.vx = self.player1.vy = 0.0
        self.player2.x, self.player2.y = 750.0, float(GROUND_Y - Player.HEIGHT)
        self.player2.vx = self.player2.vy = 0.0
        self.ball.reset(SCREEN_W//2, GROUND_Y - 200)
        for p in (self.player1, self.player2):
            p.ability_armed = False
            p.ability_timer = 0
            p.scale         = 1.0
            p.float_timer   = 0
            p.speed_mult    = 1.0
            p.frozen_timer       = 0
            p.super_jump_timer   = 0
            p.upside_down_timer  = 0
            p.hat_timer          = 0
            p.invert_timer       = 0
            p.auto_goal_armed    = False
            p.rony_spin_timer    = 0
        self.sabor_timer = 0
        self.claw_timer  = 0
        self.goal_by = None

    def _hud(self, surface, f_sm, f_md, f_lg):
        c1 = CHARACTERS[self.p1_idx]
        c2 = CHARACTERS[self.p2_idx]

        sb_w, sb_h = 230, 48
        sbx = SCREEN_W//2 - sb_w//2
        sby = 6
        pygame.draw.rect(surface, BLACK,  (sbx,    sby,    sb_w,    sb_h))
        pygame.draw.rect(surface, YELLOW, (sbx,    sby,    sb_w,    sb_h), 3)
        pygame.draw.rect(surface, GOLD,   (sbx+3,  sby+3,  sb_w-6,  sb_h-6), 1)
        sc = f_lg.render(f"{self.player1.score}  :  {self.player2.score}", False, WHITE)
        surface.blit(sc, (SCREEN_W//2 - sc.get_width()//2, sby+7))

        for i, (ch, tag_x, player) in enumerate([
                (c1, 6,            self.player1),
                (c2, SCREEN_W-196, self.player2)]):
            tag = pygame.Rect(tag_x, sby, 190, sb_h)
            bg  = tuple(min(25, ch["color"][k]//7) for k in range(3))
            pygame.draw.rect(surface, bg,          tag)
            pygame.draw.rect(surface, ch["color"], tag, 3)
            nm  = f_sm.render(ch["name"], False, ch["light"])
            key_hint = "WASD+Q  [E=SKILL]" if i == 0 else "ARROWS+;  [SHF=SKILL]"
            ctr = f_sm.render(key_hint, False, GRAY)
            surface.blit(nm,  (tag.centerx - nm.get_width()//2,  tag.top+7))
            surface.blit(ctr, (tag.centerx - ctr.get_width()//2, tag.top+27))

        pip_y = sby + sb_h + 5
        for i in range(self.MAX_SCORE):
            px2 = sbx + 10 + i * 22
            col = c1["color"] if i < self.player1.score else DARK_GRAY
            pygame.draw.rect(surface, col,   (px2, pip_y, 16, 8))
            pygame.draw.rect(surface, WHITE, (px2, pip_y, 16, 8), 1)

        for i in range(self.MAX_SCORE):
            px2 = sbx + sb_w - 10 - (i+1)*22
            col = c2["color"] if i < self.player2.score else DARK_GRAY
            pygame.draw.rect(surface, col,   (px2, pip_y, 16, 8))
            pygame.draw.rect(surface, WHITE, (px2, pip_y, 16, 8), 1)

        # ── Barra de cooldown da habilidade ─────────────────
        ab_y = pip_y + 12
        for ab_player, ab_tag_x in ((self.player1, 6), (self.player2, SCREEN_W - 196)):
            ab_rect = pygame.Rect(ab_tag_x, ab_y, 190, 7)
            pygame.draw.rect(surface, DARK_GRAY, ab_rect)
            if ab_player.ability_timer > 0:
                ratio = ab_player.ability_timer / Player.ABILITY_DURATION
                ab_col = GOLD
            elif ab_player.ability_armed:
                ratio  = 1.0
                ab_col = YELLOW
            elif ab_player.ability_cooldown > 0:
                ratio  = 1.0 - ab_player.ability_cooldown / Player.ABILITY_COOLDOWN
                ab_col = GRAY
            else:
                ratio  = 1.0
                ab_col = GREEN_NEON
            fw = int(ab_rect.width * ratio)
            if fw > 0:
                pygame.draw.rect(surface, ab_col, (ab_rect.x, ab_rect.y, fw, ab_rect.height))
            pygame.draw.rect(surface, WHITE, ab_rect, 1)
            lbl = f_sm.render("SKILL", False, ab_col)
            surface.blit(lbl, (ab_rect.x + 2, ab_rect.bottom + 1))
            draw_ability_tooltip(surface, ab_player, ab_tag_x, f_sm)

        esc = f_sm.render("ESC=MENU", False, DARK_GRAY)
        surface.blit(esc, (SCREEN_W - esc.get_width() - 4, SCREEN_H - 18))

    # ── Efeito visual: "SABOR" gigante (Toguro) ─────────────────
    def _draw_sabor_effect(self, surface, f_xl):
        ratio = self.sabor_timer / 120.0
        # Escala gigante; ainda maior nos primeiros frames (impacto)
        scale = 4.0 + (1.0 - ratio) * 0.6
        alpha = int(255 * min(1.0, ratio * 2.5))

        txt = f_xl.render("SABOR", True, (255, 230, 0))
        tw, th = txt.get_size()
        sw, sh = max(1, int(tw * scale)), max(1, int(th * scale))
        scaled = pygame.transform.smoothscale(txt, (sw, sh))
        scaled.set_alpha(alpha)
        shadow = pygame.transform.smoothscale(
            f_xl.render("SABOR", True, BLACK), (sw, sh))
        shadow.set_alpha(alpha)
        x = SCREEN_W // 2 - sw // 2
        y = SCREEN_H // 2 - sh // 2
        # Fundo escurecido para destaque
        bg = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        bg.fill((0, 0, 0, int(120 * min(1.0, ratio * 2.5))))
        surface.blit(bg, (0, 0))
        surface.blit(shadow, (x + 10, y + 10))
        surface.blit(scaled, (x, y))

    # ── Efeito visual: garras arranhando a tela (Raposão) ──────
    def _draw_claw_effect(self, surface):
        ratio = self.claw_timer / 90.0
        alpha = int(255 * min(1.0, ratio * 2.0))
        progress = 1.0 - ratio    # 0..1 do movimento das garras
        layer    = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        # 4 listras de garra, espaçadas pela tela toda
        for i in range(4):
            cy_start = 90  + i * 100
            cy_end   = cy_start + 460
            cy       = int(cy_start + (cy_end - cy_start) * progress)
            if self.claw_facing_right:
                x_start, x_end = -200, SCREEN_W + 200
            else:
                x_start, x_end = SCREEN_W + 200, -200
            cx = int(x_start + (x_end - x_start) * progress)
            for j in range(3):
                dx = (j - 1) * 40
                length = 360
                col = (220, 20, 20, alpha)
                start = (cx + dx - length // 2, cy - length // 2)
                end   = (cx + dx + length // 2, cy + length // 2)
                pygame.draw.line(layer, col, start, end, 9)
                pygame.draw.line(layer, (255, 240, 240, alpha),
                                 start, end, 3)
        surface.blit(layer, (0, 0))

    def draw(self, surface, f_sm, f_md, f_lg):
        if self.flash > 0:
            fl  = pygame.Surface((SCREEN_W, SCREEN_H))
            fl.fill(WHITE)
            fl.set_alpha(min(210, self.flash * 10))

        surface.blit(self._field, (0, 0))
        for p in self.particles: p.draw(surface)

        self.player1.draw(surface)
        self.player2.draw(surface)
        self.ball.draw(surface)

        # Efeitos visuais das habilidades novas
        if self.claw_timer  > 0: self._draw_claw_effect(surface)
        if self.sabor_timer > 0: self._draw_sabor_effect(surface, f_xl=f_lg)

        self._hud(surface, f_sm, f_md, f_lg)

        if self.flash > 0:
            surface.blit(fl, (0, 0))

        if self.reset_timer > 0 and self.goal_by and not self.game_over:
            ch   = CHARACTERS[self.p1_idx if self.goal_by == 1 else self.p2_idx]
            gstr = "  GOAL!  "
            gw   = f_lg.size(gstr)[0] + 20
            gh   = f_lg.size(gstr)[1] + 18
            gx   = SCREEN_W//2 - gw//2
            gy   = SCREEN_H//2 - gh//2
            pygame.draw.rect(surface, PIXEL_SHADOW, (gx-4, gy-4, gw+8, gh+8))
            pygame.draw.rect(surface, YELLOW,       (gx, gy, gw, gh))
            pygame.draw.rect(surface, ch["color"],  (gx, gy, gw, gh), 4)
            gt  = f_lg.render(gstr, False, BLACK)
            surface.blit(gt, (SCREEN_W//2 - gt.get_width()//2, gy+9))
            who = f_sm.render(f"PLAYER {self.goal_by} SCORED!", False, ch["color"])
            surface.blit(who, (SCREEN_W//2 - who.get_width()//2, gy+gh+6))

        if self.game_over:
            ov = pygame.Surface((SCREEN_W, SCREEN_H))
            ov.fill(BG_DARK); ov.set_alpha(210)
            surface.blit(ov, (0, 0))

            ch  = CHARACTERS[self.p1_idx if self.winner==1 else self.p2_idx]
            box = pygame.Rect(SCREEN_W//2-300, SCREEN_H//2-110, 600, 220)
            pygame.draw.rect(surface, BLACK,       box)
            pygame.draw.rect(surface, ch["color"], box, 5)
            pygame.draw.rect(surface, YELLOW, (box.left+5, box.top+5, box.width-10, box.height-10), 2)

            winner_portrait = get_portrait(ch.get("portrait"), size=(96, 110))
            if winner_portrait is not None:
                px = box.left + 20
                py = box.centery - 55
                surface.blit(winner_portrait, (px, py))
                pygame.draw.rect(surface, ch["color"], (px, py, 96, 110), 3)
                pygame.draw.rect(surface, WHITE,       (px, py, 96, 110), 1)
            else:
                draw_pixel_sprite(surface, box.left+60, box.centery, ch["sprite"], scale=2)

            wt   = f_lg.render(f"PLAYER {self.winner} WINS!", False, YELLOW)
            wt_s = f_lg.render(f"PLAYER {self.winner} WINS!", False, PIXEL_SHADOW)
            surface.blit(wt_s, (SCREEN_W//2 - wt.get_width()//2+3, SCREEN_H//2-78))
            surface.blit(wt,   (SCREEN_W//2 - wt.get_width()//2,   SCREEN_H//2-82))

            cn = f_md.render(ch["name"], False, ch["light"])
            surface.blit(cn, (SCREEN_W//2 - cn.get_width()//2, SCREEN_H//2-22))

            # Trophy pixel
            tr_x, tr_y = box.right-65, box.centery-20
            for blk in [(tr_x-8,tr_y-22,16,18),(tr_x-14,tr_y-22,4,10),
                         (tr_x+10,tr_y-22,4,10),(tr_x-6,tr_y-4,12,4),
                         (tr_x-10,tr_y,20,6)]:
                pygame.draw.rect(surface, GOLD, blk)

            rt = f_sm.render("R = REMATCH     ESC = MENU", False, WHITE)
            surface.blit(rt, (SCREEN_W//2 - rt.get_width()//2, SCREEN_H//2+56))

        surface.blit(get_scanline_surf(), (0, 0))


# ============================================================
#  MAIN
# ============================================================
def main():
    pygame.init()
    # SCALED garante 1000x600 pixel-perfect mesmo em telas Retina/HiDPI
    screen = pygame.display.set_mode((SCREEN_W, SCREEN_H), pygame.SCALED | pygame.FULLSCREEN, vsync=1)
    pygame.display.set_caption("Copa Cabeça — jogo é jogo e treino é treino")
    clock  = pygame.time.Clock()

    f_sm, f_md, f_lg, f_xl = build_fonts()

    state = IntroState()

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()

            if isinstance(state, IntroState):
                if state.handle_event(event):
                    state = CharSelectState()

            elif isinstance(state, CharSelectState):
                new = state.handle_event(event)
                if new is not None:
                    state = new

            elif isinstance(state, GameState):
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        state = CharSelectState()
                    if event.key == pygame.K_r and state.game_over:
                        state = GameState(state.p1_idx, state.p2_idx)

        keys = pygame.key.get_pressed()

        if isinstance(state, IntroState):
            state.update()
            state.draw(screen, f_sm, f_md, f_lg, f_xl)

        elif isinstance(state, CharSelectState):
            state.update()
            state.draw(screen, f_sm, f_md, f_lg)

        elif isinstance(state, GameState):
            state.update(keys)
            state.draw(screen, f_sm, f_md, f_lg)

        pygame.display.flip()
        clock.tick(FPS)


if __name__ == "__main__":
    main()
