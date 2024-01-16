import pygame
import os
import sys
import sqlite3
import random


W, H = 800, 600
FPS = 60
P = 16
S = 75
CLOCK = pygame.time.Clock()
FONT = 'data/ThaleahFat.ttf'
DB = 'data/data.db'


class Game:
    def __init__(self, world: str) -> None:
        pygame.init()
        self.screen = pygame.display.set_mode((W, H))
        pygame.display.set_icon(load_image('ico.png'))
        self.world = world
        pygame.display.set_caption('World: {}'.format(self.world))
        self.con = sqlite3.connect(DB)
        self.bg = load_image(random.choice(os.listdir('sprites/random_backgrounds')),
                             folder='sprites/random_backgrounds/')
        self.bg_pos = -random.randrange(2200), -random.randrange(2400)
        self.systems_sprites = pygame.sprite.Group()
        self.asteroid_sprites = pygame.sprite.Group()
        self.system_sprites = pygame.sprite.Group()
        self.all_sprites = [self.system_sprites]
        self.starter_planet = None
        self.starter_system = None
        self.stars = self.stars_fill()
        self.planets = self.planets_fill()
        self.load_map()
        self.load_system(self.starter_system)
        self.running = True

    def main_loop(self) -> None:
        while self.running:
            self.check_events()
            self.screen.fill((0, 0, 0))
            self.screen.blit(self.bg, self.bg.get_rect(topleft=self.bg_pos))
            for group in self.all_sprites:
                group.draw(self.screen)
                group.update()
            # if self.systems_sprites.
            pygame.display.flip()
            CLOCK.tick(FPS)

    def check_events(self) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

    def load_map(self):
        mp = self.con.cursor().execute('SELECT map FROM worlds WHERE name = "{}"'.format(self.world)).fetchall()[0][0]
        try:
            with open('maps/' + mp) as map_file:
                level = [line.strip() for line in map_file]
                starter_data = level[0].split(': ')[1].split('_')
                self.starter_system = int(starter_data[0])
                self.starter_planet = int(starter_data[1])
                for y in range(1, len(level)):
                    for x in range(len(level[0])):
                        if level[y][x] in '123456789':
                            pass
        except FileNotFoundError:
            print('File "{}" not found'.format(mp))
            sys.exit()

    def load_system(self, n):
        self.system_sprites.remove()
        try:
            with open('systems/system' + str(self.starter_system) + '.txt') as system_file:
                level = [line.strip() for line in system_file]
                for y in range(len(level)):
                    for x in range(len(level[0])):
                        if level[y][x] == 's':
                            AnimatedSprite(load_image(self.stars[n], folder='sprites/random_stars/'), 50, 1, x * S - 25,
                                           y * S - 25, self.system_sprites)
                        elif level[y][x] in '123':
                            AnimatedSprite(load_image(self.planets[n - 1][int(level[y][x])],
                                                      folder='sprites/random_planets/'), 10, 10, x * S, y * S,
                                           self.system_sprites)
        except FileNotFoundError:
            print('File "system{}" not found'.format(self.starter_system))
            sys.exit()

    def stars_fill(self) -> dict:
        d = {}
        for i in range(9):
            d[i + 1] = random.choice(os.listdir('sprites/random_stars'))
        return d

    def planets_fill(self) -> list:
        b = []
        for i in range(9):
            d = {}
            for j in range(3):
                d[j + 1] = random.choice(os.listdir('sprites/random_planets'))
            b.append(d)
        return b


