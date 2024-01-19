import pygame
import os
import sys
import sqlite3
import random
import math
import json

W, H = 800, 600
FPS = 60
S = 75
CLOCK = pygame.time.Clock()
FONT = 'data/ThaleahFat.ttf'
DB = 'data/data.db'
PRICES = {0: 100, 1: 1000, 2: 5000, 3: 15000, 4: 50000, 5: 100000}
PASSIVE = {0: 0, 1: 10, 2: 30, 3: 100, 4: 300, 5: 500, 6: 1000}
EMPTY_DICT = json.loads(open('data/empty.json').read())


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
        self.asteroid_sprites = pygame.sprite.Group()
        self.system_sprites = pygame.sprite.Group()
        self.player_sprites = pygame.sprite.Group()
        self.layout_sprites = pygame.sprite.Group()
        self.pause_sprites = pygame.sprite.Group()
        self.menu_sprites = pygame.sprite.Group()
        self.back_button = Button('back', FONT, 80, 'white', (400, 500), self.pause_sprites, self.menu_sprites)
        self.save_button = Button('save', FONT, 80, 'white', (400, 340), self.pause_sprites)
        self.close_button = Button('close', FONT, 80, 'white', (400, 420), self.pause_sprites)
        self.pause_text = text_surface('PAUSED', FONT, 120, 'white')
        self.buy_button = Button('colonise for ' + str(PRICES[0]), FONT, 80, 'white', (400, 420), self.menu_sprites)
        self.pause_text_pos = 400, 100
        self.pause_button = Button('||', FONT, 60, 'white', (782, 28), self.layout_sprites)
        self.stars = self.stars_fill()
        self.planets = self.planets_fill()
        self.all_sprites = [self.asteroid_sprites, self.system_sprites]
        self.system, self.crds = self.load_map()
        if self.system:
            self.load_system(self.system)
        self.pos_now = list(self.crds)
        self.pos_to = list(self.crds)
        self.pos_to[0] += 10
        self.speed = 3
        self.player = Player(self.player_sprites)
        self.balance = int(self.con.cursor().execute(
            'SELECT balance FROM worlds WHERE name = "{}"'.format(self.world)).fetchall()[0][0])
        self.balance_text = Button('balance: ' + str(self.balance), FONT, 60, 'white', (400, 550), self.layout_sprites)
        self.json_file = f'data/{self.world}.json'
        if os.path.exists(self.json_file):
            self.buyed = open(self.json_file, 'r').read()
            if self.buyed:
                self.buyed = json.loads(self.buyed)
            else:
                self.buyed = EMPTY_DICT[:]
        else:
            self.buyed = EMPTY_DICT[:]
        print(self.buyed)
        self.passive = self.count_passive(self.buyed)
        self.paused = False
        self.menued = False
        self.menued_planet = None
        self.running = True

    def main_loop(self) -> None:
        while self.running:
            self.check_events()
            self.screen.fill((0, 0, 0))
            self.screen.blit(self.bg, self.bg.get_rect(topleft=self.bg_pos))
            if self.paused:
                self.pause_sprites.draw(self.screen)
                self.pause_sprites.update()
                self.screen.blit(self.pause_text, self.pause_text.get_rect(center=self.pause_text_pos))
            elif self.menued:
                self.screen.blit(pygame.transform.scale_by(self.menued_planet.image, 6), (240, 50))
                self.menued_planet.update()
                self.menu_sprites.draw(self.screen)
                self.menu_sprites.update()
            else:
                if ((self.pos_now[0] - self.pos_to[0]) ** 2 + (self.pos_now[1] - self.pos_to[1]) ** 2) ** 0.5 > 6:
                    self.player.moving = True
                    angle = math.atan2(self.pos_now[1] - self.pos_to[1], self.pos_to[0] - self.pos_now[0])
                    self.pos_now[0] += self.speed * math.cos(angle)
                    self.pos_now[1] -= self.speed * math.sin(angle)
                else:
                    self.player.moving = False
                for group in self.all_sprites:
                    if self.player.moving:
                        for sprite in group.sprites():
                            sprite.rect.center = sprite.pos[0] - self.pos_now[0], sprite.pos[1] - self.pos_now[1]
                    group.draw(self.screen)
                    group.update()
                for group in (self.player_sprites, self.layout_sprites):
                    group.draw(self.screen)
                    group.update()
            self.balance += self.passive / 60
            for group in self.balance_text.groups():
                group.remove(self.balance_text)
            self.balance_text = Button('balance: ' + str(int(self.balance)), FONT, 60, 'white', (400, 550),
                                       self.layout_sprites, self.menu_sprites)
            pygame.display.flip()
            CLOCK.tick(FPS)

    def check_events(self) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.save()
                self.running = False
            if event.type == pygame.MOUSEBUTTONDOWN:
                if self.paused:
                    if self.back_button.rect.collidepoint(event.pos):
                        self.paused = False
                    if self.save_button.rect.collidepoint(event.pos):
                        self.save()
                        self.paused = False
                    if self.close_button.rect.collidepoint(event.pos):
                        self.save()
                        self.running = False
                elif self.menued:
                    if self.back_button.rect.collidepoint(event.pos):
                        self.menued = False
                    if self.buy_button.rect.collidepoint(event.pos):
                        k = self.buyed[self.system - 1][self.menued_planet.id[3]]
                        if k < len(PRICES):
                            price = PRICES[k]
                            if self.balance >= price:
                                self.balance -= price
                                self.buyed[self.system - 1][self.menued_planet.id[3]] += 1
                                self.passive = self.count_passive(self.buyed)
                                self.menued = False
                else:
                    if event.button == 3:
                        if self.system:
                            if ((self.pos_now[0] - self.pos_to[0]) ** 2 + (
                                    self.pos_now[1] - self.pos_to[1]) ** 2) ** 0.5 <= 6:
                                self.pos_to[0] += event.pos[0] - 400
                                self.pos_to[1] += event.pos[1] - 300
                            else:
                                self.pos_to[0] = self.pos_now[0] + event.pos[0] - 400
                                self.pos_to[1] = self.pos_now[1] + event.pos[1] - 300
                            self.player.rotate(event.pos)
                    if self.pause_button.rect.collidepoint(event.pos) and event.button == 1:
                        self.paused = True
                    else:
                        collide = pygame.sprite.spritecollide(self.player, self.system_sprites, False)
                        if event.button == 1 and collide:
                            sprite = collide[0]
                            if sprite.id[0] == 'p':
                                self.menued_planet = sprite
                                k = self.buyed[self.system - 1][self.menued_planet.id[3]]
                                self.menu_sprites.remove(self.buy_button)
                                if k == 0:
                                    self.buy_button = Button('colonise for ' + str(PRICES[k]), FONT, 80, 'white',
                                                             (400, 420),
                                                             self.menu_sprites)
                                elif k < len(PRICES):
                                    self.buy_button = Button('upgrade for ' + str(PRICES[k]), FONT, 80, 'white',
                                                             (400, 420), self.menu_sprites)
                                else:
                                    self.buy_button = Button('maximum lvl' + str(PRICES[k]), FONT, 80, 'white',
                                                             (400, 420), self.menu_sprites)
                                self.menued = True
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.paused = -self.paused
                elif event.key == pygame.K_SPACE:  # TODO: check for max lvl
                    self.system = self.system % 9 + 1
                    self.load_system(self.system)
                    self.bg_pos = -random.randrange(2200), -random.randrange(2400)
                    self.pos_to[0] -= 5
                    self.pos_to[1] -= 5

    def load_map(self) -> tuple:
        mp, system, crds = self.con.cursor().execute('SELECT * FROM worlds WHERE name = "{}"'.format(
            self.world)).fetchall()[0][2:5]
        try:
            with open('maps/' + mp) as map_file:
                level = [line.strip() for line in map_file]
                default_data = [int(i) for i in level[0].split(': ')[1].split(' ')]
                if system is None:
                    system = default_data[0]
                else:
                    system = int(system)
                if crds is None:
                    crds = default_data[1:3]
                else:
                    crds = [int(i) for i in crds.split(' ')]
                return system, crds
        except FileNotFoundError:
            print('File "{}" not found'.format(mp))
            sys.exit()

    def load_system(self, n: int) -> None:
        self.asteroid_sprites.empty()
        self.system_sprites.empty()
        try:
            with open('systems/system' + str(self.system) + '.txt') as system_file:
                level = [line.strip() for line in system_file]
                for y in range(len(level)):
                    for x in range(len(level[0])):
                        if level[y][x] == 's':
                            AnimatedSprite('s', load_image(self.stars[n], folder='sprites/random_stars/'), 50,
                                           1, x * S - 25, y * S - 25, self.system_sprites)
                        elif level[y][x] in '123':
                            AnimatedSprite(f'p: {level[y][x]}', load_image(
                                self.planets[n - 1][int(level[y][x])], folder='sprites/random_planets/'), 10,
                                           10, x * S, y * S, self.system_sprites)
                        elif level[y][x] == 'a':
                            Tile(x * S, y * S, self.asteroid_sprites)
        except FileNotFoundError:
            print('File "system{}" not found'.format(self.system))
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

    def count_passive(self, data) -> int:
        k = 0
        for system in data:
            for i, j in system.items():
                k += PASSIVE[j]
        return k

    def save(self) -> None:
        self.con.cursor().execute('UPDATE worlds SET system = {}, crds = "{}", balance = {} WHERE name = "{}"'.format(
            self.system, f'{int(self.pos_now[0])} {int(self.pos_now[1])}', int(self.balance), self.world))
        self.con.commit()
        with open(self.json_file, 'w') as jf:
            jf.writelines(json.dumps(self.buyed, indent=4))


