#
# Серверное приложение для соединений
#
import asyncio
from asyncio import transports


class ServerProtocol(asyncio.Protocol):
    login: str = None
    server: 'Server'
    transport: transports.Transport

    def __init__(self, server: 'Server'):
        self.server = server

    def data_received(self, data: bytes):
        print(data)

        decoded = data.decode()

        # При каждом соединении создаем список логинов для проверки
        logins = list()
        for client in self.server.clients:
            logins.append(client.login)

        if self.login is not None:
            self.send_message(decoded)
        else:
            if decoded.startswith("login:"):
                self.login = decoded.replace("login:", "").replace("\r\n", "")
                # Для проверки, есть ли клиент с таким логином в чате
                if self.login in logins:
                    self.transport.write(
                        f"Логин {self.login} занят, попробуйте другой\n".encode()
                    )
                    # Обрыв соединения в случае того, если логин такой существует
                    self.transport.abort()
                else:
                    self.transport.write(
                        f"Привет, {self.login}!\n".encode()
                    )
                    # В случае успешного входа посылаем историю сообщений
                    self.send_history()
            else:
                self.transport.write("Неправильный логин\n".encode())

    def connection_made(self, transport: transports.Transport):

        self.server.clients.append(self)
        self.transport = transport
        print("Пришел новый клиент")

    def connection_lost(self, exception):
        self.server.clients.remove(self)
        print("Клиент вышел")

    def send_message(self, content: str):
        message = f"{self.login}: {content}\n"
        self.server.messages.append(message)

        for user in self.server.clients:
            user.transport.write(message.encode())

    # Необходимый метод посылки истории сообщений
    def send_history(self):
        # Если количество сообщений больше 10 - берем только 10
        if len(self.server.messages) > 10:
            for message in self.server.messages[:10]:
                self.transport.write(f"{message}".encode())
        # Если количество сообщений меньше 10 - берем все
        else:
            for message in self.server.messages:
                self.transport.write(f"{message}".encode())


class Server:
    clients: list
    # Тут создаем еще список для всех сообщений
    messages: list

    def __init__(self):
        self.clients = []
        # Инициализируем список
        self.messages = list()

    def build_protocol(self):
        return ServerProtocol(self)

    async def start(self):
        loop = asyncio.get_running_loop()

        coroutine = await loop.create_server(
            self.build_protocol,
            '127.0.0.1',
            8888
        )

        print("Сервер запущен ...")

        await coroutine.serve_forever()


process = Server()

try:
    asyncio.run(process.start())
except KeyboardInterrupt:
    print("Сервер остановлен вручную")