class MainMenu:
    def __init__(self) -> None:
        pygame.init()
        self.screen = pygame.display.set_mode((W, H))
        pygame.display.set_icon(load_image('ico.png'))
        pygame.display.set_caption('Main menu')
        self.con = sqlite3.connect(DB)
        self.worlds = [i[1] for i in self.con.cursor().execute('SELECT * FROM worlds').fetchall()]
        self.world = None
        self.main_sprites = pygame.sprite.Group()
        self.menu_sprites = pygame.sprite.Group()
        self.select_sprites = pygame.sprite.Group()
        self.statistic_sprites = pygame.sprite.Group()
        self.worlds_sprites = pygame.sprite.Group()
        self.no_worlds = None
        if not self.worlds:
            self.no_worlds = Button('there are no worlds :(', FONT, 80, 'white', (400, 390), self.worlds_sprites,
                                    animate=True)
        self.bg = Image('mainbg.png', (0, 0), self.main_sprites)
        self.logo = Image('logo.png', (148, 93), self.main_sprites, animate=True)
        self.play = Button('PLAY', FONT, 80, 'white', (400, 350), self.menu_sprites, animate=True)
        self.settings = Button('STATISTICS', FONT, 80, 'white', (400, 430), self.menu_sprites, animate=True)
        self.exit = Button('EXIT', FONT, 80, 'white', (400, 510), self.menu_sprites, animate=True)
        self.back = Button('BACK', FONT, 80, 'white', (400, 510), self.statistic_sprites, self.select_sprites,
                           self.worlds_sprites, animate=True)
        self.load = Button('LOAD', FONT, 80, 'white', (400, 350), self.select_sprites, animate=True)
        self.selected = Button(self.worlds[0], FONT, 65, 'white', (400, 370), self.worlds_sprites, animate=True)
        self.previous = Button('<', FONT, 80, 'white', (self.selected.rect.left - 25, 370), self.worlds_sprites,
                               animate=True)
        self.next = Button('>', FONT, 80, 'white', (self.selected.rect.right + 25, 365), self.worlds_sprites,
                           animate=True)
        self.new = Button('NEW', FONT, 80, 'white', (400, 430), self.select_sprites, animate=True)
        self.sprite_update = [self.main_sprites, self.menu_sprites]
        self.running = True

    def main_loop(self) -> None:
        while self.running:
            self.check_events()
            self.screen.fill((0, 0, 0))
            for group in self.sprite_update:
                group.draw(self.screen)
                group.update()
            pygame.display.flip()
            CLOCK.tick(FPS)

    def check_events(self) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            if event.type == pygame.MOUSEBUTTONDOWN:
                if self.menu_sprites in self.sprite_update:
                    if self.play.rect.collidepoint(event.pos):
                        self.sprite_update.remove(self.menu_sprites)
                        self.sprite_update.append(self.select_sprites)
                    elif self.settings.rect.collidepoint(event.pos):
                        self.sprite_update.remove(self.menu_sprites)
                        self.sprite_update.append(self.statistic_sprites)
                    elif self.exit.rect.collidepoint(event.pos):
                        self.con.close()
                        sys.exit()
                elif self.statistic_sprites in self.sprite_update:
                    if self.back.rect.collidepoint(event.pos):
                        self.sprite_update.remove(self.statistic_sprites)
                        self.sprite_update.append(self.menu_sprites)
                elif self.select_sprites in self.sprite_update:
                    if self.back.rect.collidepoint(event.pos):
                        self.sprite_update.remove(self.select_sprites)
                        self.sprite_update.append(self.menu_sprites)
                    if self.load.rect.collidepoint(event.pos):
                        self.sprite_update.remove(self.select_sprites)
                        self.sprite_update.append(self.worlds_sprites)
                    if self.new.rect.collidepoint(event.pos):
                        self.create_world()
                elif self.worlds_sprites in self.sprite_update:
                    if self.no_worlds and self.no_worlds.rect.collidepoint(event.pos):
                        self.create_world()
                    if self.back.rect.collidepoint(event.pos):
                        self.sprite_update.remove(self.worlds_sprites)
                        self.sprite_update.append(self.select_sprites)

    def create_world(self) -> None:
        mp = random.choice(os.listdir('maps'))
        existed = [i[0] for i in self.con.cursor().execute('SELECT name FROM worlds').fetchall()]
        with open('data/galaxy_names.txt', 'r') as names:
            list_of_names = names.read().split('\n')
            if len(existed) >= len(list_of_names):
                print('Name error')
                sys.exit()
            name = random.choice(names.read().split('\n'))
            while name in existed:
                name = random.choice(list_of_names)
        self.con.cursor().execute('INSERT INTO worlds VALUES (NULL, "{}", "{}")'.format(name, mp))
        self.con.commit()
        self.world = name
        self.running = False


