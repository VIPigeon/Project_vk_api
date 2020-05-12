
import traceback
import random
import vk_api
import sys
import asyncio
import time
from collections import defaultdict
from datetime import datetime
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEvent, VkBotMessageEvent, VkBotEventType


# def say_after0(delay, what):
#     time.sleep(delay)
#     print(what)


# async def say_after(delay, what):
#     await asyncio.sleep(delay)
#     print(what)

def get_name(id0):
	return vk.users.get(user_ids=[id0])[0]['first_name'] + \
	' ' + vk.users.get(user_ids=[id0])[0]['last_name']			

class Master():

	__slots__ = (
		'keyword',  # тайное слово ведущего
		'lead_id',  # id ведущего
		'room_id',  # peer_id комнаты (беседы) мастера
		'users',  # set id игроков
		'contact_now',  # boolean
		'progress',  # int, прогресс в угадывании слова
		'lead_words',  # слова ведущего во время контакта
		'contact_words',  # слова остальных участников контакта
		'end',  # отгадано ли секретное слово
		'first_game'  # является ли текущая игра первой
	)

	def __init__(self, room_id):
		self.room_id = room_id
		self.first_game = True
		self.users = set()
		self.contact_now = False
		self.keyword = None
		self.lead_id = None
		self.progress = 1
		self.lead_words = set()
		self.contact_words = {}
		self.end = False

	def sms(self, s):
		vk.messages.send(  # Отправляем собщение
			# user_id=event.raw['object']['from_id'],
			# chat_id=event.raw['object']['id'],
			group_id=GROUP_ID,
			peer_id=self.room_id,
			random_id=random.randint(1, 10 ** 7),
			# sticker_id=12710,
			message=s
		)		

	def start(self):
		# Приветствие
		if self.first_game:
			self.sms(
				"""Привет!
				Назначьте бота администратором, а потом отправьте сообщение, чтобы продолжить
				Чтобы узнать команды бота, напишите "Помощь"
				"""
				)
		else:
			self.sms('Кто ведущий?')

	async def processing(self, ev):
		# обработка нового сообщения
		if not self.users:
			self.set_users()
		elif ev.raw['object']['text'] == 'Контакт':
			loop = asyncio.get_running_loop()
			loop.run_in_executor(None, self.make_contact)
		elif ev.raw['object']['text'] == 'Помощь':
			self.help()
		elif ev.raw['object']['text'] == 'Я ведущий':
			self.set_lead(ev.raw['object']['from_id'])
		else:
			print('was')

	def set_users(self):
		try:
			inf = vk.messages.getConversationMembers(
				peer_id=self.room_id,
				group_id=GROUP_ID
			)
		except Exception as e:
			print('===', e)
			self.sms('Сделайте бота администратором')
			return
		print('====================================================')
		print(inf)
		# print(inf['profiles'])
		for profile in inf['profiles']:
			self.users.add(profile['id'])
			user_to_room[profile['id']] = self.room_id
		self.sms('Кто ведущий?')

	def new_player(self, ev):
		if 'action' in ev.raw['object'] \
		and ev.raw['object']['action']['type'] == 'chat_invite_user':
			us_id = ev.raw['object']['action']['member_id']
			self.users.add(us_id)
			user_to_room[us_id] = self.room_id
			return True
		return False

	def set_lead(self, id0):
		if self.lead_id is None:
			self.lead_id = id0
			self.sms(f'{get_name(id0)} ведущий')
			self.sms('Ведущий должен написать в личные сообщения боту своё секретное слово')

	def exit_player(self, ev):
		if 'action' in ev.raw['object'] \
		and ev.raw['object']['action']['type'] == 'chat_kick_user':
			us_id = ev.raw['object']['action']['member_id']
			self.users.discard(us_id)
			user_to_room.pop(us_id)
			return True
		return False

	def make_contact(self):
		print('*')
		if self.lead_id is None:
			self.sms('Не объявлен ведущий')
			return
		if self.keyword is None:
			self.sms('Ведущий не объявил ключевое слово')
			return

		self.sms("""Контакт!
			Идёт отсчёт: 20 секунд"""
		)

		try:

			self.contact_now = True

			wait0()

			self.contact_now = False
			result = self.check()

			self.sms(result)
			if result == 'Контакт прошел успешно':
				if self.progress == len(self.keyword):
					self.sms('Секретное слово отгадано')
					self.end = True
				else:
					self.sms(f'Следующая буква -- {self.keyword[self.progress]}')
					self.progress += 1

			s = 'Названные слова:\n'
			for key, value in self.contact_words.items():
				if value == self.keyword:
					self.sms(get_name(key) + ' отгадал(а) секретное слово')
					self.end = True
				s += get_name(key) + ': ' + value + '\n'

			self.sms(s)
			self.lead_words = set()
			self.contact_words = {}
			self.final()
			
		except Exception as e:
			exc_type, exc_value, exc_traceback = sys.exc_info()
			print("*** print_tb:")
			traceback.print_tb(exc_traceback, file=sys.stdout)
			print('!!!', e)

	def check(self):
		# Проверка на удачность контакта
		"""
		check_dict = defaultdict(set) # word: {id1, id2...}
		for id0, word in self.contact_words.items():
			check_dict[word].add(id0)
		check_set = set(check_dict.keys()) - self.lead_words
		checklist1 = filter(lambda x: len(check_dict[x]) > 1, list(check_set))
		checklist2 = filter(lambda x: len(check_dict[x]) > 1, list(self.lead_words))
		if checklist1:
			return 'Контакт прошел успешно'
		if not checklist2:
			return 'Игроки не сконтактировали'
		if checklist2:
			return 'Ассоциация сбита'
		"""
		check_set = set()
		for id0, word in self.contact_words.items():
			if word not in self.lead_words and len(word) >= self.progress \
			and word[:self.progress] == self.keyword[:self.progress]:
				if word in check_set:
					return 'Контакт прошел успешно'
				check_set.add(word)
		return 'Контакт не состоялся'

	def help(self):
		self.sms(
			"""
			"Я ведущий" -- назначает написавшего игрока ведущим, если он ещё не определен
			"Контакт" -- начинает контакт
			"Помощь" -- присылает список команд
			Правила игры опубликованы на странице сообщества
			"""
		)

	def processing_ls(self, ev):
		# обработка лс
		if self.keyword is None and self.lead_id is not None:
			self.keyword = ev.raw['object']['text'].strip()
			if ' ' not in self.keyword:
				self.sms(f'{self.keyword[0]} -- первая буква секретного слова')
			else:
				self.sms('Ведущий должен назвать одно слово')
				self.keyword = None
		if self.contact_now:
			if ev.raw['object']['from_id'] == self.lead_id:
				self.lead_words.add(ev.raw['object']['text'])
			else:
				self.contact_words[ev.raw['object']['from_id']] = ev.raw['object']['text']

	def final(self):
		if self.end:
			self.sms('Слово отгадано, начать новую игру (Да/Нет)')
			self.new_game()

	def new_game(self):
		self.keyword = None
		self.lead_id = None
		self.progress = 1
		self.lead_words = set()
		self.contact_words = {}
		self.end = False
		self.sms('Кто ведущий?')


