
import random
import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType


def main():
    token = 'b677113e34fc7a2aba2f407a091e4ff9e3a38d4c2e40f6945db05759646f9631f2c87ad072e250b462900'
    vk_session = vk_api.VkApi(token=token)
    vk = vk_session.get_api()
    longpoll = VkLongPoll(vk_session)
    for event in longpoll.listen():
        if event.type == VkEventType.MESSAGE_NEW and event.to_me and event.text:
            # если пришло сообщение:
            if event.from_user:
                # если написали в лс
                print('!')
                # vk.messages.send(  # Отправляем сообщение
                #     user_id=event.user_id,
                #     random_id=random.randint(1, 10 ** 7),
                #     message=f'Пришло сообщение от {user_id}'
                # )
                vk.wall.post(
                    owner_id=-194517385,
                    from_group=1,
                    message=f'@id{event.user_id} написал мне "{event.text}"',
                    signed=1,
                    guid=random.randint(1, 2**64)
                )
            elif event.from_chat:
                # если написали в чат
                vk.messages.send(  # Отправляем собщение
                    chat_id=event.chat_id,
                    random_id=random.randint(1, 10 ** 7),
                    message=f'Пришло сообщение от {chat_id}'
                )


if __name__ == '__main__':
    main()
