import pygame

pygame.init()

WINDOW_WIDTH = 1200
WINDOW_HEIGHT = 800
TARGET_FPS = 60



screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))

clock = pygame.time.Clock()
font = pygame.font.Font(None,28)



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