def new_room(ev):
	# если новая беседа, то создаётся мастер
	if 'action' in ev.raw['object'] \
	and ev.raw['object']['action']['type'] == 'chat_invite_user' \
	and ev.raw['object']['action']['member_id'] == -GROUP_ID:
		masters[ev.raw['object']['peer_id']] = Master(ev.raw['object']['peer_id'])
		return True
	return False


def wait0(delay=20):
	print('Start waiting!')
	print(datetime.now().isoformat())
	time.sleep(delay)
	print('Awake!')
	print(datetime.now().isoformat())


async def main():
	print('work')
	b_longpoll = VkBotLongPoll(vk=vk_session, group_id=GROUP_ID)

	for event in b_longpoll.listen():
		print(event.raw)
		if event.type == VkBotEventType.MESSAGE_NEW:  # and event.to_me and event.text:
			if event.from_chat:
				print('from_chat')

				pr_id = event.raw['object']['peer_id']
				if new_room(event):
					masters[pr_id].start()
				elif masters[pr_id].new_player(event):
					print('==== new_player ====')
					print(masters[pr_id].users, '\n')
					print(user_to_room)
					print('=============================================')
				elif masters[pr_id].exit_player(event):
					print('==== exit_player ====')
					print(masters[pr_id].users, '\n')
					print(user_to_room)
					print('=============================================')
				else:
					await masters[pr_id].processing(event)

			if event.from_user:
				print('from_user')
				masters[user_to_room[event.raw['object']['from_id']]].processing_ls(event)


if __name__ == '__main__':
	token = 'b677113e34fc7a2aba2f407a091e4ff9e3a38d4c2e40f6945db05759646f9631f2c87ad072e250b462900'
	vk_session = vk_api.VkApi(token=token)
	vk = vk_session.get_api()
	GROUP_ID = 194517385

	masters = {}  # {peer_id: Master(peer_id)}
	user_to_room = {}  # {user_id: room_id}
	asyncio.run(main())
