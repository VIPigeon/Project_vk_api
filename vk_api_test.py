
import random
import vk_api
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEvent, VkBotMessageEvent, VkBotEventType


class Master():

	__slots__ = (
		'keyword',  # тайное слово ведущего
		'lead_id',  # id ведущего
		'associations',  # список ассоциаций
		'room_id',  # peer_id комнаты (беседы) мастера
		'users',  # set id игроков
		'cur_association'  # id игрока, загадавшего ассоциацию
	)

	def __init__(self, room_id):
		self.room_id = room_id
		self.users = set()
		self.cur_association = None

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

	def processing(self, ev):
		# обработка нового сообщения
		if not self.users:
			self.set_users()
		elif ev.raw['object']['text'] == 'Ассоциация':
			self.new_association(event.raw['object']['from_id'])
		elif ev.raw['object']['text'] == 'Контакт':
			self.make_contact()
		elif ev.raw['object']['text'] == 'Помощь':
			self.help()
		else:
			print('was')

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

	def new_player(self, ev):
		if 'action' in ev.raw['object'] \
		and ev.raw['object']['action']['type'] == 'chat_invite_user':
			us_id = ev.raw['object']['action']['member_id']
			self.users.add(us_id)
			user_to_room[us_id] = self.room_id
			return True
		return False

	def exit_player(self, ev):
		if 'action' in ev.raw['object'] \
		and ev.raw['object']['action']['type'] == 'chat_kick_user':
			us_id = ev.raw['object']['action']['member_id']
			self.users.discard(us_id)
			user_to_room.pop(us_id)
			return True
		return False

	def new_association(self, id0):
		self.cur_association = id0

	def make_contact(self):
		print('*')
		vk.messages.send(
			group_id=GROUP_ID,
			peer_id=self.room_id,
			random_id=random.randint(1, 10 ** 7),
			# sticker_id=12710,
			message='Есть контакт.\nИдёт отсчёт: 20 секунд'
		)

	def help(self):
		vk.messages.send(
			group_id=GROUP_ID,
			peer_id=self.room_id,
			random_id=random.randint(1, 10 ** 7),
			# sticker_id=12710,
			message='Правила игры'
		)

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


def processing_ls(ev):
	# обработка лс
	pass


def main():
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
					masters[pr_id].processing(event)

			if event.from_user:
				print('from_user')
				processing_ls(event)


if __name__ == '__main__':
	token = 'b677113e34fc7a2aba2f407a091e4ff9e3a38d4c2e40f6945db05759646f9631f2c87ad072e250b462900'
	vk_session = vk_api.VkApi(token=token)
	vk = vk_session.get_api()
	GROUP_ID = 194517385

	masters = {}  # {peer_id: Master(peer_id)}
	user_to_room = {}  # {user_id: room_id}
	main()
