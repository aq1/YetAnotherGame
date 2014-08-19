#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import random
import sys
import gc
import collections

import kivy

from kivy.app import App

from kivy.uix.widget import Widget
from kivy.uix.image import Image
from kivy.uix.boxlayout import BoxLayout

from kivy.core.window import Window
from kivy.core.audio import SoundLoader

from kivy.clock import Clock
from kivy.animation import Animation

from kivy.properties import NumericProperty, BooleanProperty, StringProperty


PLATFORM = kivy.platform()

# if PLATFORM is not 'android':
    # pass
    # Window.size = (1100, 650)


FPS = 1.0 / 60.0
FACTOR = Window.width // 12
GAME_SPEED = float(Window.width) / 300
SLOW_GAME_SPEED = int(GAME_SPEED / 2)

TIME_SEGMENT = 0.5
FUNCTION_TIMING = 0.1

BEZIER_PRECISION = 0.2
MIN_DISTANCE = 15
DISTANCE = int(3.5 * FACTOR)
FIRST_POINT = [1.75 * Window.width, Window.height // 2]

JUMP_DISTANCE = Window.width // 23
IMMORTALITY_TIME = 3
HERO_LIVES = 10
MAX_HERO_LIVES = 3
COIN_VALUE = 10
BONUS_VALUE = 200
JUMP_POINT_VALUE = 30
MAX_ANGLE = 25

ISLANDS_BEFORE_GUARDIAN = 30
ENEMY_PROBABILITY = 3
BONUS_PROBABILITY = 5

JUMP_LABELS = (None, None, 'Triple', 'Quadro', 'Multiply')


def fibonacci_decorator(function):
    prevs = [0, 1]

    def _f():
        out = function(*prevs)
        prevs[0], prevs[1] = prevs[1], out
        return out
    return _f


def keep_last_point(function):
    points = [FIRST_POINT]

    def decorator(self):
        result = function(self, points)
        del points[:-1]
        return result

    return decorator


def bezier(points, precision=BEZIER_PRECISION):
    assert len(points) == 4, len(points)
    coords = []

    t = precision
    while t <= 1:
        x = [((1 - t) ** 3) * points[0][0],
             3 * t * ((1 - t) ** 2) * points[1][0],
             3 * (t ** 2) * (1 - t) * points[2][0],
             (t ** 3) * points[3][0]]
        y = [((1 - t) ** 3) * points[0][1],
             3 * t * ((1 - t) ** 2) * points[1][1],
             3 * (t ** 2) * (1 - t) * points[2][1],
             (t ** 3) * points[3][1]]
        coords.append((int(sum(x)), int(sum(y))))
        t += precision
    return coords


class Hero(Image):

    _factor = NumericProperty(FACTOR)
    _angle = NumericProperty(0)
    __speed = NumericProperty()
    __lives = NumericProperty(HERO_LIVES)
    __jump_init_y = NumericProperty(Window.height)
    is_immortal = BooleanProperty(False)

    def __init__(self):
        super(Hero, self).__init__()

        # Well... Don't know if that is correct.
        self.__velocity_up = 0.01 * FACTOR / 6.64
        self.__velocity_down = 1.2 * self.__velocity_up

        self.__max_up_speed_factor = 0.9
        self.__max_down_speed_factor = -1.1

        self.__touch = False
        self.__jumps_count = 0

        self.__intersection_coords = collections.namedtuple(
            'Coords', ('x', 'y', 'right', 'top'))

        self.center = (FACTOR, Window.center[1])
        self.source = 'texture/hero_normal_moving.zip'
        # self.source = 'texture/1.png'
        self.anim_delay = 0.05

        Clock.schedule_interval(self.__move, FPS)

    def __up(self, *args):
        # print 'up'
        if not self.__touch and self.y - self.__jump_init_y >= JUMP_DISTANCE:
            # print 'JUMP_DISTANCE TRUE'
            self.__jump_init_y = Window.height
            self.down()

        if self.__speed > self.__max_up_speed_factor * self.parent.get_speed():
            # print '> True'
            return

        self.__increase_angle()
        self.__speed += self.__velocity_up

    def __down(self, *args):
        # print 'down'
        if (self.__speed <
                self.__max_down_speed_factor * self.parent.get_speed()):
            return

        self.__speed -= self.__velocity_down
        self.__decrease_angle()

    def __increase_angle(self):
        if self._angle < MAX_ANGLE:
            self._angle += 1

    def __decrease_angle(self):
        if self._angle > -10:
            self._angle -= 1

    def __move(self, timing):
        ''' Check statement'''

        # print 'Move'
        if self.top <= 0:
            self.jump(bottom=True)
        elif self.y > Window.height + self.height:
            self.top = Window.height + self.height
            # return
        self.y += self.__speed * self.parent.get_speed()

    def __become_mortal(self, timing):
        self.is_immortal = False
        self.color = (1, 1, 1, 1)
        Clock.unschedule(self.__blink)

    def __blink(self, timing):
        self.color = (1, 1, 1, 1 - self.color[-1] + 0.5)

    def __check_jumps(self):
        if self.__jumps_count > 5:
            self.__jumps_count -= 1

        if self.__jumps_count >= 3:
            self.parent.add_points(self.__jumps_count * JUMP_POINT_VALUE)
            self.parent.display_jump_label(self.__jumps_count - 1)

        # print self.__jumps_count, JUMP_LABELS[self.__jumps_count - 1]

    def get_intersection_coords(self):
        x, y = self.x + self.width / 3.0, self.y
        right, top = x + 2 * self.width / 3.0, y + 4 * self.height / 5.0
        return self.__intersection_coords(x, y, right, top)

    def lose_life(self):
        if self.is_immortal:
            return
        self.__lives -= 1

        if self.__lives == 0:
            self.parent.game_over()

        self.is_immortal = True
        Clock.schedule_once(self.__become_mortal, IMMORTALITY_TIME)
        Clock.schedule_interval(self.__blink, 0.1)

    def add_life(self):
        self.__lives += 1

    def jump(self, bottom=False):
        # print 'Jump'
        if bottom:
            self.lose_life()
        else:
            self.y += FACTOR / 4.0
            self.__jumps_count += 1
            self.__check_jumps()

        self._angle = MAX_ANGLE / 2.0
        self.__jump_init_y = self.y
        self.__speed = self.__max_up_speed_factor * self.parent.get_speed()
        Clock.unschedule(self.__down)
        Clock.schedule_interval(self.__up, FPS)

    def roll(self):
        pass

    def up(self):
        self.__touch = True
        self.__jumps_count = 0
        self.__jump_init_y = Window.height
        Clock.unschedule(self.__down)
        Clock.schedule_interval(self.__up, FPS)

    def down(self):
        self.__touch = False
        Clock.unschedule(self.__up)
        Clock.schedule_interval(self.__down, FPS)


class FlyingObject(Image):

    _factor = NumericProperty(FACTOR)

    def __init__(self, pos=None, speed_factor=1.1):
        super(FlyingObject, self).__init__()

        self.__speed_factor = speed_factor

        if not pos:
            interval = (0, int(Window.height - self.height))
            pos = Window.width, random.randint(*interval)

        self.pos = pos

        Clock.schedule_interval(self._move, FPS)
        # try:
        #     Clock.schedule_interval(
        #         self._check_if_need_to_create_next, 2 * FPS)
        # except AttributeError:
        #     pass

    # def _deal_with_collision(self):
    #     '''Overwrite in subclasses'''
    #     pass

    def _collides_with(self, obj):
        '''Overwrite in subclasses'''
        return False

    def _check_if_need_to_create_next(self, timing):
        '''Overwrite in subclasses'''
        return False

    def _move(self, *args):
        if self.right <= 0:
            self.parent.remove_widget(self)
            return False

        if self.x <= self.parent.hero.right:
            self._collides_with(self.parent.hero)

        self.x -= self.get_speed()

    def get_speed(self):
        try:
            return self.__speed_factor * self.parent.get_speed()
        except AttributeError:
            return 0


class Coin(FlyingObject):

    def __init__(self, pos, *args):
        super(Coin, self).__init__(pos, *args)

        self.source = 'texture/coin.png'

    def _deal_with_collision(self, obj):
        Clock.unschedule(self._move)

        x, y = obj.center
        anim = Animation(x=x, y=y, size=(0, 0), d=0.4)
        anim.bind(on_start=lambda *args: self.parent.collect_coin(self))
        anim.start(self)

    def _check_if_need_to_create_next(self, *args):
        try:
            width = self.parent.width
        except AttributeError:
            return True

        if self.right <= width - random.randint(100, 500):
            return not self.parent.add_coins()

    def _collides_with(self, obj):
        assert self.x <= obj.right

        rectangle = obj.get_intersection_coords()
        if self.right <= rectangle.x:
            return False

        if self.y <= rectangle.top and self.top >= rectangle.y:
            self._deal_with_collision(obj)


class Island(FlyingObject):
    _offset = NumericProperty(0)

    def __init__(self, **kw):
        super(Island, self).__init__(**kw)

        self.source = 'texture/island_small_1.png'
        # self._offset = random.choice((0, 30, -30))
        self._offset = -30
        self.allow_stretch = True

        if random.randint(0, 10) < ENEMY_PROBABILITY:
            # I need parent widget. Better solution? I don't know
            Clock.schedule_once(self.__add_guardian, 0.05)
            # self.__add_bonus()

        Clock.schedule_interval(self._check_if_need_to_create_next, FPS)

    def __add_guardian(self, damn_timing=None):
        if self.parent.number_of_islands < ISLANDS_BEFORE_GUARDIAN:
            return False

        if random.randint(0, 10) < BONUS_PROBABILITY:
            self.__add_bonus()

        guardian = Guardian(
            pos=(random.randint(int(self.x), int(self.right) - FACTOR / 2), self.top))
        self.add_widget(guardian)

    def __add_bonus(self):
        self.add_widget(
            Bonus(pos=(random.randint(int(self.x), int(self.right) - FACTOR / 2), self.top)))

    def __rectangle_and_segment_intersection(self, rectangle, line):
        x_min, x_max, y_min, y_max = (rectangle.x, rectangle.right,
                                      rectangle.y, rectangle.top)

        x_a, y_a, x_b, y_b = line

        t, d_t = 0, 0.1
        while t <= 1:
            if (x_min <= (x_a + (x_b - x_a) * t) <= x_max and
                    y_min <= (y_a + (y_b - y_a) * t) <= y_max):
                return True
            t += d_t
        return False

    def _check_if_need_to_create_next(self, *args):
        if self.right <= self.parent.get_distance() - random.randint(0, 50):
            self.parent.add_island()
            return False

    def _collides_with(self, obj):
        # lines = ((self.x, self.top, self.center[0] + self._offset, self.y),
        #         (self.x, self.top, self.right, self.top),
        #         (self.right, self.top, self.center[0] + self._offset, self.y),)
        # functions = (self.parent.hero_collided, self.parent.hero.jump,
        #              self.parent.hero.roll)
        # for func, line in zip(functions, (damage_line, jump_line, roll_line)):
        #     if self.__rectangle_and_segment_intersection(self.parent.hero, line):
        #         func()
        #         return

        damage_line = self.x, self.top, self.center[0] + self._offset, self.y
        jump_line = self.x, self.top, self.right, self.top
        roll_line = self.right, self.top, self.center[0] + self._offset, self.y

        hero = self.parent.hero
        rectangle = hero.get_intersection_coords()

        if hero.y >= self.top - FACTOR / 4.5:
            # Don't forget to union this
            # print self.x
            # pass
            if self.__rectangle_and_segment_intersection(rectangle, jump_line):
                hero.jump()
            # print 'JUMP'

        elif (not hero.is_immortal and
              self.__rectangle_and_segment_intersection(rectangle, damage_line)):
            self.parent.hero_collided()
            # print 'COLLIDED'

        # elif (self.__rectangle_and_segment_intersection(rectangle, roll_line)):
        #     hero.roll()
            # print 'ROLL'


class MovingObject(Image):

    ''' Unlike FlyingObject it's walking on island'''
    _factor = NumericProperty(FACTOR)
    __speed_factor = NumericProperty()

    def __init__(self, pos):
        super(MovingObject, self).__init__()
        self.pos = pos
        Clock.schedule_interval(self._move, FPS)

    def _collides_with(self, obj):
        assert self.x <= obj.right

        rectangle = obj.get_intersection_coords()
        if self.right <= rectangle.x:
            return False

        if self.y <= rectangle.top and self.top >= rectangle.y:
            Clock.unschedule(self._move)
            obj.parent.add_points(BONUS_VALUE)
            self.parent.remove_widget(self)
            return True

    def _move(self, timing):
        if self.right <= 0:
            self.parent.remove_widget(self)
            return False

        if (self.x <= self.parent.parent.hero.right and
                self._collides_with(self.parent.parent.hero)):
            return False

        self.x -= self.parent.get_speed()


class Guardian(MovingObject):

    def __init__(self, pos):
        super(Guardian, self).__init__(pos)

        self.__speed_left = 1.2
        self.__speed_right = 0.5
        self.__current_speed = random.choice(
            (self.__speed_left, self.__speed_right))
        # self.__current_speed = self.__speed_left

        self.source = 'texture/enemy_draft.png'

        if self.__current_speed is self.__speed_left:
            Clock.schedule_interval(self.__check_if_sees, FPS / 2)
        # self.__current_speed = self.__speed_right

    def __collision_with(self, obj):
        assert self.x <= obj.right

        rectangle = obj.get_intersection_coords()
        if self.right <= rectangle.x:
            return False

        if self.y <= rectangle.top and self.top >= rectangle.y:
            if self.__current_speed == 1:
                self.__attack(obj)
                return False
            else:
                self.__destroy()
                return True

    def __get_hero(self):
        try:
            return self.parent.parent.hero
        except AttributeError:
            return None

    def __check_if_sees(self, timing=None):
        hero = self.__get_hero()

        if (hero and self.x - hero.right <= Window.height / 2.0
                and self.y <= hero.top):
            self.__current_speed = 1
            return False

    def __attack(self, hero):
        hero.parent.hero_collided()

    def __destroy(self):
        self.parent.remove_widget(self)

    def __get_intercetion_coords(self):
        offset = self.width / 5
        return self.x + offset, self.right - offset

    def _move(self, timing):
        hero = self.__get_hero()

        if hero and self.x <= hero.right:
            if self.__collision_with(hero):
                return False

        if self.right <= 0:
            self.parent.remove_widget(self)
            return False

        x, right = self.__get_intercetion_coords()
        if x <= self.parent.x:
            self.__current_speed = self.__speed_right
            Clock.unschedule(self.__check_if_sees)
        elif right >= self.parent.right:
            self.__current_speed = self.__speed_left
            Clock.schedule_interval(self.__check_if_sees, FPS / 2)

        self.x -= self.__current_speed * self.parent.get_speed()


class Bonus(MovingObject):
    pass


class MovingBackground(Widget):

    def __init__(self, pos=(0, 0)):
        super(MovingBackground, self).__init__()
        self.size = Window.size

        self.pos = pos
        # self.allow_stretch = True
        # self.size_hint_x = 0.2
        # self.source = 'texture/background_2.png'


class TopBorder(BoxLayout):

    _points = NumericProperty(0)
    _factor = NumericProperty(FACTOR)

    def __init__(self):
        super(TopBorder, self).__init__()
        self.pos = 0, Window.height - Window.height // 17
        self.size = Window.width, Window.height // 17
        self.orientation = 'horizontal'
        self.padding, self.spacing = 2, 0

    def set_points(self, value):
        self._points = value


class Game(Widget):

    __distance_between_islands = NumericProperty(DISTANCE)
    __speed = NumericProperty()
    __points = NumericProperty(0)
    _factor = NumericProperty(FACTOR)
    _center_label_text = StringProperty('Touch to Start')

    @staticmethod
    @fibonacci_decorator
    def __get_fibonacci_number(x, y):
        return x + y

    def __test(self):
        self.add_island()
        self.add_coins()

    def __test_1(self):
        pass

    def __get_fps(self, timing):
        return False
        print Clock.get_rfps()

    def __change_distance(self, *args):
        # print self.__speed
        value = random.randint(30, 50)

        if self.__distance_between_islands - value <= MIN_DISTANCE:
            return False

        self.__distance_between_islands -= value
        self.__islands_to_next_level = self.__get_fibonacci_number()

    def __load_textures(self):
        self.textures = dict()

    # def __take_screenshot(self, timing=None, f_=0):
    #     Window.screenshot(name='%s.png' % f_)
    #     Clock.schedule_once(lambda t: self.__take_screenshot(f_=f_+1), 1)

    def __init_touch(self):
        self.__speed = GAME_SPEED
        self.add_island()
        self.add_coins()
        self.__touch_handler = self.hero.up
        # self.remove_widget(
            # [child for child in self.children if isinstance(child, Label)][0])
        # self._center_label_text = ''

        self.__information_deck = TopBorder()
        self.add_widget(self.__information_deck)

        self.__clear_label()
        # Clock.schedule_once(self.__take_screenshot, 1)

    def __clear_label(self, timing=None):
        self._center_label_text = ''

    def display_jump_label(self, index):
        self._center_label_text = JUMP_LABELS[index] + ' Jump!'
        Clock.schedule_once(self.__clear_label, 3)

    def add_points(self, value=COIN_VALUE):
        self.__points += value
        self.__information_deck.set_points(self.__points)

    def hero_collided(self):
        self.hero.lose_life()

    def remove_object(self, obj):
        self.remove_widget(obj)

    def collect_coin(self, coin):
        self.remove_widget(coin)
        self.add_points()

    def get_distance(self):
        return self.width - self.__distance_between_islands

    @keep_last_point
    def get_coins_coords(self, points):
        '''Generates 4 random points and calls bezier's function with them.'''

        quarter = self.width // 4

        points[0][0] -= 3 * quarter

        areas = [self.width + quarter,
                 self.width + (2 * quarter),
                 self.width + (3 * quarter),
                 2 * self.width]

        index = 0
        while index < len(areas) - 1:
            x = random.randint(areas[index], areas[index + 1])
            y = random.randint(0, self.height)
            points.append([x, y])
            index += 1

        return bezier(points)

    def add_coins(self, timing=None):
        coords = self.get_coins_coords()

        for coord in coords:
            coin = Coin(pos=coord)
            self.add_widget(coin)
        Clock.schedule_interval(coin._check_if_need_to_create_next, FPS)
        # print coin
        return True

    def add_island(self):
        self.number_of_islands += 1

        if self.number_of_islands == self.__islands_to_next_level:
            self.__change_distance()

        self.add_widget(Island())

        # print 'garbage:'
        # for x in gc.garbage:
        #     print x

        # print 'hero_refs:', sys.getrefcount(self.hero)
        # print self.number_of_islands, self.__islands_to_next_level,
        # self.distance_between_islands

    # def get_hero_object(self):
    #     return self.hero

    def on_touch_down(self, touch):
        # if touch.is_double_tap:
            # print self.__speed, SLOW_GAME_SPEED, GAME_SPEED
            # if self.__speed == SLOW_GAME_SPEED:
            #     self.__run_time()
            # else:
            #     self.__slow_time()
            # self.__pause_time()
            # self.__decrease_speed()
        self.hero.up()
        self.__touch_handler()

    def on_touch_up(self, touch):
        # self.hero.set(23, 0, 0, 1)
        self.hero.down()

    def get_speed(self):
        return self.__speed

    def game_over(self):
        self.__speed = 0
        self._center_label_text = 'Game Over'

    def start(self):
        self.size = Window.size

        self.__speed = 0
        self.number_of_islands = 0

        self.__islands_to_next_level = self.__get_fibonacci_number()

        self.__touch_handler = self.__init_touch

        self.hero = Hero()
        self.add_widget(self.hero)

        # args = dict(text='Touch to start',
        #             center=self.center,
        #             font_size=FACTOR,
        # self.add_widget(Label(**args))

        # first_island = Island()
        # first_island.pos = self.hero.x, self.hero.y - first_island.height - 2
        # self.add_widget(first_island)

        # self.add_widget(MovingBackground())

        # self.__Point = collections.namedtuple('Point', ['x', 'y'])
        # self.__test()

        Clock.schedule_interval(self.__get_fps, 1)
        # Clock.schedule_interval(lambda t: self.add_coins(), 1)
        # Clock.schedule_once(self.__change_distance, 5)


class YetApp(App):

    '''Just starts the game and clocks. Adds label'''

    def build(self):
        # Window.fullscreen = True
        game = Game()
        game.start()
        return game


if __name__ == '__main__':
    '''Simple game. Almost identical to The Shortest Story from WinPhone'''
    YetApp().run()
