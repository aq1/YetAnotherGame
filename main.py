import random

from kivy.app import App
from kivy.uix.widget import Widget
from kivy.vector import Vector
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.properties import NumericProperty, ObjectProperty,\
    ReferenceListProperty, BooleanProperty, ListProperty


IMMORTALITY_TIME = 3
GRAVITY = 0.3
MAX_GRAVITY = -1
PLAYER_SPEED = 5
MAX_LIVES = 3
TIME_TO_GO_DOWN = 0.7
BEZIER_ACCURACY = 0.2
GAME_SPEED = 5
FIRST_POINT = [1.75 * Window.width, Window.height//2]


class MainWindow(Widget):

    '''Deals with gravity,   movement, collisions, schedule'''

    player = ObjectProperty(None)
    points = ListProperty([FIRST_POINT])
    childrenSlice = NumericProperty()

    def start_the_game(self):
        self.childrenSlice = len(self.children) - 1
        self.size = Window.size
        self.generate_coins()
        self.generate_obstacles()

    def bezier(self, points, accuracy=BEZIER_ACCURACY):
        assert len(points) == 4, len(points)
        coords = []

        t = accuracy
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
            t += accuracy
        return coords

    def get_objects_coords(self, timing=None):
        '''Generates four random points and calls bezier's function.
            First, four points should be in differnet corners of screen
            areas = [MIN_X, MAX_X, MIN_Y, MAX_Y]'''
        # points = []
        quarter = self.width // 4

        del self.points[:-1]
        self.points[0][0] -= 3*quarter

        areas = [self.width + quarter,
                 self.width + (2 * quarter),
                 self.width + (3 * quarter),
                 2 * self.width]

        index = 0
        while index < len(areas) - 1:
            x = random.randint(areas[index], areas[index+1])
            y = random.randint(0, self.height)
            self.points.append([x, y])
            index += 1

        # for area in areas:
        #     # print area[0], area[1]
        #     # print area[2], area[3]
        #     x = random.randint(area[0], area[1])
        #     y = random.randint(area[2], area[3])
        #     self.points.append([x, y])

        # print self.points, len(self.children)
        return self.bezier(self.points)

        # del self.points[:]

    def generate_coins(self, timing=None):
        coords = self.get_objects_coords()
        for coord in coords:
            coin = Coin()
            coin.pos = coord
            coin.size = self.size[0] // 40, self.size[0] // 40
            self.add_widget(coin)

        Clock.schedule_once(self.generate_coins, GAME_SPEED)

    def generate_obstacles(self, timing=None):
        coords = self.get_objects_coords()
        # print coords
        for coord in coords:
            obstacle = Obstacle()
            obstacle.pos = coord
            obstacle.size = self.size[0] // 10, self.size[0] // 15
            self.add_widget(obstacle)

        Clock.schedule_once(self.generate_obstacles, GAME_SPEED)

    def update(self, timing=None):
        # print self.children[:self.childrenSlice]
        for child in self.children[:self.childrenSlice]:
            try:
                child.move()
                # print child.pos, child.size
            except AttributeError:
                # print 'Warning! Children is not moveable'
                pass

            # print '\n\n\n', type(child), type(self.player), '\n\n\n\n'
            if child.x < self.player.right:
                try:
                    child.collide(self.player)
                    # print 'checking collision', child
                    # print self.player.lives, self.player.coins
                    # print self.player.right, self.player.pos, self.player.size
                except AttributeError:
                    # print 'Something Wrong', child
                    pass

    def on_touch_down(self, touch):
        self.player.up()

    def on_touch_up(self, touch):
        self.player.down()

    def game_over(self):
        print 'game over'
        Clock.unschedule(self.update)
        Clock.unschedule(self.generate_coins)
        Clock.unschedule(self.generate_obstacles)


class Player(Widget):

    '''Just player's square. Moves, dies, jumps, collects coins'''

    velX = NumericProperty(0)
    velY = NumericProperty(0)
    velocity = ReferenceListProperty(velX, velY)
    immortal = BooleanProperty(False)
    lives = NumericProperty(MAX_LIVES)
    coins = NumericProperty(0)

    def become_immortal(self):
        self.immortal = True
        Clock.schedule_once(self.become_mortal, IMMORTALITY_TIME)

    def become_mortal(self, timing):
        self.immortal = False

    def collision_with_bottom(self, timing=None):
        self.velY = PLAYER_SPEED * 1.8
        Clock.schedule_once(self.down, TIME_TO_GO_DOWN)

    def move(self):
        if self.y < -self.height:
            self.collision_with_bottom()

        self.pos = Vector(*self.velocity) + self.pos

    def up(self):
        Clock.unschedule(self.down)
        self.velY = PLAYER_SPEED

    def down(self, timing=None):
        self.velY = -PLAYER_SPEED

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


class Obstacle(FlyingObjects):

    '''Kills the player'''

    def collide(self, player):
        if self.collide_widget(player):
            player.take_a_life()


class Coin(FlyingObjects):

    '''Checks if collides with player.
        Should be gently generated on the playground'''

    def collide(self, player):
        if self.collide_widget(player):
            print 'coin collide'
            # print self.pos, self.size, player.pos, player.size
            player.add_coin()
            self.parent.remove_widget(self)


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
