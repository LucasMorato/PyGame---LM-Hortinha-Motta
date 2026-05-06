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
PLAYER1_IMAGE_PATH = os.path.join(ASSETS_DIR, "player1.png")
PLAYER2_IMAGE_PATH = os.path.join(ASSETS_DIR, "player2.png")

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
GOAL_W = 30
GOAL_H = 200
GOAL_Y = GROUND_Y - GOAL_H

# ─── Controles ───────────────────────────────────────────────
CONTROLS_P1 = {"left": pygame.K_a, "right": pygame.K_d, "jump": pygame.K_w, "kick": pygame.K_q}
CONTROLS_P2 = {"left": pygame.K_LEFT, "right": pygame.K_RIGHT, "jump": pygame.K_UP, "kick": pygame.K_SEMICOLON}

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
    {"name": "RED KICK",  "color": RED,       "light": LIGHT_RED,
     "sprite": _spr(LIGHT_RED,          RED,            (160, 20, 20)),
     "image": PLAYER1_IMAGE_PATH},
    {"name": "TURBO",     "color": BLUE,      "light": LIGHT_BLUE,
     "sprite": _spr(LIGHT_BLUE,         BLUE,           (20, 40, 160)),
     "image": PLAYER2_IMAGE_PATH},
    {"name": "VOLT",      "color": (0,150,45), "light": GREEN_NEON,
     "sprite": _spr(GREEN_NEON,         (0, 130, 40),   (0, 90, 25)),
     "image": None},
    {"name": "BLAZE",     "color": ORANGE,    "light": (255,195,80),
     "sprite": _spr((255, 195, 80),     ORANGE,         (180, 70, 0)),
     "image": None},
    {"name": "SHADOW",    "color": PURPLE,    "light": (170,90,235),
     "sprite": _spr((170, 90, 235),     PURPLE,         (55, 5, 115)),
     "image": None},
    {"name": "ICE",       "color": CYAN,      "light": (195,235,255),
     "sprite": _spr((195, 235, 255),    CYAN,           (0, 140, 170)),
     "image": None},
]


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
    COLL_W_FACTOR = 0.50
    COLL_H_FACTOR = 0.75

    def __init__(self, x, y, char_data, controls, facing_right=True):
        self.x, self.y   = float(x), float(y)
        self.vx = self.vy = 0.0
        self.color        = char_data["color"]
        self.light_color  = char_data["light"]
        self.sprite_cols  = char_data["sprite"]
        self.controls     = controls
        self.facing_right = facing_right
        self.on_ground    = False
        self.kicking      = False
        self.kick_timer   = 0
        self.score        = 0
        self.image        = None

        ip = char_data.get("image")
        if ip and os.path.exists(ip):
            try:
                img = pygame.image.load(ip).convert_alpha()
                self.image = pygame.transform.smoothscale(img, (self.WIDTH, self.HEIGHT))
            except Exception:
                pass

    @property
    def rect(self):
        return pygame.Rect(self.x, self.y, self.WIDTH, self.HEIGHT)

    @property
    def collision_rect(self):
        cw = int(self.WIDTH  * self.COLL_W_FACTOR)
        ch = int(self.HEIGHT * self.COLL_H_FACTOR)
        return pygame.Rect(
            int(self.x + (self.WIDTH  - cw) / 2),
            int(self.y + (self.HEIGHT - ch)),
            cw, ch)

    @property
    def foot_center(self):
        fx = self.x + self.WIDTH * (0.7 if self.facing_right else 0.3)
        fy = self.y + self.HEIGHT * 0.85
        return (fx, fy)

    def _clamp_ground(self):
        if self.y + self.HEIGHT >= GROUND_Y:
            self.y = GROUND_Y - self.HEIGHT
            if self.vy > 0:
                self.vy = 0
            self.on_ground = True

    def handle_input(self, keys):
        if keys[self.controls["left"]]:
            self.vx = -self.SPEED
            self.facing_right = False
        elif keys[self.controls["right"]]:
            self.vx = self.SPEED
            self.facing_right = True
        else:
            self.vx *= 0.75

        if keys[self.controls["jump"]] and self.on_ground:
            self.vy = self.JUMP_FORCE
            self.on_ground = False

        if keys[self.controls["kick"]] and not self.kicking:
            self.kicking    = True
            self.kick_timer = self.KICK_DURATION

    def update(self):
        self.vy += GRAVITY
        self.x  += self.vx
        self.y  += self.vy
        self._clamp_ground()

        if self.x < GOAL_W:
            self.x = float(GOAL_W)
        if self.x + self.WIDTH > SCREEN_W - GOAL_W:
            self.x = float(SCREEN_W - GOAL_W - self.WIDTH)

        if self.kicking:
            self.kick_timer -= 1
            if self.kick_timer <= 0:
                self.kicking = False

    def try_kick_ball(self, ball):
        if not self.kicking:
            return
        fx, fy = self.foot_center
        dist = math.hypot(ball.x - fx, ball.y - fy)
        if dist < self.KICK_RADIUS + BALL_RADIUS:
            dist = max(dist, 1)
            dx = (ball.x - fx) / dist
            dy = (ball.y - fy) / dist
            ball.vx = dx * self.KICK_FORCE + (self.SPEED if self.facing_right else -self.SPEED)
            ball.vy = dy * self.KICK_FORCE - 2

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

    def draw(self, surface):
        x, y = int(self.x), int(self.y)
        w, h = self.WIDTH, self.HEIGHT
        t_k  = self.kick_timer / self.KICK_DURATION if self.kicking else 0.0

        if self.image:
            img = self.image if self.facing_right else pygame.transform.flip(self.image, True, False)
            surface.blit(img, (x, y))
        else:
            self._draw_retro(surface, x, y, w, h)

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
        self.angle = 0.0

    def update(self):
        self.vy    += GRAVITY * 0.50
        self.x     += self.vx
        self.y     += self.vy
        self.angle += self.vx * 1.5

        if self.y + BALL_RADIUS >= GROUND_Y:
            self.y  = GROUND_Y - BALL_RADIUS
            self.vy = -abs(self.vy) * self.BOUNCE
            self.vx *= self.FRICTION
            if abs(self.vy) < 1.2:
                self.vy = 0

        if self.y - BALL_RADIUS <= 0:
            self.y  = float(BALL_RADIUS)
            self.vy = abs(self.vy) * self.BOUNCE

        if self.x - BALL_RADIUS <= GOAL_W and self.y + BALL_RADIUS < GOAL_Y:
            self.x  = GOAL_W + BALL_RADIUS
            self.vx = abs(self.vx) * self.BOUNCE

        if self.x + BALL_RADIUS >= SCREEN_W - GOAL_W and self.y + BALL_RADIUS < GOAL_Y:
            self.x  = SCREEN_W - GOAL_W - BALL_RADIUS
            self.vx = -abs(self.vx) * self.BOUNCE

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

        # Title
        for txt_str, f, col, y_pos in [
            ("HEAD",   f_xl, YELLOW,     70),
            ("SOCCER", f_xl, WHITE,     150),
            ("2D",     f_lg, GREEN_NEON, 235),
        ]:
            t  = f.render(txt_str, False, col)
            ts = f.render(txt_str, False, PIXEL_SHADOW)
            ox = SCREEN_W // 2 - t.get_width() // 2
            surface.blit(ts, (ox + 4, y_pos + 4))
            surface.blit(t,  (ox,     y_pos))

        # Underbar
        soccer = f_xl.render("SOCCER", False, WHITE)
        bar_x  = SCREEN_W // 2 - soccer.get_width() // 2
        pygame.draw.rect(surface, GREEN_NEON, (bar_x, 150 + soccer.get_height() + 4, soccer.get_width(), 4))
        pygame.draw.rect(surface, YELLOW,     (bar_x + 4, 150 + soccer.get_height() + 9, soccer.get_width()-8, 2))

        ver = f_sm.render("v2.0  PIXEL EDITION", False, DARK_GRAY)
        surface.blit(ver, (SCREEN_W//2 - ver.get_width()//2, 268))

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

        bob   = int(4 * math.sin(math.radians(self.anim)))
        spr_y = rect.top + 110 + bob
        halo  = pygame.Surface((80, 80), pygame.SRCALPHA)
        pygame.draw.ellipse(halo, (*ch["color"], 45), (0, 0, 80, 80))
        surface.blit(halo, (rect.centerx - 40, spr_y - 40))
        draw_pixel_sprite(surface, rect.centerx, spr_y, ch["sprite"], scale=2)

        name_col = YELLOW if flash > 0 else ch["light"]
        nm  = f_md.render(ch["name"], False, name_col)
        nm_s = f_md.render(ch["name"], False, PIXEL_SHADOW)
        surface.blit(nm_s, (rect.centerx - nm.get_width()//2 + 2, rect.top + 192))
        surface.blit(nm,   (rect.centerx - nm.get_width()//2,     rect.top + 190))

        if not ready:
            for arrow_txt, ax in [("<", rect.left+8), (">", rect.right-22)]:
                at = f_md.render(arrow_txt, False, ch["color"])
                surface.blit(at, (ax, spr_y - at.get_height()//2))

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
        surface.blit(st, (rect.centerx - st.get_width()//2, st_rect.top + 6))

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

        title   = f_lg.render("SELECT  YOUR  FIGHTER", False, YELLOW)
        title_s = f_lg.render("SELECT  YOUR  FIGHTER", False, PIXEL_SHADOW)
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
        self._field      = self._make_field()

    # ── Field surface ──────────────────────────────────────────
    def _make_field(self):
        surf = pygame.Surface((SCREEN_W, SCREEN_H))
        surf.fill(STADIUM_COL)

        crowd_h = GROUND_Y - GOAL_H - 20
        for row in range(0, crowd_h, 8):
            for col in range(0, SCREEN_W, 8):
                shade = random.choice([CROWD_COL, BG_MID, (25, 25, 60)])
                pygame.draw.rect(surf, shade, (col, row, 7, 7))

        pygame.draw.rect(surf, (15, 15, 40), (0, 0, SCREEN_W, 30))

        for lx in [60, 200, 420, 580, 800, 940]:
            pygame.draw.rect(surf, (70, 70, 55),     (lx-4, 8,  8, 22))
            pygame.draw.ellipse(surf, (255, 240, 160), (lx-22, 4, 44, 18))

        field_top = GROUND_Y - GOAL_H - 20
        sw        = 100
        for i in range(0, SCREEN_W, sw*2):
            pygame.draw.rect(surf, FIELD_LITE, (i,    field_top, sw, SCREEN_H - field_top))
            pygame.draw.rect(surf, FIELD_DARK, (i+sw, field_top, sw, SCREEN_H - field_top))

        lc = LINE_COL
        pygame.draw.rect(surf, lc, (SCREEN_W//2-1, GROUND_Y-GOAL_H, 3, GOAL_H+120))
        pygame.draw.circle(surf, lc, (SCREEN_W//2, GROUND_Y+50), 60, 2)
        pygame.draw.rect(surf, lc,   (SCREEN_W//2-4, GROUND_Y+46, 8, 8))
        pygame.draw.rect(surf, lc,   (GOAL_W, GROUND_Y, SCREEN_W-GOAL_W*2, 3))
        for side_x in [GOAL_W, SCREEN_W-GOAL_W-110]:
            pygame.draw.rect(surf, lc, (side_x, GROUND_Y-80, 110, 80), 2)

        for left in (True, False):
            gx  = 0 if left else SCREEN_W - GOAL_W
            net = pygame.Surface((GOAL_W, GOAL_H), pygame.SRCALPHA)
            net.fill((20, 20, 40, 190))
            for ry in range(0, GOAL_H, 14):
                pygame.draw.rect(net, (*NET_COL, 160), (0, ry, GOAL_W, 1))
            for rx in range(0, GOAL_W, 7):
                pygame.draw.rect(net, (*NET_COL, 160), (rx, 0, 1, GOAL_H))
            surf.blit(net, (gx, GOAL_Y))
            pygame.draw.rect(surf, GOAL_SILVER, (gx, GOAL_Y,     GOAL_W, 5))
            pygame.draw.rect(surf, GOAL_DARK,   (gx, GOAL_Y+5,   GOAL_W, 2))
            pw  = 5
            px2 = GOAL_W - pw if left else 0
            pygame.draw.rect(surf, GOAL_SILVER, (gx+px2, GOAL_Y, pw, GOAL_H))
            pygame.draw.rect(surf, GOAL_DARK,   (gx+px2+(pw-2 if left else 0), GOAL_Y, 2, GOAL_H))
            pygame.draw.rect(surf, GOAL_SILVER, (gx, GROUND_Y-5, GOAL_W, 5))

        return surf

    def check_goal(self):
        bx, by = self.ball.x, self.ball.y
        if bx - BALL_RADIUS <= GOAL_W and by + BALL_RADIUS >= GOAL_Y:
            self.player2.score += 1
            self.goal_by = 2
            self.particles += burst(GOAL_W+35, (GOAL_Y+GROUND_Y)//2, CHARACTERS[self.p2_idx]["color"])
            self.flash = 22
            return True
        if bx + BALL_RADIUS >= SCREEN_W - GOAL_W and by + BALL_RADIUS >= GOAL_Y:
            self.player1.score += 1
            self.goal_by = 1
            self.particles += burst(SCREEN_W-GOAL_W-35, (GOAL_Y+GROUND_Y)//2, CHARACTERS[self.p1_idx]["color"])
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
        self.ball.update()

        self.player1.collide_with_player(self.player2)
        self.ball.collide_with_player(self.player1)
        self.ball.collide_with_player(self.player2)
        self.player1.try_kick_ball(self.ball)
        self.player2.try_kick_ball(self.ball)

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

        for i, (ch, tag_x) in enumerate([(c1, 6), (c2, SCREEN_W-196)]):
            tag = pygame.Rect(tag_x, sby, 190, sb_h)
            bg  = tuple(min(25, ch["color"][k]//7) for k in range(3))
            pygame.draw.rect(surface, bg,          tag)
            pygame.draw.rect(surface, ch["color"], tag, 3)
            nm  = f_sm.render(ch["name"], False, ch["light"])
            ctr = f_sm.render("WASD+Q" if i==0 else "ARROWS+;", False, GRAY)
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

        esc = f_sm.render("ESC=MENU", False, DARK_GRAY)
        surface.blit(esc, (SCREEN_W - esc.get_width() - 4, SCREEN_H - 18))

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
    screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
    pygame.display.set_caption("HEAD SOCCER 2D — PIXEL EDITION")
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