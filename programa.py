import os
import pygame
import sys
import math

# ============================================================
#  CONFIGURAÇÕES GERAIS
# ============================================================
SCREEN_W, SCREEN_H = 1000, 600
FPS = 60
GRAVITY = 0.5
GROUND_Y = 480
BALL_RADIUS = 30

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
PLAYER1_IMAGE_PATH = os.path.join(ASSETS_DIR, "player1.png")
PLAYER2_IMAGE_PATH = os.path.join(ASSETS_DIR, "player2.png")

# ─── Cores ──────────────────────────────────────────────────
WHITE      = (255, 255, 255)
BLACK      = (  0,   0,   0)
SKY_BLUE   = (135, 206, 235)
GREEN      = ( 34, 139,  34)
DARK_GREEN = ( 20, 100,  20)
YELLOW     = (255, 220,   0)
RED        = (220,  40,  40)
BLUE       = ( 40,  80, 220)
LIGHT_RED  = (255, 120, 120)
LIGHT_BLUE = (120, 160, 255)
GRAY       = (160, 160, 160)
DARK_GRAY  = ( 80,  80,  80)
ORANGE     = (255, 140,   0)
NET_COLOR  = (200, 200, 200)
POST_COLOR = (230, 230, 230)

# ─── Goleiras ───────────────────────────────────────────────
GOAL_W  = 30
GOAL_H  = 200
GOAL1_X = 0
GOAL2_X = SCREEN_W - GOAL_W
GOAL_Y  = GROUND_Y - GOAL_H

# ─── Controles ──────────────────────────────────────────────
CONTROLS_P1 = {
    "left":  pygame.K_a,
    "right": pygame.K_d,
    "jump":  pygame.K_w,
    "kick":  pygame.K_q,
}
CONTROLS_P2 = {
    "left":  pygame.K_LEFT,
    "right": pygame.K_RIGHT,
    "jump":  pygame.K_UP,
    "kick":  pygame.K_SEMICOLON,
}


