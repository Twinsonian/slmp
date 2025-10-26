import pygame
import random
import math
import time

# --- Ball Class ---
class Ball:
    def __init__(self, x, y, dx, dy, radius, color, generation, immune=False):
        self.x = x
        self.y = y
        self.dx = dx
        self.dy = dy
        self.radius = radius
        self.color = color
        self.generation = generation
        self.immune = immune
        self.spawn_time = time.time() if immune else None  #Always set spawn_time if immune

    def move(self, screen_width, screen_height):
        self.x += self.dx
        self.y += self.dy

        # Bounce off walls with slight randomization
        if self.x - self.radius <= 0 or self.x + self.radius >= screen_width:
            self.dx *= -1
            self.dy += random.uniform(-0.5, 0.5)
        if self.y - self.radius <= 0 or self.y + self.radius >= screen_height:
            self.dy *= -1
            self.dx += random.uniform(-0.5, 0.5)

        # Disable immunity after 5 seconds
        if self.immune and self.spawn_time and time.time() - self.spawn_time > 1:
            self.immune = False
            self.spawn_time = None  # Optional: clear spawn_time once expired

    def draw(self, screen):
        pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), self.radius)

# --- Particle Class ---
class Particle:
    def __init__(self, x, y, dx, dy, color):
        self.x = x
        self.y = y
        self.dx = dx
        self.dy = dy
        self.color = color
        self.life = 30

    def move(self):
        self.x += self.dx
        self.y += self.dy
        self.life -= 1

    def draw(self, screen):
        if self.life > 0:
            pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), 2)

# --- Safe Velocity Helper ---
def safe_velocity():
    v = 0
    while abs(v) < 1.5:
        v = random.choice([-4, -3, 3, 4]) + random.uniform(-0.5, 0.5)
    return v

# --- Spawn a Ball ---
def spawn_ball(balls, width, height, immune=True):
    radius = 60
    dx = safe_velocity()
    dy = safe_velocity()
    color = [random.randint(100, 255) for _ in range(3)]
    x = random.randint(radius, width - radius)
    y = random.randint(radius, height - radius)
    balls.append(Ball(x, y, dx, dy, radius, color, generation=0, immune=immune))

# --- Check and Spawn Big Ball ---
def check_and_spawn_big_ball(balls, width, height):
    has_big_ball = any(ball.generation == 0 for ball in balls)
    if not has_big_ball and len(balls) < 10:
        spawn_ball(balls, width, height, immune=True)

# --- Main Game Loop ---

def ensure_minimum_balls(balls, width, height):
    if len(balls) < 3:
        spawn_ball(balls, width, height, immune=True)

def launch_visual(arg=None):
    pygame.init()
    screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
    clock = pygame.time.Clock()
    width, height = screen.get_size()

    balls = []
    particles = []

    # Start with 5 big balls
    for _ in range(5):
        spawn_ball(balls, width, height, immune=False)

    running = True
    while running:
        screen.fill((10, 10, 30))

        for event in pygame.event.get():
            if event.type in (pygame.QUIT, pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
                running = False

        # Move and draw balls
        for ball in balls:
            ball.move(width, height)
            ball.draw(screen)

        # Move and draw particles
        for p in particles:
            p.move()
            p.draw(screen)
        particles = [p for p in particles if p.life > 0]

        # Collision detection
        new_balls = []
        removed = set()
        for i in range(len(balls)):
            for j in range(i + 1, len(balls)):
                a, b = balls[i], balls[j]
                if math.hypot(a.x - b.x, a.y - b.y) < a.radius + b.radius:
                    # Skip collision if either ball is immune
                    if a.immune or b.immune:
                        continue

                    removed.update([i, j])
                    for ball in (a, b):
                        if ball.generation < 3:
                            for _ in range(2):
                                radius = ball.radius // 2
                                dx = safe_velocity()
                                dy = safe_velocity()
                                offset_x = random.randint(-5, 5)
                                offset_y = random.randint(-5, 5)
                                color = [min(255, max(0, c + random.randint(-30, 30))) for c in ball.color]
                                new_balls.append(Ball(ball.x + offset_x, ball.y + offset_y, dx, dy, radius, color, ball.generation + 1, immune=True))
                        else:
                            for _ in range(5):
                                dx = random.uniform(-2, 2)
                                dy = random.uniform(-2, 2)
                                color = [min(255, max(0, c + random.randint(-50, 50))) for c in ball.color]
                                particles.append(Particle(ball.x, ball.y, dx, dy, color))

        balls = [b for i, b in enumerate(balls) if i not in removed] + new_balls

        # Always ensure at least 3 balls
        if len(balls) < 3:
            spawn_ball(balls, width, height, immune=True)

        # Ensure at least one big ball if under 10 total
        check_and_spawn_big_ball(balls, width, height)


        pygame.display.update()
        clock.tick(60)

    pygame.display.quit()

# --- Run the Game ---
if __name__ == "__main__":
    launch_visual()

