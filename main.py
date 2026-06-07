from enum import Enum, auto
import random
import time
from typing import Any
import pygame
from pygame.sprite import AbstractGroup

SCREEN = (1250, 700)
GRID = (25, 14)
GRID_LINE_WIDTH = 1
CELL = (SCREEN[0] // GRID[0], SCREEN[1] // GRID[1])
SIMULATION_SPEED = 500

INITIAL_GRASS = 20
GRASS_GROWTH_RATE = 1
MAX_GRASS = 100

INITIAL_RABBITS_COUNT = 20
INITIAL_RABBIT_FOOD = 10
RABBIT_MAX_FOOD = 45
RABBIT_METABOLISM_RATE = 3
RABBIT_REPRODUCTION_AGE = 10
RABBIT_RERPODUCTION_PROB = 0.5
RABBIT_MIN_FOOD_TO_REPRODUCE = 40
RABBIT_FOOD_VALUE = 10
RABBIT_MAX_AGE = 25

INITIAL_WOLVES_COUNT = 5
INITIAL_WOLF_FOOD = 150
WOLF_MAX_FOOD = 200
WOLF_METABOLISM_RATE = 2
WOLF_REPRODUCTION_AGE = 10
WOLF_RERPODUCTION_PROB = 0.5
WOLF_MIN_FOOD_TO_REPRODUCE = 120
WOLF_MAX_AGE = 50


class AnimalKind(Enum):
    RABBIT = auto()
    WOLF = auto()


class Animal(pygame.sprite.Sprite):
    def __init__(
        self,
        kind: AnimalKind,
        x: int,
        y: int,
        food: float,
        age: int,
        *groups: AbstractGroup,
    ) -> None:
        super().__init__(*groups)
        self.kind = kind
        if kind == AnimalKind.WOLF:
            self.image = pygame.image.load("assets/wolf-head.png").convert_alpha()
            self.key = "wolf"
        elif kind == AnimalKind.RABBIT:
            self.image = pygame.image.load("assets/rabbit-head.png").convert_alpha()
            self.key = "rabbit"
        self.age = age
        self.food = food
        image_size = self.image.get_size()
        self.rect = self.image.get_rect().move(
            x * CELL[0] + image_size[0] / 4, y * CELL[1] + image_size[1] / 4
        )
        self.x = x
        self.y = y
        area[y][x][self.key] = self

    def update(self, *args: Any, **kwargs: Any) -> None:
        self.age += 1
        if self.kind == AnimalKind.WOLF:
            if self.age > WOLF_MAX_AGE:
                self.kill()
                area[self.y][self.x]["wolf"] = None
                return
            self.food -= WOLF_METABOLISM_RATE
        elif self.kind == AnimalKind.RABBIT:
            if self.age > RABBIT_MAX_AGE:
                self.kill()
                area[self.y][self.x]["rabbit"] = None
                return
            self.food -= RABBIT_METABOLISM_RATE
        if self.food <= 0:
            self.kill()
            area[self.y][self.x][self.key] = None
            return
        self.move()
        self.eat()
        self.reproduce()

    def move(self):
        directions = []
        for direction in [
            (-1, 0),
            (1, 0),
            (0, -1),
            (0, 1),
            (-1, -1),
            (-1, 1),
            (1, -1),
            (1, 1),
        ]:
            x, y = self.x + direction[0], self.y + direction[1]
            if x < 0 or x >= GRID[0] or y < 0 or y >= GRID[1]:
                continue
            cell = area[y][x]
            if (
                cell[self.key]
                or (self.kind == AnimalKind.RABBIT and cell["wolf"])
                or (
                    self.kind == AnimalKind.WOLF
                    and cell["rabbit"]
                    and self.food + RABBIT_FOOD_VALUE > WOLF_MAX_FOOD
                )
            ):
                continue
            directions.append(direction)
        if not directions:
            return
        dx, dy = random.sample(directions, 1)[0]
        area[self.y][self.x][self.key] = None
        self.x += dx
        self.y += dy
        self.rect.move_ip(dx * CELL[0], dy * CELL[1])
        area[self.y][self.x][self.key] = self

    def eat(self):
        if self.kind == AnimalKind.WOLF:
            rabbit = area[self.y][self.x]["rabbit"]
            if rabbit:
                rabbit.kill()
                area[self.y][self.x]["rabbit"] = None
                self.food += RABBIT_FOOD_VALUE
        elif self.kind == AnimalKind.RABBIT:
            grass_sprite = area[self.y][self.x]["grass"]
            grass = min(RABBIT_MAX_FOOD - self.food, grass_sprite.grass)
            self.food += grass
            grass_sprite.grass -= grass

    def reproduce(self) -> None:
        if (
            self.kind == AnimalKind.WOLF
            and (
                self.age < WOLF_REPRODUCTION_AGE
                or self.food < WOLF_MIN_FOOD_TO_REPRODUCE
                or random.random() < WOLF_RERPODUCTION_PROB
            )
            or self.kind == AnimalKind.RABBIT
            and (
                self.age < RABBIT_REPRODUCTION_AGE
                or self.food < RABBIT_MIN_FOOD_TO_REPRODUCE
                or random.random() < RABBIT_RERPODUCTION_PROB
            )
        ):
            return
        directions = []
        for direction in [
            (-1, 0),
            (1, 0),
            (0, -1),
            (0, 1),
            (-1, -1),
            (-1, 1),
            (1, -1),
            (1, 1),
        ]:
            x, y = self.x + direction[0], self.y + direction[1]
            if x < 0 or x >= GRID[0] or y < 0 or y >= GRID[1]:
                continue
            cell = area[y][x]
            if self.kind == AnimalKind.WOLF and (cell["rabbit"] or cell["wolf"]):
                continue
            if self.kind == AnimalKind.RABBIT and cell["wolf"]:
                return
            directions.append(direction)
        if not directions:
            return
        dx, dy = random.sample(directions, 1)[0]
        self.food /= 2
        Animal(self.kind, self.x + dx, self.y + dy, self.food, 0, *self.groups())


class Grass(pygame.sprite.Sprite):
    def __init__(self, x: int, y: int, *groups: AbstractGroup) -> None:
        super().__init__(*groups)
        self.grass = INITIAL_GRASS
        self.image = pygame.surface.Surface(
            (CELL[0] - GRID_LINE_WIDTH, CELL[1] - GRID_LINE_WIDTH)
        ).convert()
        self.rect = self.image.get_rect().move(x * CELL[0], y * CELL[1])
        self._fill_grass()

    def update(self, *args: Any, **kwargs: Any) -> None:
        self.grass = min(MAX_GRASS, self.grass + GRASS_GROWTH_RATE)
        self._fill_grass()

    def _fill_grass(self):
        if self.grass >= 80:
            self.image.fill((65, 117, 5))
        elif self.grass >= 50:
            self.image.fill((126, 211, 33))
        elif self.grass >= 20:
            self.image.fill((184, 233, 134))
        else:
            self.image.fill((139, 87, 42))


def main():
    pygame.init()
    screen = pygame.display.set_mode(SCREEN)
    pygame.display.set_caption("Rabbits and Wolves")

    background = pygame.Surface(SCREEN).convert()
    background.fill("black")
    screen.blit(background, (0, 0))

    grass_sprites = pygame.sprite.Group()
    wolf_sprites = pygame.sprite.Group()
    rabbit_sprites = pygame.sprite.Group()
    all_sprites = pygame.sprite.RenderPlain()
    global area
    area = [
        [
            {
                "grass": Grass(x, y, grass_sprites, all_sprites),
                "rabbit": None,
                "wolf": None,
            }
            for x in range(GRID[0])
        ]
        for y in range(GRID[1])
    ]
    positions = random.sample(
        range(GRID[0] * GRID[1]), INITIAL_RABBITS_COUNT + INITIAL_WOLVES_COUNT
    )
    wolf_positions = random.sample(positions, INITIAL_WOLVES_COUNT)
    rabbit_positions = [pos for pos in positions if pos not in wolf_positions]
    print(f"wolf positions: {wolf_positions}\nrabbit positions: {rabbit_positions}")
    for pos in wolf_positions:
        Animal(
            AnimalKind.WOLF,
            pos % GRID[0],
            pos // GRID[0],
            INITIAL_WOLF_FOOD,
            random.randint(0, WOLF_MAX_AGE),
            wolf_sprites,
            all_sprites,
        )
    for pos in rabbit_positions:
        Animal(
            AnimalKind.RABBIT,
            pos % GRID[0],
            pos // GRID[0],
            INITIAL_RABBIT_FOOD,
            random.randint(0, RABBIT_MAX_AGE),
            rabbit_sprites,
            all_sprites,
        )
    pygame.time.set_timer(0, SIMULATION_SPEED)
    clock = pygame.time.Clock()
    for i in range(GRID[0]):
        pygame.draw.line(
            screen, "black", (i * CELL[0], 0), (i * CELL[0], SCREEN[1]), GRID_LINE_WIDTH
        )
    for i in range(GRID[1]):
        pygame.draw.line(
            screen, "black", (0, i * CELL[1]), (SCREEN[0], i * CELL[1]), GRID_LINE_WIDTH
        )
    while True:
        clock.tick(30)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return
            elif event.type == 0:
                grass_sprites.update()
                rabbit_sprites.update()
                wolf_sprites.update()
                print(f"wolves: {len(wolf_sprites)}\nrabbits: {len(rabbit_sprites)}")
        all_sprites.clear(screen, background)
        all_sprites.draw(screen)
        pygame.display.update()


if __name__ == "__main__":
    main()