# ============================================================
#  CLASSE JOGADOR
# ============================================================
class Player:
    WIDTH  = 50 * 1.5 * 2
    HEIGHT = 70 * 1.5
    SPEED  = 4.2
    JUMP_FORCE   = -13   # pulo mais alto
    KICK_RADIUS  = 90
    KICK_FORCE   = 8
    KICK_DURATION = 15

    def __init__(self, x, y, color, light_color, controls, facing_right=True, image_path=None):
        self.x = float(x)
        self.y = float(y)
        self.vx = 0.0
        self.vy = 0.0
        self.color = color
        self.light_color = light_color
        self.controls = controls
        self.facing_right = facing_right
        self.on_ground = False
        self.kicking = False
        self.kick_timer = 0
        self.score = 0
        self.image = None

        if image_path and os.path.exists(image_path):
            try:
                img = pygame.image.load(image_path).convert_alpha()
                self.image = pygame.transform.smoothscale(img, (self.WIDTH, self.HEIGHT))
            except Exception:
                self.image = None

    @property
    def rect(self):
        return pygame.Rect(self.x, self.y, self.WIDTH, self.HEIGHT)

    @property
    def center(self):
        return (self.x + self.WIDTH / 2, self.y + self.HEIGHT / 2)

    @property
    def foot_center(self):
        foot_x = self.x + self.WIDTH * (0.7 if self.facing_right else 0.3)
        foot_y = self.y + self.HEIGHT * 0.85
        return (foot_x, foot_y)

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
            self.kicking = True
            self.kick_timer = self.KICK_DURATION

    def update(self):
        self.vy += GRAVITY
        self.x += self.vx
        self.y += self.vy

        if self.y + self.HEIGHT >= GROUND_Y:
            self.y = GROUND_Y - self.HEIGHT
            self.vy = 0
            self.on_ground = True

        if self.x < GOAL_W:
            self.x = GOAL_W
        if self.x + self.WIDTH > SCREEN_W - GOAL_W:
            self.x = SCREEN_W - GOAL_W - self.WIDTH

        if self.kicking:
            self.kick_timer -= 1
            if self.kick_timer <= 0:
                self.kicking = False

    def try_kick_ball(self, ball):
        if not self.kicking:
            return

        fx, fy = self.foot_center
        bx, by = ball.x, ball.y
        dist = math.hypot(bx - fx, by - fy)

        if dist < self.KICK_RADIUS + BALL_RADIUS:
            if dist == 0:
                dist = 1
            dx = (bx - fx) / dist
            dy = (by - fy) / dist
            ball.vx = dx * self.KICK_FORCE + (self.SPEED if self.facing_right else -self.SPEED)
            ball.vy = dy * self.KICK_FORCE - 2

    def collide_with_player(self, other):
        r1 = self.rect
        r2 = other.rect
        if not r1.colliderect(r2):
            return
        overlap_x = (r1.right - r2.left) if self.x < other.x else (r2.right - r1.left)
        push = overlap_x / 2
        if self.x < other.x:
            self.x -= push
            other.x += push
        else:
            self.x += push
            other.x -= push

    def draw(self, surface):
        x, y = int(self.x), int(self.y)
        w, h = self.WIDTH, self.HEIGHT

        if self.image:
            img = self.image if self.facing_right else pygame.transform.flip(self.image, True, False)
            surface.blit(img, (x, y))
        else:
            pygame.draw.rect(surface, self.color, (x + 10, y + 30, w - 20, h - 30), border_radius=8)
            head_r = 26
            head_cx = x + w // 2
            head_cy = y + 26
            pygame.draw.circle(surface, self.light_color, (head_cx, head_cy), head_r)
            pygame.draw.circle(surface, self.color, (head_cx, head_cy), head_r, 3)
            eye_offset = 8 if self.facing_right else -8
            pygame.draw.circle(surface, BLACK, (head_cx + eye_offset, head_cy - 4), 5)
            pygame.draw.circle(surface, WHITE, (head_cx + eye_offset + 2, head_cy - 6), 2)
            pygame.draw.rect(surface, self.color, (x + 10, y + h - 22, 14, 22), border_radius=4)
            pygame.draw.rect(surface, self.color, (x + w - 24, y + h - 22, 14, 22), border_radius=4)
            if self.kicking:
                kick_x = int(self.foot_center[0])
                kick_y = int(self.foot_center[1])
                pygame.draw.circle(surface, YELLOW, (kick_x, kick_y), 18, 4)


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
        self.x = float(x)
        self.y = float(y)
        self.vx = 0.0
        self.vy = 0.0
        self.angle = 0.0

    def update(self):
        self.vy += GRAVITY * 0.50  # queda mais lenta
        self.x += self.vx
        self.y += self.vy
        self.angle += self.vx * 1.5

        if self.y + BALL_RADIUS >= GROUND_Y:
            self.y = GROUND_Y - BALL_RADIUS
            self.vy = -abs(self.vy) * self.BOUNCE
            self.vx *= self.FRICTION
            if abs(self.vy) < 1.2:
                self.vy = 0

        if self.y - BALL_RADIUS <= 0:
            self.y = BALL_RADIUS
            self.vy = abs(self.vy) * self.BOUNCE

        if self.x - BALL_RADIUS <= GOAL_W:
            if self.y + BALL_RADIUS < GOAL_Y:
                self.x = GOAL_W + BALL_RADIUS
                self.vx = abs(self.vx) * self.BOUNCE

        if self.x + BALL_RADIUS >= SCREEN_W - GOAL_W:
            if self.y + BALL_RADIUS < GOAL_Y:
                self.x = SCREEN_W - GOAL_W - BALL_RADIUS
                self.vx = -abs(self.vx) * self.BOUNCE

    def collide_with_player(self, player):
        rect = player.rect

        closest_x = max(rect.left, min(self.x, rect.right))
        closest_y = max(rect.top, min(self.y, rect.bottom))

        dx = self.x - closest_x
        dy = self.y - closest_y
        dist_sq = dx * dx + dy * dy

        if dist_sq == 0:
            if not rect.collidepoint(self.x, self.y):
                return

            distances = {
                "left": self.x - rect.left,
                "right": rect.right - self.x,
                "top": self.y - rect.top,
                "bottom": rect.bottom - self.y,
            }
            side = min(distances, key=distances.get)

            if side == "left":
                nx, ny = -1, 0
                overlap = BALL_RADIUS + distances["left"]
            elif side == "right":
                nx, ny = 1, 0
                overlap = BALL_RADIUS + distances["right"]
            elif side == "top":
                nx, ny = 0, -1
                overlap = BALL_RADIUS + distances["top"]
            else:
                nx, ny = 0, 1
                overlap = BALL_RADIUS + distances["bottom"]
        elif dist_sq < BALL_RADIUS * BALL_RADIUS:
            dist = math.sqrt(dist_sq)
            nx = dx / dist
            ny = dy / dist
            overlap = BALL_RADIUS - dist
        else:
            return

        self.x += nx * overlap
        self.y += ny * overlap

        rel_vx = self.vx - player.vx
        rel_vy = self.vy - player.vy
        dot = rel_vx * nx + rel_vy * ny
        if dot < 0:
            self.vx -= dot * nx * 1.4
            self.vy -= dot * ny * 1.4

    def draw(self, surface):
        ix, iy = int(self.x), int(self.y)
        r = BALL_RADIUS

        if self.image:
            rotated = pygame.transform.rotate(self.image, -self.angle)
            rect = rotated.get_rect(center=(ix, iy))
            surface.blit(rotated, rect)
        else:
            pygame.draw.circle(surface, WHITE, (ix, iy), r)
            pygame.draw.circle(surface, BLACK, (ix, iy), r, 3)

            center_points = []
            for i in range(5):
                a = math.radians(self.angle + 18 + i * 72)
                rr = r * 0.38
                center_points.append((
                    ix + int(rr * math.cos(a)),
                    iy + int(rr * math.sin(a))
                ))
            pygame.draw.polygon(surface, DARK_GRAY, center_points)

            for i in range(5):
                a = math.radians(self.angle + i * 72)
                cx = ix + int(r * 0.58 * math.cos(a))
                cy = iy + int(r * 0.58 * math.sin(a))

                patch = []
                for j in range(5):
                    aa = math.radians(self.angle * 0.25 + i * 72 + 36 + j * 72)
                    patch.append((
                        cx + int(8 * math.cos(aa)),
                        cy + int(8 * math.sin(aa))
                    ))
                pygame.draw.polygon(surface, BLACK, patch)
