import random

from kivy.app import App
from kivy.uix.widget import Widget
from kivy.vector import Vector
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.graphics import Line
from kivy.properties import NumericProperty, ObjectProperty,\
    ReferenceListProperty, BooleanProperty, ListProperty


IMMORTALITY_TIME = 3
GRAVITY = 0.3
MAX_GRAVITY = -1
PLAYER_SPEED = Window.width // 120
MAX_LIVES = 3
TIME_TO_GO_DOWN = 0.7
BEZIER_PRECISION = 0.2
GAME_SPEED = Window.width // 150
FIRST_POINT = [1.75 * Window.width, Window.height // 2]


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


class MainWindow(Widget):

    '''Deals with gravity, movement, collisions, schedule'''

    player = ObjectProperty(None)
    points = ListProperty([FIRST_POINT])
    childrenSlice = 0

    def start_the_game(self):
        self.childrenSlice = len(self.children) - 1
        self.size = Window.size
        self.generate_coins()
        self.generate_obstacles()
        with self.canvas:
            Line(points=[self.player.right, 0, self.player.right, self.height])

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

    def generate_coins(self, timing=None):
        coords = self.get_coins_coords()
        for coord in coords:
            coin = Coin()
            coin.pos = coord
            coin.size = self.size[0] // 40, self.size[0] // 40
            self.add_widget(coin)

        # print 'generated coins'
        Clock.schedule_once(self.generate_coins, 3)

    def generate_obstacles(self, timing=None):
        '''Generates 4 obstacles on the edge of the screen
            But each obstacle has a 1/3 chance to not be generated'''

        coords = [[random.randint(self.width, self.width + 200),
                   random.randint(20, self.height)]
                  for _ in range(4) if random.randint(0, 10) < 3]

        for coord in coords:
            obstacle = Obstacle()
            obstacle.pos = coord
            obstacle.factor = self.size[1]//3
            self.add_widget(obstacle)

        # print 'generated obstacles'
        Clock.schedule_once(self.generate_obstacles, 1)

    def update(self, timing=None):
        # print self.size
        # print self.children[:self.childrenSlice]
        for child in self.children[:-3]:
            try:
                child.move()
                # print child.pos, child.size
            except AttributeError:
                # print 'Warning! Children is not moveable'
                pass

            # print '\n\n\n', type(child), type(self.player), '\n\n\n\n'
            if child.x < self.player.right:
                try:
                    pass
                    child.collide(self.player)
                    # print 'checking collision', child
                    # print self.player.lives, self.player.coins
                except AttributeError:
                    # print 'Something Wrong', child
                    pass

    def on_touch_down(self, touch):
        self.player.go_up()

    def on_touch_up(self, touch):
        self.player.go_down()

    def unschedule_all(self):
        Clock.unschedule(self.update)
        Clock.unschedule(self.generate_coins)
        Clock.unschedule(self.generate_obstacles)

    def game_over(self):
        print 'game over'
        self.unschedule_all()


class Player(Widget):

    '''Just player's square. Moves, dies, jumps, collects coins'''

    velX = NumericProperty(0)
    velY = NumericProperty(0)
    velocity = ReferenceListProperty(velX, velY)
    immortal = BooleanProperty(False)
    lives = NumericProperty(MAX_LIVES)
    coins = NumericProperty(0)
    offset = NumericProperty(0)
    maxSpeed = NumericProperty(4)

    def become_immortal(self):
        self.immortal = True
        # Clock.schedule_once(self.become_mortal, IMMORTALITY_TIME)

    def become_mortal(self, timing):
        self.immortal = False

    def collision_with_bottom(self, timing=None):
        Clock.unschedule(self.go_down)
        print 'bottom'
        self.take_a_life()
        self.velY = self.maxSpeed*2
        Clock.schedule_once(self.go_down, 0.2)

    def move(self):
        if self.y < -self.height:
            self.collision_with_bottom()

        self.pos = Vector(*self.velocity) + self.pos

    def go_up(self, timing=None):
        print self.velY
        Clock.unschedule(self.go_down)
        if self.velY > self.maxSpeed:
            return

        self.velY += 2
        Clock.schedule_once(self.go_up, 0.1)

    def go_down(self, timing=None):
        Clock.unschedule(self.go_up)
        # print self.velY, self.maxSpeed
        # if self.velY < -self.maxSpeed:
        #     return

        self.velY -= 1
        Clock.schedule_once(self.go_down, 0.1)

    def take_a_life(self):
        if not self.immortal:
            # print 'took a life'
            self.lives -= 1

            if self.lives == 0:
                self.parent.game_over()
            self.become_immortal()

    def give_a_life(self):
        if self.lives == MAX_LIVES:
            return
        else:
            self.lives += 1

    def add_coin(self):
        self.coins += 1
        if self.coins % 10 == 0:
            self.give_a_life()


class FlyingObjects(Widget):

    ''' 'Abstract' class '''

    velY = NumericProperty(0)
    velX = NumericProperty(-GAME_SPEED)
    velocity = ReferenceListProperty(velX, velY)

    def move(self):
        self.pos = Vector(*self.velocity) + self.pos
        if self.right < 0:
            self.parent.remove_widget(self)

    def collide(self, player):
        assert self.x <= player.right # remove in release
        # print 'checking'
        # print self.x, self.right, self.y, self.top
        if self.y > player.top or self.top < player.y:
            return False
        else:
            self.parent.remove_widget(self)
            # print 'collide', self
            return True


class Obstacle(FlyingObjects):

    '''Kills the player'''
    factor = NumericProperty()

    def collide(self, player):
        pass
        # if self.collide_widget(player):
        #     self.parent.remove_widget(self)
        #     player.take_a_life()


class Coin(FlyingObjects):

    '''Checks if collides with player.
        Should be gently generated on the playground'''

    # def collide(self, player):
    #     if self.collide_widget(player):
    #         # print 'coin collide'
    #         # print self.pos, self.size, player.pos, player.size
    #         player.add_coin()
    #         self.parent.remove_widget(self)


class YetApp(App):

    '''Just starts the game and clocks. Adds label'''

    def build(self):
        mainWindow = MainWindow()
        mainWindow.start_the_game()
        Clock.schedule_interval(mainWindow.update, 1.0 / 60.0)
        return mainWindow


if __name__ == '__main__':
    '''Simple game. Almost identical to The Shortest Story from WinPhone'''
    YetApp().run()
