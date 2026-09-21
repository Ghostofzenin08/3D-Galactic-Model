import math
import os
import random
import sys

import pygame


WINDOW_WIDTH = 1200
WINDOW_HEIGHT = 800
TARGET_FPS = 60

STAR_COUNT = 5500



def main():
    pygame.init()
    try:
        screen =  pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    except pygame.error:
        if "SDL_VIDEODRIVER" not in os.environ:
            os.environ["SDL_VIDEODRIVER"] = "dummy"
            pygame.quit()
            pygame.init()
            screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        else:
            raise
        pygame.display.set_caption("Galactic_Model")
        clock = pygame.time.Clock()
        font = pygame.font.Font(None, 24)
    
    running = True

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running  = False
        pygame.display.flip()

    pygame.quit()

if __name__ == "__main__":
    main()