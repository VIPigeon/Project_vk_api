
import random
import vk_api
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
	return vk.users.get(id0)[0]['first_name'] + ' ' + vk.users.get(id0)[0]['last_name']

class Master():

	__slots__ = (
		'keyword',  # тайное слово ведущего
		'lead_id',  # id ведущего
		'room_id',  # peer_id комнаты (беседы) мастера
		'users',  # set id игроков
		'contact_now',  # boolean
		'progress',  # int, прогресс в угадывании слова
		'lead_words',  # слова ведущего во время контакта
		'contact_words'  # слова остальных участников контакта
	)

	def __init__(self, room_id):
		self.room_id = room_id
		self.keyword = None
		self.users = set()
		self.contact_now = False
		self.lead_id = None
		self.progress = 0
		self.lead_words = set()
		self.contact_words = {}

	def start(self):
		# Задаются игроки, ведущий и его тайное слово
		vk.messages.send(  # Отправляем собщение
					# user_id=event.raw['object']['from_id'],
					# chat_id=event.raw['object']['id'],
					group_id=GROUP_ID,
					peer_id=self.room_id,
					random_id=random.randint(1, 10 ** 7),
					# sticker_id=12710,
					message="""Привет!
					 Назначьте бота администратором, а потом отправьте сообщение, чтобы продолжить
					 """
				)

	async def processing(self, ev):
		# обработка нового сообщения
		if not self.users:
			self.set_users()
		elif ev.raw['object']['text'] == 'Контакт':
			loop = asyncio.get_running_loop()
			loop.run_in_executor(None, self.make_contact)
		elif ev.raw['object']['text'] == 'Помощь':
			self.help()
		else:
			print('was')
		if ev.raw['object']['text'] == 'Я ведущий':
			self.set_lead(ev.raw['object']['from_id'])

	def set_users(self):
		inf = vk.messages.getConversationMembers(
			peer_id=self.room_id,
			group_id=GROUP_ID
		)
		print('====================================================')
		print(inf)
		# print(inf['profiles'])
		for profile in inf['profiles']:
			self.users.add(profile['id'])
			user_to_room[profile['id']] = self.room_id
		vk.messages.send(
			group_id=GROUP_ID,
			peer_id=self.room_id,
			random_id=random.randint(1, 10 ** 7),
			# sticker_id=12710,
			message='Кто ведущий?'
		)

	def new_player(self, ev):
		if 'action' in ev.raw['object'] \
		and ev.raw['object']['action']['type'] == 'chat_invite_user':
			us_id = ev.raw['object']['action']['member_id']
			self.users.add(us_id)
			user_to_room[us_id] = self.room_id
			return True
		return False

	def set_lead(self, id0):
		self.lead_id = id0
		vk.messages.send(
			group_id=GROUP_ID,
			peer_id=self.room_id,
			random_id=random.randint(1, 10 ** 7),
			# sticker_id=12710,
			message=f'{get_name(id0)} ведущий'
		)

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

		vk.messages.send(
			group_id=GROUP_ID,
			peer_id=self.room_id,
			random_id=random.randint(1, 10 ** 7),
			# sticker_id=12710,
			message=f"""Контакт!.
					Идёт отсчёт: 10 секунд"""
		)
		try:
			self.contact_now = True
			wait0()
			self.contact_now = False
			result = self.check()
			vk.messages.send(
				group_id=GROUP_ID,
				peer_id=self.room_id,
				random_id=random.randint(1, 10 ** 7),
				# sticker_id=12710,
				message=result
			)

			s = ''
			for key, value in self.contact_words.items():
				s += get_name(key) + ': ' + value + '\n'

			vk.messages.send(
				group_id=GROUP_ID,
				peer_id=self.room_id,
				random_id=random.randint(1, 10 ** 7),
				# sticker_id=12710,
				message=f'{get_name(self.lead_id)}: {self.lead_words}\n' + s
			)
		except Exception as e:
			print('!!!', e)

	def check(self):
		# Проверка на удачность контакта
		check_dict = defaultdict(set) # word: {id1, id2...}
		for id0, word in self.contact_words.items():
			check_dict[word].add(id0)
		check_set = set(check_dict.keys()) - self.lead_words
		checklist1 = filter(lambda x: check_dict[x].len() > 1, list(check_set))
		checklist2 = filter(lambda x: check_dict[x].len() > 1, list(self.lead_words))
		if checklist1:
			return 'Контакт прошел успешно'
		if not checklist2:
			return 'Игроки не сконтактировали'
		if checklist2:
			return 'Ассоциация сбита'

	def help(self):
		vk.messages.send(
			group_id=GROUP_ID,
			peer_id=self.room_id,
			random_id=random.randint(1, 10 ** 7),
			# sticker_id=12710,
			message='Правила игры'
		)

	def processing_ls(self, ev):
		# обработка лс
		if self.keyword is None and self.lead_id is not None:
			self.keyword = ev.raw['object']['text']
		if self.contact_now:
			if ev.raw['object']['from_id'] == self.lead_id:
				self.lead_words.add(ev.raw['object']['text'])
			else:
				self.contact_words[ev.raw['object']['from_id']] = ev.raw['object']['text']

	def final(self):
		pass


def new_room(ev):
	# если новая беседа, то создаётся мастер
	if 'action' in ev.raw['object'] \
	and ev.raw['object']['action']['type'] == 'chat_invite_user' \
	and ev.raw['object']['action']['member_id'] == -GROUP_ID:
		masters[ev.raw['object']['peer_id']] = Master(ev.raw['object']['peer_id'])
		return True
	return False


def wait0(delay=10):
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
