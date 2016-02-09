#!/usr/bin/env python3
import sys
from threading import Thread
from binascii import hexlify
from pprint import pprint as printp
from time import sleep
from pymouse import PyMouse
from pykeyboard import PyKeyboard

dbtn = {
		'a_dx': b'\x02\x04',
		'a_dy': b'\x02\x05',
		'a_lx': b'\x02\x00',
		'a_ly': b'\x02\x01',
		'a_rx': b'\x02\x02',
		'a_ry': b'\x02\x03',
		'b_circle': b'\x01\x01',
		'b_down': b'\x01\x0e',
		'b_ex': b'\x01\x02',
		'b_lb': b'\x01\x04',
		'b_left': b'\x01\x0f',
		'b_ls': b'\x01\n',
		'b_lt': b'\x01\x06',
		'b_rb': b'\x01\x05',
		'b_right': b'\x01\r',
		'b_select': b'\x01\x08',
		'b_square': b'\x01\x03',
		'b_rs': b'\x01\x0b',
		'b_rt': b'\x01\x07',
		'b_start': b'\x01\t',
		'b_triangle': b'\x01\x00',
		'b_up': b'\x01\x0c',

		'unknown': 'unknown',
	}

dbtn_r = {value: key for (key, value) in dbtn.items()}

class Controller():

	def __init__(self,speed=8):
		self.m = PyMouse()
		self.k = PyKeyboard()
		self.speed = speed*8

		self.xy = {
				'x': 0,
				'y': 0,
				'd_x': 0,
				'd_y': 0,
			}

	def run(self):
		pipe = open('/dev/input/js0','rb')

		try:
			self._move_mouse_thread = Thread(target=self._move_mouse)
			self._move_mouse_thread.start()

			while 1:
				nb = pipe.read(8)
				self._handle(gen_inf(nb))
		except RuntimeError as e:
			raise e

	def _handle(self,inf):
		try:
			if inf['btn'] == 'a_lx':
				self.xy['d_x'] = int(inf['lvl']/self.speed)
			if inf['btn'] == 'a_ly':	
				self.xy['d_y'] = int(inf['lvl']/self.speed)
			if inf['btn'] == 'a_rx':
				self.xy['d_x'] = int(inf['lvl']/(self.speed*4))
			if inf['btn'] == 'a_ry':	
				self.xy['d_y'] = int(inf['lvl']/(self.speed*4))

			if inf['btn'] == 'b_lb' and inf['lvl'] == 1:
				self.m.press(
						x=self.xy['x'],
						y=self.xy['y'],
						button=1,
				)
			elif inf['btn'] == 'b_lb' and inf['lvl'] == 0:
				self.m.release(
						x=self.xy['x'],
						y=self.xy['y'],
						button=1,
				)

			if inf['btn'] == 'b_rb' and inf['lvl'] == 1:
				self.m.press(
						x=self.xy['x'],
						y=self.xy['y'],
						button=2,
				)
			elif inf['btn'] == 'b_rb' and inf['lvl'] == 0:
				self.m.release(
						x=self.xy['x'],
						y=self.xy['y'],
						button=2,
				)
		except RuntimeError as e:
			raise e


	def _move_mouse(self):
		try:
			while 1:
				self.xy['x'] += self.xy['d_x']
				self.xy['y'] += self.xy['d_y']
				self.m.move(
						x=self.xy['x']+self.xy['d_x'],
						y=self.xy['y']+self.xy['d_y'],
				)
				sleep(1/120)
		except RuntimeError as e:
			raise e

	def __del__(self):
		print('Stopping driver...')

def gen_inf(nb):
	try:
		nbtn = dbtn_r[nb[6:]]
	except:
		nbtn = dbtn_r['unknown']
	return {
		'btn': nbtn,
		'lvl': int.from_bytes(nb[4:6],'little',signed=True),
		#'lvl': int.from_bytes(nb[4:6],'big'),
	}
	

def debug(state='read'):
	pipe = open('/dev/input/js0','rb')
	action = []
	while 1:
		nb = pipe.read(8)
		inf = gen_inf(nb)
		if state == 'read':
			action += [inf]
			printp(inf)
		elif state == 'save':
			if nb[6:] not in dbtn.values():
				print(inf)
				print('Enter name:',end=' ')
				try:
					dbtn[input()] = nb[6:]
				except KeyboardInterrupt:
					print('Skipping...')
				printp(dbtn)
		else:
			raise NameError('incorrect debug type specified')

if len(sys.argv) < 2:
	print('Please specify mode of operation. Current options: run, debug')
	exit()

if sys.argv[1] == 'debug':
	try:
		debug_mode = sys.argv[2]
	except IndexError:
		debug_mode = 'read'
	debug(debug_mode)

if sys.argv[1] == 'run':
	try:
		speed = int(sys.argv[2])
	except (IndexError, ValueError):
		speed = 8	
	while 1:
		try:
			c = Controller(speed)
			print('Starting driver...')
			c.run()
		except RuntimeError as e:
			print(e)
			print('Attempting restart...')
			del c
		except Exception as e:
			print(e)
			print('This isn\'t good. Attempting to exit...')
			break
