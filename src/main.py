import pygame
import random

pygame.init()

WINDOW_WIDTH = 1200
WINDOW_HEIGHT = 800
TARGET_FPS = 60

class Stars:
    def __init__(self, x, y, velocity_x, velocity_y, mass, radius, brightness, temperature, color, age):
        self.position = pygame.Vector2(x, y)
        self.velocity = pygame.Vector2(velocity_x, velocity_y)
        self.acceleration = pygame.Vector2(0, 0)
        self.mass = mass
        self.radius = radius
        self.brightness = brightness
        self.temperature  = temperature
        self.color = color
        self.age = age

    def update(self, delta_time):
        self.velocity += self.acceleration * delta_time
        self.position += self.velocity  * delta_time

    def draw(self, surface):
        display_color = tuple(int(value * self.brightness) for value in self.color)
        pygame.draw.circle(surface, display_color, self.position, self.radius)

screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))

clock = pygame.time.Clock()
font = pygame.font.Font(None,28)

stars = []
for __ in range(STAR_COUNT):
    x = random.radint(0, WINDOW_WIDTH)
    y = random.radint(0, WINDOW_HEIGHT)

    stars.append(Stars(x, y, ))

pygame.display.set_caption("Galactic Model")

running = True

while running:
    delta_time = clock.tick(TARGET_FPS) / 1000

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    screen.fill((0, 0, 0))

    fps = clock.get_fps()

    fps_text = font.render(f"FPS: {fps:.0f}", True, (255, 255, 255))

    screen.blit(fps_text, (15, 15))

    pygame.display.flip()


pygame.quit()