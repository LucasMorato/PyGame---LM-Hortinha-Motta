import pygame
import sys
import math

# ============================================================
#  CONFIGURAÇÕES GERAIS
# ============================================================
SCREEN_W, SCREEN_H = 1000, 600
FPS = 60
GRAVITY = 0.6
GROUND_Y = 480          # Y do chão (onde os jogadores ficam de pé)
BALL_RADIUS = 22

# ─── Cores (substitua por imagens depois) ───────────────────
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
GOAL_W  = 20
GOAL_H  = 140
GOAL1_X = 0                       # Goleira esquerda (Jogador 2 marca aqui)
GOAL2_X = SCREEN_W - GOAL_W       # Goleira direita  (Jogador 1 marca aqui)
GOAL_Y  = GROUND_Y - GOAL_H

# ─── Controles ──────────────────────────────────────────────
CONTROLS_P1 = {
    "left":  pygame.K_a,
    "right": pygame.K_d,
    "jump":  pygame.K_w,
    "kick":  pygame.K_q,       # Q para chutar (J1)
}
CONTROLS_P2 = {
    "left":  pygame.K_LEFT,
    "right": pygame.K_RIGHT,
    "jump":  pygame.K_UP,
    "kick":  pygame.K_SEMICOLON,  # ; para chutar (J2)
}

# ============================================================
#  CLASSE JOGADOR
# ============================================================
class Player:
    WIDTH  = 50
    HEIGHT = 70
    SPEED  = 3.5          # velocidade reduzida
    JUMP_FORCE   = -11   # pulo um pouco menor
    KICK_RADIUS  = 55    # raio de alcance do chute
    KICK_FORCE   = 9     # força do chute reduzida
    KICK_DURATION = 12   # frames que o chute fica ativo

    def __init__(self, x, y, color, light_color, controls, facing_right=True):
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

        # ═══════════════════════════════════════════════════════
        #  COMO USAR PNG PARA OS JOGADORES
        # ───────────────────────────────────────────────────────
        # 1. Crie uma pasta  assets/  no mesmo diretório deste arquivo
        # 2. Coloque os PNGs lá:
        #       assets/player1.png   → Jogador 1 (vermelho)
        #       assets/player2.png   → Jogador 2 (azul)
        #
        # 3. O PNG deve ter FUNDO TRANSPARENTE (.png com alpha)
        #    e a imagem do personagem olhando para a DIREITA.
        #    O jogo espelha automaticamente quando ele vira.
        #
        # 4. Tamanho recomendado do arquivo: 100x140 px
        #    (será redimensionado para WIDTH x HEIGHT abaixo)
        #
        # 5. Descomente as duas linhas abaixo e apague a linha
        #    "self.image = None" logo depois:
        #
        # self.image = pygame.image.load("assets/player1.png").convert_alpha()
        # self.image = pygame.transform.scale(self.image, (self.WIDTH, self.HEIGHT))
        self.image = None   # ← apague esta linha ao usar PNG

    # ── Retângulo de colisão ──────────────────────────────────
    @property
    def rect(self):
        return pygame.Rect(self.x, self.y, self.WIDTH, self.HEIGHT)

    # ── Centro do "corpo" para cálculo de chute ──────────────
    @property
    def center(self):
        return (self.x + self.WIDTH / 2, self.y + self.HEIGHT / 2)

    # ── Posição do pé (para colisão com bola) ─────────────────
    @property
    def foot_center(self):
        foot_x = self.x + self.WIDTH * (0.7 if self.facing_right else 0.3)
        foot_y = self.y + self.HEIGHT * 0.85
        return (foot_x, foot_y)

    def handle_input(self, keys):
        # Movimento horizontal
        if keys[self.controls["left"]]:
            self.vx = -self.SPEED
            self.facing_right = False
        elif keys[self.controls["right"]]:
            self.vx = self.SPEED
            self.facing_right = True
        else:
            self.vx *= 0.75   # atrito

        # Pulo
        if keys[self.controls["jump"]] and self.on_ground:
            self.vy = self.JUMP_FORCE
            self.on_ground = False

        # Chute
        if keys[self.controls["kick"]] and not self.kicking:
            self.kicking = True
            self.kick_timer = self.KICK_DURATION

    def update(self):
        # Gravidade
        self.vy += GRAVITY

        self.x += self.vx
        self.y += self.vy

        # Chão
        if self.y + self.HEIGHT >= GROUND_Y:
            self.y = GROUND_Y - self.HEIGHT
            self.vy = 0
            self.on_ground = True

        # Paredes laterais (respeitando as goleiras)
        if self.x < GOAL_W:
            self.x = GOAL_W
        if self.x + self.WIDTH > SCREEN_W - GOAL_W:
            self.x = SCREEN_W - GOAL_W - self.WIDTH

        # Timer do chute
        if self.kicking:
            self.kick_timer -= 1
            if self.kick_timer <= 0:
                self.kicking = False

    def try_kick_ball(self, ball):
        """Aplica força na bola se o chute está ativo e a bola está no alcance."""
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
            # Força principal na direção do chute + impulso vertical
            ball.vx = dx * self.KICK_FORCE + (self.SPEED if self.facing_right else -self.SPEED)
            ball.vy = dy * self.KICK_FORCE - 4   # leva a bola um pouco para cima

    def collide_with_player(self, other):
        """Empurra os dois jogadores quando se colidem."""
        r1 = self.rect
        r2 = other.rect
        if not r1.colliderect(r2):
            return
        # Empurra pelo eixo X
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
            # ── COM SPRITE ─────────────────────────────────────
            img = self.image if self.facing_right else pygame.transform.flip(self.image, True, False)
            surface.blit(img, (x, y))
        else:
            # ── PLACEHOLDER GEOMÉTRICO ─────────────────────────
            # Corpo
            pygame.draw.rect(surface, self.color, (x + 10, y + 30, w - 20, h - 30), border_radius=8)
            # Cabeça (grande, estilo head soccer)
            head_r = 26
            head_cx = x + w // 2
            head_cy = y + 26
            pygame.draw.circle(surface, self.light_color, (head_cx, head_cy), head_r)
            pygame.draw.circle(surface, self.color,       (head_cx, head_cy), head_r, 3)
            # Olho
            eye_offset = 8 if self.facing_right else -8
            pygame.draw.circle(surface, BLACK, (head_cx + eye_offset, head_cy - 4), 5)
            pygame.draw.circle(surface, WHITE, (head_cx + eye_offset + 2, head_cy - 6), 2)
            # Pernas
            pygame.draw.rect(surface, self.color, (x + 10, y + h - 22, 14, 22), border_radius=4)
            pygame.draw.rect(surface, self.color, (x + w - 24, y + h - 22, 14, 22), border_radius=4)

            # Efeito visual de chute
            if self.kicking:
                kick_x = int(self.foot_center[0])
                kick_y = int(self.foot_center[1])
                pygame.draw.circle(surface, YELLOW, (kick_x, kick_y), 18, 4)