# ============================================================
#  ESTADO DO JOGO
# ============================================================
class GameState:
    MAX_SCORE = 5
    RESET_DELAY = 90

    def __init__(self, p1_choice=0, p2_choice=1):
        self.p1_choice = p1_choice
        self.p2_choice = p2_choice

        self.player1 = make_player(p1_choice, 200, GROUND_Y - Player.HEIGHT, CONTROLS_P1, True)
        self.player2 = make_player(p2_choice, 750, GROUND_Y - Player.HEIGHT, CONTROLS_P2, False)
        self.ball = Ball(SCREEN_W // 2, GROUND_Y - 200)
        self.reset_timer = 0
        self.game_over = False
        self.winner = None
        self.bg = None

    def reset_positions(self):
        self.player1.x, self.player1.y = 200, GROUND_Y - Player.HEIGHT
        self.player1.vx = self.player1.vy = 0
        self.player2.x, self.player2.y = 750, GROUND_Y - Player.HEIGHT
        self.player2.vx = self.player2.vy = 0
        self.ball.reset(SCREEN_W // 2, GROUND_Y - 200)

    def check_goal(self):
        bx, by = self.ball.x, self.ball.y
        if bx - BALL_RADIUS <= GOAL_W and by + BALL_RADIUS >= GOAL_Y:
            self.player2.score += 1
            return True
        if bx + BALL_RADIUS >= SCREEN_W - GOAL_W and by + BALL_RADIUS >= GOAL_Y:
            self.player1.score += 1
            return True
        return False

    def update(self, keys):
        if self.game_over:
            return

        if self.reset_timer > 0:
            self.reset_timer -= 1
            if self.reset_timer == 0:
                self.reset_positions()
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

        if self.check_goal():
            self.reset_timer = self.RESET_DELAY
            if self.player1.score >= self.MAX_SCORE:
                self.game_over = True
                self.winner = 1
            elif self.player2.score >= self.MAX_SCORE:
                self.game_over = True
                self.winner = 2

    def draw(self, surface, font, big_font):
        if self.bg:
            surface.blit(self.bg, (0, 0))
        else:
            surface.fill(SKY_BLUE)
            pygame.draw.rect(surface, DARK_GRAY, (0, 0, SCREEN_W, 120))
            for i in range(0, SCREEN_W, 60):
                pygame.draw.rect(surface, GRAY, (i + 5, 10, 50, 100), border_radius=4)
            pygame.draw.rect(surface, GREEN, (0, GROUND_Y, SCREEN_W, SCREEN_H - GROUND_Y))
            pygame.draw.rect(surface, DARK_GREEN, (0, GROUND_Y, SCREEN_W, 6))
            pygame.draw.line(surface, WHITE, (SCREEN_W // 2, GROUND_Y), (SCREEN_W // 2, SCREEN_H), 3)
            pygame.draw.circle(surface, WHITE, (SCREEN_W // 2, GROUND_Y), 60, 3)

        pygame.draw.rect(surface, POST_COLOR, (0, GOAL_Y, GOAL_W, GOAL_H))
        pygame.draw.rect(surface, DARK_GRAY, (0, GOAL_Y, GOAL_W, GOAL_H), 3)
        for row in range(GOAL_Y, GROUND_Y, 18):
            pygame.draw.line(surface, NET_COLOR, (0, row), (GOAL_W, row), 1)
        for col in range(0, GOAL_W + 1, 9):
            pygame.draw.line(surface, NET_COLOR, (col, GOAL_Y), (col, GROUND_Y), 1)

        pygame.draw.rect(surface, POST_COLOR, (SCREEN_W - GOAL_W, GOAL_Y, GOAL_W, GOAL_H))
        pygame.draw.rect(surface, DARK_GRAY, (SCREEN_W - GOAL_W, GOAL_Y, GOAL_W, GOAL_H), 3)
        for row in range(GOAL_Y, GROUND_Y, 18):
            pygame.draw.line(surface, NET_COLOR, (SCREEN_W - GOAL_W, row), (SCREEN_W, row), 1)
        for col in range(SCREEN_W - GOAL_W, SCREEN_W + 1, 9):
            pygame.draw.line(surface, NET_COLOR, (col, GOAL_Y), (col, GROUND_Y), 1)

        self.player1.draw(surface)
        self.player2.draw(surface)
        self.ball.draw(surface)

        hud_surf = pygame.Surface((340, 52), pygame.SRCALPHA)
        hud_surf.fill((0, 0, 0, 120))
        surface.blit(hud_surf, (SCREEN_W // 2 - 170, 10))
        score_text = big_font.render(f"{self.player1.score}  :  {self.player2.score}", True, WHITE)
        surface.blit(score_text, (SCREEN_W // 2 - score_text.get_width() // 2, 14))

        p1_label = font.render("J1 (WASD + Q chuta)", True, LIGHT_RED)
        p2_label = font.render("J2 (↑←→ + ; chuta)", True, LIGHT_BLUE)
        surface.blit(p1_label, (10, 14))
        surface.blit(p2_label, (SCREEN_W - p2_label.get_width() - 10, 14))

        if self.reset_timer > 0:
            goal_text = big_font.render("⚽  G O L !  ⚽", True, YELLOW)
            shadow = big_font.render("⚽  G O L !  ⚽", True, BLACK)
            cx = SCREEN_W // 2 - goal_text.get_width() // 2
            surface.blit(shadow, (cx + 3, SCREEN_H // 2 - 30 + 3))
            surface.blit(goal_text, (cx, SCREEN_H // 2 - 30))

        if self.game_over:
            overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 160))
            surface.blit(overlay, (0, 0))
            winner_text = big_font.render(f"JOGADOR {self.winner} VENCEU!", True, YELLOW)
            restart_text = font.render("Pressione R para reiniciar", True, WHITE)
            surface.blit(winner_text, (SCREEN_W // 2 - winner_text.get_width() // 2, SCREEN_H // 2 - 40))
            surface.blit(restart_text, (SCREEN_W // 2 - restart_text.get_width() // 2, SCREEN_H // 2 + 20))

CHARACTERS = [
    ("Clássico", RED, LIGHT_RED, PLAYER1_IMAGE_PATH),
    ("Azul", BLUE, LIGHT_BLUE, PLAYER2_IMAGE_PATH),
    ("Verde", GREEN, (120, 220, 120), None),
    ("Laranja", ORANGE, (255, 195, 120), None),
    ("Cinza", DARK_GRAY, GRAY, None),
]

def make_player(choice_idx, x, y, controls, facing_right):
    _, color, light_color, image_path = CHARACTERS[choice_idx % len(CHARACTERS)]
    return Player(x, y, color, light_color, controls, facing_right=facing_right, image_path=image_path)

class MenuState:
    def __init__(self):
        self.p1_choice = 0
        self.p2_choice = 1
        self.p1_ready = False
        self.p2_ready = False

    def handle_event(self, event):
        if event.type != pygame.KEYDOWN:
            return None

        if event.key == pygame.K_ESCAPE:
            pygame.quit()
            sys.exit()

        # Player 1
        if event.key == pygame.K_a and not self.p1_ready:
            self.p1_choice = (self.p1_choice - 1) % len(CHARACTERS)
        elif event.key == pygame.K_d and not self.p1_ready:
            self.p1_choice = (self.p1_choice + 1) % len(CHARACTERS)
        elif event.key == pygame.K_w:
            self.p1_ready = True

        # Player 2
        if event.key == pygame.K_LEFT and not self.p2_ready:
            self.p2_choice = (self.p2_choice - 1) % len(CHARACTERS)
        elif event.key == pygame.K_RIGHT and not self.p2_ready:
            self.p2_choice = (self.p2_choice + 1) % len(CHARACTERS)
        elif event.key == pygame.K_UP:
            self.p2_ready = True

        # Reset seleção
        if event.key == pygame.K_r:
            self.p1_ready = False
            self.p2_ready = False

        # Começar jogo
        if event.key == pygame.K_RETURN and self.p1_ready and self.p2_ready:
            return GameState(self.p1_choice, self.p2_choice)

        return None

    def draw(self, surface, font, big_font):
        surface.fill(SKY_BLUE)

        title = big_font.render("HEAD SOCCER 2D", True, WHITE)
        surface.blit(title, (SCREEN_W // 2 - title.get_width() // 2, 40))

        info = font.render("A/D escolhe J1 | ←/→ escolhe J2 | W e ↑ confirmam", True, BLACK)
        surface.blit(info, (SCREEN_W // 2 - info.get_width() // 2, 100))

        def draw_card(x, y, choice_idx, label, ready):
            name, color, light_color, _ = CHARACTERS[choice_idx]

            rect = pygame.Rect(x, y, 250, 200)
            pygame.draw.rect(surface, DARK_GRAY, rect, border_radius=15)
            pygame.draw.rect(surface, color, rect, 3, border_radius=15)

            pygame.draw.circle(surface, color, (rect.centerx, y + 80), 35)
            pygame.draw.circle(surface, light_color, (rect.centerx, y + 80), 35, 3)

            txt_label = font.render(label, True, WHITE)
            txt_name = font.render(name, True, YELLOW)
            txt_ready = font.render("OK" if ready else "Escolher", True, GREEN if ready else RED)

            surface.blit(txt_label, (rect.centerx - txt_label.get_width() // 2, y + 10))
            surface.blit(txt_name, (rect.centerx - txt_name.get_width() // 2, y + 130))
            surface.blit(txt_ready, (rect.centerx - txt_ready.get_width() // 2, y + 160))

        draw_card(150, 200, self.p1_choice, "JOGADOR 1", self.p1_ready)
        draw_card(600, 200, self.p2_choice, "JOGADOR 2", self.p2_ready)

        if self.p1_ready and self.p2_ready:
            start = big_font.render("ENTER para jogar", True, YELLOW)
            surface.blit(start, (SCREEN_W // 2 - start.get_width() // 2, 450))


# ============================================================
#  LOOP PRINCIPAL
# ============================================================

def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
    pygame.display.set_caption("Head Soccer 2D")
    clock = pygame.time.Clock()

    font = pygame.font.SysFont("Arial", 22, bold=True)
    big_font = pygame.font.SysFont("Arial", 42, bold=True)

    state = MenuState()

    while True:
        keys = pygame.key.get_pressed()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if isinstance(state, MenuState):
                new_state = state.handle_event(event)
                if new_state is not None:
                    state = new_state

            elif isinstance(state, GameState):
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        pygame.quit()
                        sys.exit()
                    if event.key == pygame.K_r and state.game_over:
                        state = GameState(state.p1_choice, state.p2_choice)

        if isinstance(state, GameState):
            state.update(keys)
            state.draw(screen, font, big_font)
        else:
            state.draw(screen, font, big_font)

        pygame.display.flip()
        clock.tick(FPS)

if __name__ == "__main__":
    main()
