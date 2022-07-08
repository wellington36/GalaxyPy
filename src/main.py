import random
from kivy.config import Config

Config.set('graphics', 'width', '900')
Config.set('graphics', 'height', '400')

from kivy.app import App
from kivy import platform
from kivy.lang import Builder
from kivy.uix.widget import Widget
from kivy.core.window import Window
from kivy.core.audio import SoundLoader
from kivy.uix.relativelayout import RelativeLayout
from kivy.properties import Clock, NumericProperty
from kivy.graphics.context_instructions import Color
from kivy.properties import ObjectProperty, StringProperty
from kivy.graphics.vertex_instructions import Line, Quad, Triangle, Rectangle

Builder.load_file("menu.kv")


class MainWidget(RelativeLayout):
	from transforms import tranform_perspective, transform, transform_2D
	from user_actions import (keyboard_closed, on_keyboard_down, on_keyboard_up,
	                          on_touch_down, on_touch_up)

	menu_widget = ObjectProperty()

	perspective_point_x = NumericProperty(0)
	perspective_point_y = NumericProperty(0)
	current_offset_y = NumericProperty(0)
	current_offset_x = NumericProperty(0)
	current_speed_x = NumericProperty(0)
	
	V_NB_LINES = 8		# number of lines
	V_LINES_SPACING = 0.25		# percentage in screen width
	vertical_lines = []

	H_NB_LINES = 16		# number of lines
	H_LINES_SPACING = 0.1		# percentage in screen height
	horizontal_lines = []
	current_y_loop = 0

	SPEED = 0.5          # 0.5 and 1.5
	SPEED_X = 1.5

	NB_TILES = 40
	tiles = []
	tiles_coordinates = []

	SHIP_BASE_Y = 0.04
	ship = None
	ship_coordinates = [(0, 0), (0, 0), (0, 0)]

	state_game_over = False
	state_game_has_started = False

	menu_title = StringProperty("G  A  L  A  X  Y")
	menu_button_title = StringProperty("START")
	score_text = StringProperty("SCORE: 0")
	level = StringProperty("LEVEL: 1")

	sound_begin = None
	sound_galaxy = None
	sound_gameover_impact = None
	sound_gameover_voice = None
	sound_music1 = None
	sound_restart = None

	
	def __init__(self, **kwargs):
		super(MainWidget, self).__init__(**kwargs)
		self.init_vertical_lines()
		self.init_horizontal_lines()
		
		self.init_audio()
		self.init_tiles()
		self.init_ship()
		self.pre_fill_tiles_coordinates()
		self.generate_tile_coordinates()

		if self.is_desktop():
			self._keyboard = Window.request_keyboard(self.keyboard_closed, self)
			self._keyboard.bind(on_key_down=self.on_keyboard_down)
			self._keyboard.bind(on_key_up=self.on_keyboard_up)

		Clock.schedule_interval(self.update, 1.0 / 60.0)	# 60 fps
		self.sound_galaxy.play()
	

	def init_audio(self):
		self.sound_begin = SoundLoader.load("audio/begin.wav")
		self.sound_galaxy = SoundLoader.load("audio/galaxy.wav")
		self.sound_gameover_impact = SoundLoader.load("audio/gameover_impact.wav")
		self.sound_gameover_voice = SoundLoader.load("audio/gameover_voice.wav")
		self.sound_music1 = SoundLoader.load("audio/music1.wav")
		self.sound_restart = SoundLoader.load("audio/restart.wav")

		self.sound_music1.volume = 1
		self.sound_galaxy.volume = 0.25
		self.sound_gameover_impact.volume = 0.6
		self.sound_begin.volume = 0.25
		self.sound_restart.volume = 0.25
		self.sound_gameover_voice.volume = 0.25


	def reset_game(self):
		self.current_offset_x = 0
		self.current_offset_y = 0
		self.current_y_loop = 0
		self.current_speed_x = 0
		self.level = "LEVEL: 1"
		self.score_text = "SCORE: 0"
		self.SPEED = 0.5
		self.SPEED_X = 1.5

		self.tiles_coordinates = []
		self.pre_fill_tiles_coordinates()
		self.generate_tile_coordinates()

		self.state_game_over = False


	def is_desktop(self):
		if platform in ('linux', 'win', 'macosc'):
			return True
		else:
			return False
	

	def init_ship(self):
		with self.canvas:
			#Color(0, 0, 0)
			#self.ship = Triangle()

			self.ship = Rectangle(pos=(self.width/2, 10), size=(75, 75), source='images/ship2.png')
			print(self.width)
	

	def update_ship(self):
		#center_x = self.width / 2
		#base_y = self.SHIP_BASE_Y * self.height
		#ship_half_width = self.SHIP_WIDTH * self.width / 2
		#ship_height = self.SHIP_HEIGHT * self.height

		#self.ship_coordinates[0] = (center_x - ship_half_width, base_y)
		#self.ship_coordinates[1] = (center_x, base_y + ship_height)
		#self.ship_coordinates[2] = (center_x + ship_half_width, base_y)

		#x1, y1 = self.transform(*self.ship_coordinates[0])
		#x2, y2 = self.transform(*self.ship_coordinates[1])
		#x3, y3 = self.transform(*self.ship_coordinates[2])

		#self.ship.points = [x1, y1, x2, y2, x3, y3]
		self.ship.pos = (self.width/2 - self.ship.size[0]/2, 10)


	def check_ship_collision(self):
		for i in range(0, len(self.tiles_coordinates)):
			ti_x, ti_y = self.tiles_coordinates[i]
			
			if ti_y > self.current_y_loop + 1:
				return False
			
			if self.check_ship_collision_with_tile(ti_x, ti_y):
				return True

		return False


	def check_ship_collision_with_tile(self, ti_x, ti_y):
		xmin, ymin = self.get_tile_coordinates(ti_x, ti_y)
		xmax, ymax = self.get_tile_coordinates(ti_x + 1, ti_y + 1)

		g_point_ship_x = self.width/2
		g_point_ship_y = 10

		return (xmin <= g_point_ship_x <= xmax and ymin <= g_point_ship_y <= ymax)


	def init_tiles(self):
		with self.canvas:
			Color(1, 1, 1)
			
			for i in range(0, self.NB_TILES):
				self.tiles.append(Quad())


	def pre_fill_tiles_coordinates(self):
		for i in range(0, 10):
			self.tiles_coordinates.append((0, i))		


	def generate_tile_coordinates(self):
		last_x = 0
		last_y = 0

		for i in range(len(self.tiles_coordinates) - 1, -1, -1):
			if self.tiles_coordinates[i][1] < self.current_y_loop:
				del self.tiles_coordinates[i]
		
		if len(self.tiles_coordinates) > 0:
			last_coordinates = self.tiles_coordinates[-2]
			last_y = last_coordinates[1] + 1
			last_x = last_coordinates[0]

		for i in range(len(self.tiles_coordinates), self.NB_TILES):
			start_index = -int(self.V_NB_LINES / 2) + 1
			end_index = start_index + self.V_NB_LINES - 2
			r1 = random.randint(0, 2)
			r2 = random.randint(start_index, end_index)

			if last_x <= start_index:
				r1 = 1
			if last_x >= end_index:
				r1 = 2

			self.tiles_coordinates.append((last_x, last_y))
			#self.tiles_coordinates.append((r2, last_y))
			if (r1 == 1):
				last_x += 1
				self.tiles_coordinates.append((last_x, last_y))
				last_y += 1
				self.tiles_coordinates.append((last_x, last_y))
			if (r1 == 2):
				last_x -= 1
				self.tiles_coordinates.append((last_x, last_y))
				last_y += 1
				self.tiles_coordinates.append((last_x, last_y))
			
			
			last_y += 1


	def init_vertical_lines(self):
		with self.canvas:
			Color(1, 1, 1)

			for i in range(0, self.V_NB_LINES):
				self.vertical_lines.append(Line())


	def init_horizontal_lines(self):
		with self.canvas:
			Color(1, 1, 1)
			# self.line = Line(points=[self.width/2, 0, self.width/2, 100])
			for i in range(0, self.H_NB_LINES):
				self.horizontal_lines.append(Line())


	def get_line_x_from_index(self, index):
		central_line_x = self.perspective_point_x
		spacing = self.V_LINES_SPACING * self.width
		offset = index - 0.5
		line_x = central_line_x + offset * spacing + self.current_offset_x

		return line_x
	

	def get_line_y_from_index(self, index):
		spacing_y = self.H_LINES_SPACING * self.height
		line_y = index * spacing_y - self.current_offset_y
		
		return line_y

	
	def get_tile_coordinates(self, ti_x, ti_y):
		ti_y = ti_y - self.current_y_loop

		x = self.get_line_x_from_index(ti_x)
		y = self.get_line_y_from_index(ti_y)

		return x, y
	

	def update_tiles(self):
		for i in range(0, self.NB_TILES):
			tile = self.tiles[i]
			tile_coordinates = self.tiles_coordinates[i]

			xmin, ymin = self.get_tile_coordinates(tile_coordinates[0], tile_coordinates[1])
			xmax, ymax = self.get_tile_coordinates(tile_coordinates[0] + 1, tile_coordinates[1] + 1)

			x1, y1 = self.transform(xmin, ymin)
			x2, y2 = self.transform(xmin, ymax)
			x3, y3 = self.transform(xmax, ymax)
			x4, y4 = self.transform(xmax, ymin)

			tile.points = [x1, y1, x2, y2, x3, y3, x4, y4]

		
	def update_vertical_lines(self):
		start_index = -int(self.V_NB_LINES / 2) + 1

		for i in range(start_index, self.V_NB_LINES + start_index):
			line_x = self.get_line_x_from_index(i)
			
			x1, y1 = self.transform(line_x, 0)
			x2, y2 = self.transform(line_x, self.height)
			
			self.vertical_lines[i].points = [x1, y1, x2, y2]


	def update_horizontal_lines(self):
		start_index = -int(self.V_NB_LINES / 2) + 1
		end_index = start_index + self.V_NB_LINES - 1

		xmin = self.get_line_x_from_index(start_index)
		xmax = self.get_line_x_from_index(end_index)
		
		for i in range(0, self.V_NB_LINES):
			line_y = self.get_line_y_from_index(i)
			
			x1, y1 = self.transform(xmin, line_y)
			x2, y2 = self.transform(xmax, line_y)
			
			self.horizontal_lines[i].points = [x1, y1, x2, y2]


	def update(self, dt):
		time_factor = dt*60.0

		self.perspective_point_x = self.width/2
		self.perspective_point_y = self.height * 0.75

		self.update_vertical_lines()
		self.update_horizontal_lines()
		self.update_tiles()
		self.update_ship()

		if not self.state_game_over and self.state_game_has_started:
			speed_y = self.SPEED * self.height / 100
			self.current_offset_y += speed_y * time_factor

			spacing_y = self.H_LINES_SPACING * self.height
			while self.current_offset_y >= spacing_y:
				self.current_offset_y -= spacing_y
				self.current_y_loop += 1
				self.score_text = "SCORE: " + str(self.current_y_loop)
			
				if (self.current_y_loop / 50.0).is_integer():
					self.SPEED += 0.1
					self.SPEED_X += 0.2
					self.level = "LEVEL: " + str(int(self.current_y_loop / 50 + 1))

				self.generate_tile_coordinates()
				print("loop: " + str(self.current_y_loop))
		
			speed_x = self.current_speed_x * self.width / 100
			self.current_offset_x += speed_x * time_factor

		if not self.check_ship_collision() and not self.state_game_over:
			self.state_game_over = True
			self.menu_title = "G  A  M  E    O  V  E  R"
			self.menu_button_title = "RESTART"
			self.menu_widget.opacity = 1
			self.sound_music1.stop()
			self.sound_gameover_impact.play()
			Clock.schedule_once(self.play_game_over_voice, 2)
			print("GAME OVER")


	def play_game_over_voice(self, dt):
		if self.state_game_over:
			self.sound_gameover_voice.play()
	

	def on_menu_button_pressed(self):
		print("BUTTON")

		if self.state_game_over:
			self.sound_restart.play()
		else:
			self.sound_begin.play()

		self.sound_music1.play()
		self.reset_game()
		self.state_game_has_started = True
		self.menu_widget.opacity = 0


class GalaxyApp(App):
	pass
	

GalaxyApp().run()