# ============================================================
#  CLASSE BOLA
# ============================================================
class Ball:
    FRICTION = 0.985
    BOUNCE   = 0.55

    def __init__(self, x, y):
        self.reset(x, y)

        # ═══════════════════════════════════════════════════════
        #  COMO USAR PNG PARA A BOLA
        # ───────────────────────────────────────────────────────
        # 1. Coloque o arquivo em:  assets/ball.png
        # 2. PNG com fundo transparente, imagem quadrada (ex: 64x64 px)
        # 3. A bola gira automaticamente conforme se move
        # 4. Descomente e apague o "self.image = None":
        #
        # self.image = pygame.image.load("assets/ball.png").convert_alpha()
        # self.image = pygame.transform.scale(self.image, (BALL_RADIUS*2, BALL_RADIUS*2))
        self.image = None   # ← apague esta linha ao usar PNG

    def reset(self, x, y):
        self.x  = float(x)
        self.y  = float(y)
        self.vx = 0.0
        self.vy = 0.0
        self.angle = 0.0   # rotação visual

    def update(self):
        self.vy += GRAVITY * 0.55
        self.x  += self.vx
        self.y  += self.vy

        # Rotação visual proporcional à velocidade horizontal
        self.angle += self.vx * 1.5

        # Chão
        if self.y + BALL_RADIUS >= GROUND_Y:
            self.y  = GROUND_Y - BALL_RADIUS
            self.vy = -abs(self.vy) * self.BOUNCE
            self.vx *= self.FRICTION
            if abs(self.vy) < 1.5:
                self.vy = 0

        # Teto
        if self.y - BALL_RADIUS <= 0:
            self.y  = BALL_RADIUS
            self.vy = abs(self.vy) * self.BOUNCE

        # Paredes laterais (dentro de campo, excluindo área de gol)
        # Gol esquerdo
        if self.x - BALL_RADIUS <= GOAL_W:
            if self.y + BALL_RADIUS < GOAL_Y:   # acima da goleira → rebate
                self.x  = GOAL_W + BALL_RADIUS
                self.vx = abs(self.vx) * self.BOUNCE
            # se estiver na altura da goleira → entra no gol (tratado em GameState)

        # Gol direito
        if self.x + BALL_RADIUS >= SCREEN_W - GOAL_W:
            if self.y + BALL_RADIUS < GOAL_Y:
                self.x  = SCREEN_W - GOAL_W - BALL_RADIUS
                self.vx = -abs(self.vx) * self.BOUNCE

    def collide_with_player(self, player):
        """Colisão elástica simples bola ↔ jogador (corpo inteiro)."""
        bx, by = self.x, self.y
        px = player.x + player.WIDTH / 2
        py = player.y + player.HEIGHT / 2

        # Usando a cabeça como círculo dominante de colisão
        hx = player.x + player.WIDTH / 2
        hy = player.y + 26
        head_r = 26

        dist = math.hypot(bx - hx, by - hy)
        min_dist = BALL_RADIUS + head_r

        if dist < min_dist and dist > 0:
            nx = (bx - hx) / dist
            ny = (by - hy) / dist
            overlap = min_dist - dist
            self.x += nx * overlap
            self.y += ny * overlap
            # Transferência de momento
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
            # ── COM SPRITE ─────────────────────────────────────
            rotated = pygame.transform.rotate(self.image, -self.angle)
            rect = rotated.get_rect(center=(ix, iy))
            surface.blit(rotated, rect)
        else:
            # ── PLACEHOLDER ────────────────────────────────────
            pygame.draw.circle(surface, YELLOW, (ix, iy), r)
            pygame.draw.circle(surface, ORANGE, (ix, iy), r, 3)
            # Detalhes da bola (linhas de costura giradas)
            for i in range(4):
                a = math.radians(self.angle + i * 45)
                x1 = ix + int((r - 6) * math.cos(a))
                y1 = iy + int((r - 6) * math.sin(a))
                x2 = ix + int((r - 14) * math.cos(a + math.pi))
                y2 = iy + int((r - 14) * math.sin(a + math.pi))
                pygame.draw.line(surface, DARK_GRAY, (x1, y1), (x2, y2), 2)

