import pygame

pygame.init()

WINDOW_WIDTH = 1200
WINDOW_HEIGHT = 800

screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))

pygame.display.set_caption("Galactic Model")

running = True

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    screen.fill((0, 0, 0))

    pygame.display.flip()


pygame.quit()