class MainMenu:
    def __init__(self) -> None:
        pygame.init()
        self.screen = pygame.display.set_mode((W, H))
        pygame.display.set_icon(load_image('ico.png'))
        pygame.display.set_caption('Main menu')
        self.con = sqlite3.connect(DB)
        self.worlds = [i[0] for i in self.con.cursor().execute('SELECT name FROM worlds').fetchall()]
        self.best = [i[0] for i in self.con.cursor().execute('SELECT balance FROM worlds').fetchall() if
                     i[0] is not None]
        if len(self.best) > 0:
            self.best = max(self.best)
        else:
            self.best = 'None :('
        self.world = None
        self.main_sprites = pygame.sprite.Group()
        self.menu_sprites = pygame.sprite.Group()
        self.select_sprites = pygame.sprite.Group()
        self.statistic_sprites = pygame.sprite.Group()
        self.worlds_sprites = pygame.sprite.Group()
        self.no_worlds = None
        if not self.worlds:
            self.no_worlds = Button('there are no worlds :(', FONT, 80, 'white', (400, 375), self.worlds_sprites,
                                    animate=True)
        else:
            self.selected_world = 0
            self.selected = None
            self.previous = None
            self.next = None
            self.delete = None
            self.existed_worlds()
        self.bg = Image('mainbg.png', (0, 0), self.main_sprites)
        self.logo = Image('logo.png', (148, 93), self.main_sprites, animate=True)
        self.play = Button('PLAY', FONT, 80, 'white', (400, 350), self.menu_sprites, animate=True)
        self.settings = Button('STATISTICS', FONT, 80, 'white', (400, 430), self.menu_sprites, animate=True)
        self.exit = Button('EXIT', FONT, 80, 'white', (400, 510), self.menu_sprites, animate=True)
        self.back = Button('BACK', FONT, 80, 'white', (400, 510), self.statistic_sprites, self.select_sprites,
                           self.worlds_sprites, animate=True)
        self.statistic = Button('BEST: ' + str(self.best), FONT, 80, 'white', (400, 400),
                                self.statistic_sprites, animate=True)
        self.load = Button('LOAD', FONT, 80, 'white', (400, 350), self.select_sprites, animate=True)
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
                    if self.back.rect.collidepoint(event.pos):
                        self.sprite_update.remove(self.worlds_sprites)
                        self.sprite_update.append(self.select_sprites)
                    elif self.no_worlds and self.no_worlds.rect.collidepoint(event.pos):
                        self.create_world()
                    elif self.next.rect.collidepoint(event.pos):
                        self.selected_world = (self.selected_world + 1) % len(self.worlds)
                        self.existed_worlds()
                    elif self.previous.rect.collidepoint(event.pos):
                        self.selected_world = (self.selected_world - 1) % len(self.worlds)
                        self.existed_worlds()
                    elif self.selected.rect.collidepoint(event.pos):
                        self.world = self.selected.text
                        self.running = False
                    elif self.delete.rect.collidepoint(event.pos) and len(self.worlds) > 1:
                        self.worlds.remove(self.selected.text)
                        self.selected_world = (self.selected_world + 1) % len(self.worlds)
                        self.existed_worlds()
                        self.con.cursor().execute('DELETE FROM worlds WHERE name = "{}"'.format(self.selected.text))
                        self.con.commit()
                        if os.path.exists(f'data/{self.world}.json'):
                            os.remove(f'data/{self.world}.json')

    def create_world(self) -> None:
        mp = random.choice(os.listdir('maps'))
        existed = [i[0] for i in self.con.cursor().execute('SELECT name FROM worlds').fetchall()]
        with open('data/galaxy_names.txt', 'r') as names:
            list_of_names = names.read().split('\n')
            if len(existed) >= len(list_of_names):
                print('Name error')
                sys.exit()
            name = random.choice(list_of_names)
            while name in existed:
                name = random.choice(list_of_names)
        self.con.cursor().execute('INSERT INTO worlds VALUES (NULL, "{}", "{}", NULL, NULL, 100)'.format(name, mp))
        self.con.commit()
        self.world = name
        self.running = False

    def existed_worlds(self) -> None:
        self.worlds_sprites.remove(self.next, self.selected, self.previous)
        self.selected = Button(self.worlds[self.selected_world], FONT, 65, 'white', (400, 370), self.worlds_sprites,
                               animate=True)
        self.previous = Button('<', FONT, 80, 'white', (self.selected.rect.left - 30, 371),
                               self.worlds_sprites,
                               animate=True)
        self.next = Button('>', FONT, 80, 'white', (self.selected.rect.right + 30, 366),
                           self.worlds_sprites,
                           animate=True)
        if len(self.worlds) > 1:
            self.delete = Button('delete', FONT, 50, 'white', (400, 570), self.worlds_sprites, animate=True)
        else:
            self.delete = Button('', FONT, 1, 'white', (400, 570), self.worlds_sprites, animate=True)