# ============================================================
#  ESTADO DO JOGO
# ============================================================
class GameState:
    MAX_SCORE   = 5
    RESET_DELAY = 90    # frames de pausa após gol

    def __init__(self):
        self.player1 = Player(200, GROUND_Y - Player.HEIGHT, RED,  LIGHT_RED,  CONTROLS_P1, facing_right=True)
        self.player2 = Player(750, GROUND_Y - Player.HEIGHT, BLUE, LIGHT_BLUE, CONTROLS_P2, facing_right=False)
        self.ball    = Ball(SCREEN_W // 2, GROUND_Y - 200)
        self.reset_timer = 0
        self.game_over   = False
        self.winner      = None

        # ── Onde colocar a imagem de fundo ────────────────────
        # self.bg = pygame.image.load("assets/background.png").convert()
        # self.bg = pygame.transform.scale(self.bg, (SCREEN_W, SCREEN_H))
        self.bg = None   # None = fundo desenhado com primitivas

    def reset_positions(self):
        self.player1.x, self.player1.y = 200, GROUND_Y - Player.HEIGHT
        self.player1.vx = self.player1.vy = 0
        self.player2.x, self.player2.y = 750, GROUND_Y - Player.HEIGHT
        self.player2.vx = self.player2.vy = 0
        self.ball.reset(SCREEN_W // 2, GROUND_Y - 200)

    def check_goal(self):
        bx, by = self.ball.x, self.ball.y
        # Gol na goleira esquerda → ponto para Jogador 2
        if bx - BALL_RADIUS <= GOAL_W and by + BALL_RADIUS >= GOAL_Y:
            self.player2.score += 1
            return True
        # Gol na goleira direita → ponto para Jogador 1
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

        # Input
        self.player1.handle_input(keys)
        self.player2.handle_input(keys)

        # Física
        self.player1.update()
        self.player2.update()
        self.ball.update()

        # Colisões
        self.player1.collide_with_player(self.player2)
        self.ball.collide_with_player(self.player1)
        self.ball.collide_with_player(self.player2)

        # Chutes
        self.player1.try_kick_ball(self.ball)
        self.player2.try_kick_ball(self.ball)

        # Gols
        if self.check_goal():
            self.reset_timer = self.RESET_DELAY
            # Verificar vencedor
            if self.player1.score >= self.MAX_SCORE:
                self.game_over = True
                self.winner = 1
            elif self.player2.score >= self.MAX_SCORE:
                self.game_over = True
                self.winner = 2

    def draw(self, surface, font, big_font):
        # ─── FUNDO ───────────────────────────────────────────
        if self.bg:
            surface.blit(self.bg, (0, 0))
        else:
            # Céu
            surface.fill(SKY_BLUE)
            # Arquibancadas (placeholder)
            pygame.draw.rect(surface, DARK_GRAY, (0, 0, SCREEN_W, 120))
            for i in range(0, SCREEN_W, 60):
                pygame.draw.rect(surface, GRAY, (i + 5, 10, 50, 100), border_radius=4)
            # Grama
            pygame.draw.rect(surface, GREEN,      (0, GROUND_Y, SCREEN_W, SCREEN_H - GROUND_Y))
            pygame.draw.rect(surface, DARK_GREEN, (0, GROUND_Y, SCREEN_W, 6))
            # Linha do meio
            pygame.draw.line(surface, WHITE, (SCREEN_W // 2, GROUND_Y), (SCREEN_W // 2, SCREEN_H), 3)
            pygame.draw.circle(surface, WHITE, (SCREEN_W // 2, GROUND_Y), 60, 3)

        # ─── GOLEIRAS ────────────────────────────────────────
        # Goleira esquerda
        pygame.draw.rect(surface, POST_COLOR, (0, GOAL_Y, GOAL_W, GOAL_H))
        pygame.draw.rect(surface, DARK_GRAY,  (0, GOAL_Y, GOAL_W, GOAL_H), 3)
        # Rede esquerda (linhas)
        for row in range(GOAL_Y, GROUND_Y, 18):
            pygame.draw.line(surface, NET_COLOR, (0, row), (GOAL_W, row), 1)
        for col in range(0, GOAL_W + 1, 9):
            pygame.draw.line(surface, NET_COLOR, (col, GOAL_Y), (col, GROUND_Y), 1)

        # Goleira direita
        pygame.draw.rect(surface, POST_COLOR, (SCREEN_W - GOAL_W, GOAL_Y, GOAL_W, GOAL_H))
        pygame.draw.rect(surface, DARK_GRAY,  (SCREEN_W - GOAL_W, GOAL_Y, GOAL_W, GOAL_H), 3)
        for row in range(GOAL_Y, GROUND_Y, 18):
            pygame.draw.line(surface, NET_COLOR, (SCREEN_W - GOAL_W, row), (SCREEN_W, row), 1)
        for col in range(SCREEN_W - GOAL_W, SCREEN_W + 1, 9):
            pygame.draw.line(surface, NET_COLOR, (col, GOAL_Y), (col, GROUND_Y), 1)

        # ─── JOGADORES E BOLA ────────────────────────────────
        self.player1.draw(surface)
        self.player2.draw(surface)
        self.ball.draw(surface)

        # ─── HUD (placar) ────────────────────────────────────
        hud_surf = pygame.Surface((340, 52), pygame.SRCALPHA)
        hud_surf.fill((0, 0, 0, 120))
        surface.blit(hud_surf, (SCREEN_W // 2 - 170, 10))
        score_text = big_font.render(f"{self.player1.score}  :  {self.player2.score}", True, WHITE)
        surface.blit(score_text, (SCREEN_W // 2 - score_text.get_width() // 2, 14))

        p1_label = font.render("J1 (WASD + Q chuta)", True, LIGHT_RED)
        p2_label = font.render("J2 (↑←→ + ; chuta)", True, LIGHT_BLUE)
        surface.blit(p1_label, (10, 14))
        surface.blit(p2_label, (SCREEN_W - p2_label.get_width() - 10, 14))

        # ─── GOL / VENCEDOR ──────────────────────────────────
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

# ============================================================
#  LOOP PRINCIPAL
# ============================================================
def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
    pygame.display.set_caption("Head Soccer 2D")
    clock  = pygame.time.Clock()

    font     = pygame.font.SysFont("Arial", 22, bold=True)
    big_font = pygame.font.SysFont("Arial", 42, bold=True)

    game = GameState()

    while True:
        keys = pygame.key.get_pressed()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()
                if event.key == pygame.K_r:
                    game = GameState()

        game.update(keys)
        game.draw(screen, font, big_font)
        pygame.display.flip()
        clock.tick(FPS)

if __name__ == "__main__":
    main()