class Button(pygame.sprite.Sprite):
    def __init__(self, text: str, font: str, size: int, color, pos: tuple, *group, animate=False) -> None:
        super().__init__(*group)
        self.text = text
        self.image = text_surface(text, font, size, color)
        self.image.set_alpha(150)
        self.rect = self.image.get_rect()
        self.def_pos = pos
        self.rect.center = self.def_pos
        self.animate = animate
        if self.animate:
            self.anim_f = False
            self.anim_c = 0

    def update(self) -> None:
        if self.rect.collidepoint(pygame.mouse.get_pos()):
            self.image.set_alpha(255)
            if self.animate:
                self.anim_c += 1
                if self.anim_c == FPS // 3:
                    self.anim_c = 0
                    self.anim_f = not self.anim_f
                    if self.anim_f:
                        self.rect.y += 2
                    else:
                        self.rect.y -= 2
        else:
            self.image.set_alpha(150)
            self.rect.center = self.def_pos
            if self.animate:
                self.anim_f = False
                self.anim_c = 0


class Image(pygame.sprite.Sprite):
    def __init__(self, name: str, pos: tuple, *group, animate=False):
        super().__init__(*group)
        self.image = load_image(name)
        self.rect = self.image.get_rect()
        self.rect.topleft = pos
        self.animate = animate
        if self.animate:
            self.anim_f = False
            self.anim_c = 0

    def update(self):
        if self.animate:
            self.anim_c += 1
            if self.anim_c == FPS:
                self.anim_c = 0
                self.anim_f = not self.anim_f
                if self.anim_f:
                    self.rect.y += 2
                else:
                    self.rect.y -= 2


class Player(pygame.sprite.Sprite):
    def __init__(self, x, y, *group) -> None:
        super().__init__(*group)
        self.image = load_image('solar.png')
        self.rect = self.image.get_rect()


class Tile(pygame.sprite.Sprite):
    def __init__(self, name, x, y, *group) -> None:
        super().__init__(*group)
        if name == 'p':
            self.image = load_image('random_planets/' + random.choice(os.listdir('sprites/random_planets')),
                                    folder='sprites/')
        elif name == 's':
            self.image = load_image('solar.png')
        elif name == 'a':
            pass
        self.rect = self.image.get_rect()
        self.rect.topleft = (x, y)


class AnimatedSprite(pygame.sprite.Sprite):
    def __init__(self, sheet, columns, rows, x, y, *group):
        super().__init__(*group)
        self.frames = []
        self.cut_sheet(sheet, columns, rows)
        self.cur_frame = 0
        self.image = self.frames[self.cur_frame]
        self.rect = self.rect.move(x, y)
        self.speed = random.randint(2, 10)

    def cut_sheet(self, sheet, columns, rows):
        self.rect = pygame.Rect(0, 0, sheet.get_width() // columns, sheet.get_height() // rows)
        for j in range(rows):
            for i in range(columns):
                frame_location = (self.rect.w * i, self.rect.h * j)
                self.frames.append(sheet.subsurface(pygame.Rect(frame_location, self.rect.size)))

    def update(self):
        self.cur_frame = (self.cur_frame + self.speed / 100) % len(self.frames)
        self.image = self.frames[int(self.cur_frame)]


def text_surface(text, font, size, color) -> pygame.Surface:
    font = pygame.font.Font(font, size)
    text = font.render(text, True, pygame.Color(color))
    return text


def load_image(path, ckey=None, folder='sprites/') -> pygame.Surface:
    path = folder + path
    if not os.path.isfile(path):
        print('Файла с именем "{}" не существует.'.format(path))
        sys.exit()
    image = pygame.image.load(path)
    if ckey is None:
        image = image.convert_alpha()
    return image


if __name__ == '__main__':
    pygame.init()
    menu = MainMenu()
    while menu.running:
        menu.main_loop()
    if menu.world is not None:
        game = Game(menu.world)
        while game.running:
            game.main_loop()
