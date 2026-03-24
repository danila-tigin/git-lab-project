import socket
import threading
import sys

CMD_REGISTER = "REGISTER"
CMD_BID = "BID"
CMD_GET_LOT = "GET_LOT"
CMD_QUIT = "QUIT"

RESP_OK = "OK"
RESP_ERROR = "ERROR"
RESP_LOT_INFO = "LOT_INFO"
RESP_BID_ACCEPTED = "BID_ACCEPTED"
RESP_BROADCAST = "BROADCAST"
RESP_WINNER = "WINNER"


class AuctionClient:
    def __init__(self, host='localhost', port=8888):
        self.host = host
        self.port = port
        self.socket = None
        self.nickname = None

    def connect(self):
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.host, self.port))
            print(f"Подключен к {self.host}:{self.port}")

            threading.Thread(target=self._receive, daemon=True).start()
            return True
        except Exception as e:
            print(f"Ошибка подключения: {e}")
            return False

    def _receive(self):
        while True:
            try:
                data = self.socket.recv(1024).decode().strip()
                if not data:
                    break
                # Разделяем сообщения, если пришло несколько
                for msg in data.split('\n'):
                    if msg.strip():
                        self._process(msg.strip())
            except:
                break
        print("\nСоединение разорвано")
        sys.exit(0)

    def _process(self, msg):
        # Пропускаем пустые сообщения
        if not msg:
            return

        # Разделяем команду и данные
        if '|' in msg:
            parts = msg.split('|', 1)
            cmd = parts[0]
            content = parts[1] if len(parts) > 1 else ""
        else:
            # Для сообщений без разделителя (OK, ERROR)
            parts = msg.split(maxsplit=1)
            cmd = parts[0]
            content = parts[1] if len(parts) > 1 else ""

        # Обработка команд
        if cmd == RESP_OK:
            print(f"\n✓ {content}")

        elif cmd == RESP_ERROR:
            print(f"\n✗ {content}")

        elif cmd == RESP_LOT_INFO:
            # LOT_INFO|название|цена|время
            lot_data = content.split('|')
            if len(lot_data) >= 3:
                name = lot_data[0].replace('_', ' ')
                price = lot_data[1]
                time_left = lot_data[2]
                print(f"\n=== Текущий лот ===")
                print(f"Лот: {name}")
                print(f"Текущая цена: {price}")
                print(f"Осталось времени: {time_left} сек")
                print("===================")

        elif cmd == RESP_BID_ACCEPTED:
            print(f"\n✓ Ставка {content} принята! Вы лидер!")

        elif cmd == RESP_BROADCAST:
            # BROADCAST|отправитель|сообщение
            if content and '|' in content:
                sender, text = content.split('|', 1)
                if sender == "Система":
                    print(f"\n[Система] {text}")
                else:
                    print(f"\n[{sender}] {text}")

        elif cmd == RESP_WINNER:
            # WINNER|победитель|цена
            winner_data = content.split('|')
            if len(winner_data) >= 2:
                print(f"\n🏆 ПОБЕДИТЕЛЬ: {winner_data[0]} с ценой {winner_data[1]} 🏆")

    def send(self, cmd):
        try:
            self.socket.send(f"{cmd}\n".encode())
        except:
            print("Ошибка отправки")

    def run(self):
        if not self.connect():
            return

        print("\n=== АУКЦИОН ===")
        print("/reg <ник> - регистрация")
        print("/bid <сумма> - сделать ставку")
        print("/info - информация о текущем лоте")
        print("/quit - выход")
        print("===============\n")

        while True:
            try:
                text = input("> ").strip()
                if not text:
                    continue

                if text.startswith('/'):
                    parts = text.split()
                    cmd = parts[0][1:].upper()

                    if cmd == "REG" and len(parts) > 1:
                        self.nickname = parts[1]
                        self.send(f"{CMD_REGISTER} {parts[1]}")
                    elif cmd == "BID" and len(parts) > 1:
                        try:
                            float(parts[1])
                            self.send(f"{CMD_BID} {parts[1]}")
                        except:
                            print("Сумма должна быть числом")
                    elif cmd == "INFO":
                        self.send(CMD_GET_LOT)
                    elif cmd == "QUIT":
                        self.send(CMD_QUIT)
                        break
                    else:
                        print("Неверная команда. Используйте: /reg, /bid, /info, /quit")
                else:
                    print("Используйте / для команд")

            except KeyboardInterrupt:
                break

        self.socket.close()
        print("Клиент остановлен")


if __name__ == "__main__":
    host = sys.argv[1] if len(sys.argv) > 1 else 'localhost'
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 8888

    client = AuctionClient(host, port)
    client.run()