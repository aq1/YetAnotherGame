import random

from kivy.app import App
from kivy.uix.widget import Widget
from kivy.uix.image import Image
from kivy.clock import Clock
from kivy.uix.label import Label
from kivy.properties import NumericProperty, ObjectProperty,\
    ReferenceListProperty, BooleanProperty, StringProperty


JET_PACK_POWER = 0.5
GRAVITY = 0.3
MAX_GRAVITY = 1


class MainWindow(Widget):
    player = ObjectProperty(None)
    status = StringProperty()

    def update(self, y):
        print 'hey'
        # self.player.source = 'spaceman-new.png'

    def on_touch_down(self, touch):
        print touch.shape
        self.status = 'Single Touch'
        if touch.is_double_tap:
            self.status = 'Double Touch'

    def on_touch_up(self, touch):
        self.status = 'No Touch'


class Player(Widget):
    source = StringProperty('monster_5_2_1.png')


class DraftApp(App):

    def build(self):
        m = MainWindow()
        # s = Image(source='im.zip', anim_delay=0.2, mipmap=True)
        # s.size = 300, 300
        # m.add_widget(s)
        Clock.schedule_interval(m.update, 2)
        return m


if __name__ == '__main__':
    DraftApp().run()
