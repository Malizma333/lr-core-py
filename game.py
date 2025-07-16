from main import get_moment
import pygame

pygame.init()
screen = pygame.display.set_mode((600, 400))
running = True

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                print("Spacebar pressed!")
            elif event.key == pygame.K_a:
                print(" 'a' key pressed!")
        elif event.type == pygame.KEYUP:
            if event.key == pygame.K_SPACE:
                print("Spacebar released!")

    pygame.display.flip()

pygame.quit()