class Button(pygame.sprite.Sprite):
    def __init__(self, text: str, font: str, size: int, color: str, pos: tuple, *group, animate=False) -> None:
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

    def retext(self, text) -> None:
        self.text = text
        self.rect = self.image.get_rect()
        self.rect.center = self.def_pos

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
    def __init__(self, name: str, pos: tuple, *group, animate=False) -> None:
        super().__init__(*group)
        self.image = load_image(name)
        self.rect = self.image.get_rect()
        self.rect.topleft = pos
        self.animate = animate
        if self.animate:
            self.anim_f = False
            self.anim_c = 0

    def update(self) -> None:
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
    def __init__(self, *group) -> None:
        super().__init__(*group)
        self.frames = []
        self.cut_sheet(load_image('ship.png'), 2, 2)
        self.cur_frame = 0
        self.angle = 90
        self.pos = 400, 300
        self.speed = 3
        self.image = self.frames[self.cur_frame]
        self.rect = self.image.get_rect(center=self.pos)
        self.moving = False

    def cut_sheet(self, sheet, columns, rows) -> None:
        self.rect = pygame.Rect(0, 0, sheet.get_width() // columns, sheet.get_height() // rows)
        for j in range(rows):
            for i in range(columns):
                frame_location = (self.rect.w * i, self.rect.h * j)
                self.frames.append(sheet.subsurface(pygame.Rect(frame_location, self.rect.size)))

    def rotate(self, pos) -> None:
        self.angle = math.degrees(math.atan2(-pos[1] + 300, pos[0] - 400))

    def update(self) -> None:
        if self.moving:
            self.cur_frame = (self.cur_frame + 0.8) % len(self.frames)
        else:
            self.cur_frame = 0
        self.image = pygame.transform.rotate(self.frames[int(self.cur_frame)], int(self.angle) - 90)
        self.rect = self.image.get_rect(center=self.pos)


class Tile(pygame.sprite.Sprite):
    def __init__(self, x: int, y: int, *group) -> None:
        super().__init__(*group)
        self.image = load_image(random.choice(os.listdir('sprites/random_asteroids')),
                                folder='sprites/random_asteroids/')
        self.pos = x, y
        self.rect = self.image.get_rect()
        self.rect.center = self.pos


class AnimatedSprite(pygame.sprite.Sprite):
    def __init__(self, t: str, sheet: pygame.Surface, columns: int, rows: int, x: int, y: int, *group) -> None:
        super().__init__(*group)
        self.id = t
        self.frames = []
        self.cut_sheet(sheet, columns, rows)
        self.cur_frame = 0
        self.image = self.frames[self.cur_frame]
        self.pos = x, y
        self.rect.center = self.pos
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
    while True:
        menu = MainMenu()
        while menu.running:
            menu.main_loop()
        if menu.world:
            game = Game(menu.world)
            while game.running:
                game.main_loop()
        else:
            pygame.quit()
            sys.exit()
