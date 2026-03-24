import socket
import threading
import time
import signal

# Константы протокола
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


class AuctionServer:
    def __init__(self, host='localhost', port=8888):
        self.host = host
        self.port = port
        self.clients = {}
        self.running = True
        self.lots = [
            {"name": "Картина_Звездная_ночь", "price": 1000.0},
            {"name": "Винтажные_часы_Rolex", "price": 5000.0},
            {"name": "Коллекция_монет", "price": 2000.0}
        ]
        self.current_lot = None
        self.lot_index = 0
        self.lot_start_time = 0
        self.lot_duration = 30
        self.current_leader = None
        self.current_price = 0.0

    def start(self):
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server.bind((self.host, self.port))
        self.server.listen(5)
        print(f"Сервер запущен на {self.host}:{self.port}")

        threading.Thread(target=self._auction_loop, daemon=True).start()

        while self.running:
            try:
                client, addr = self.server.accept()
                print(f"Подключен {addr}")
                self.clients[client] = {"nickname": None, "addr": addr}
                threading.Thread(target=self._handle_client, args=(client,), daemon=True).start()
            except:
                break

    def _handle_client(self, client):
        while self.running:
            try:
                data = client.recv(1024).decode().strip()
                if not data:
                    break

                parts = data.split()
                cmd = parts[0].upper()

                if cmd == CMD_REGISTER and len(parts) > 1:
                    nickname = parts[1]
                    # Проверка уникальности
                    taken = False
                    for c in self.clients.values():
                        if c["nickname"] == nickname:
                            taken = True
                            break

                    if taken:
                        client.send(f"{RESP_ERROR} Никнейм занят\n".encode())
                    else:
                        self.clients[client]["nickname"] = nickname
                        client.send(f"{RESP_OK} Добро пожаловать, {nickname}!\n".encode())
                        self._send_lot_info(client)
                        self._broadcast(f"{RESP_BROADCAST}|Система|{nickname} присоединился")

                elif cmd == CMD_BID and len(parts) > 1:
                    if not self.clients[client]["nickname"]:
                        client.send(f"{RESP_ERROR} Сначала зарегистрируйтесь\n".encode())
                        continue

                    try:
                        amount = float(parts[1])
                    except:
                        client.send(f"{RESP_ERROR} Неверная сумма\n".encode())
                        continue

                    if not self.current_lot:
                        client.send(f"{RESP_ERROR} Аукцион не активен\n".encode())
                    elif time.time() - self.lot_start_time > self.lot_duration:
                        client.send(f"{RESP_ERROR} Время для ставок истекло\n".encode())
                    elif amount <= self.current_price:
                        client.send(f"{RESP_ERROR} Ставка должна быть больше {self.current_price:.2f}\n".encode())
                    else:
                        self.current_price = amount
                        self.current_leader = self.clients[client]["nickname"]
                        client.send(f"{RESP_BID_ACCEPTED} {amount:.2f}\n".encode())
                        self._broadcast(f"{RESP_BROADCAST}|{self.current_leader}|Ставка {amount:.2f}")

                elif cmd == CMD_GET_LOT:
                    self._send_lot_info(client)

                elif cmd == CMD_QUIT:
                    client.send(f"{RESP_OK} До свидания\n".encode())
                    break

            except Exception as e:
                print(f"Ошибка: {e}")
                break

        self._remove_client(client)

    def _send_lot_info(self, client):
        if self.current_lot:
            time_left = max(0, self.lot_duration - (time.time() - self.lot_start_time))
            # Формат: LOT_INFO|название|цена|время
            msg = f"{RESP_LOT_INFO}|{self.current_lot['name']}|{self.current_price:.2f}|{int(time_left)}\n"
            client.send(msg.encode())
        else:
            client.send(f"{RESP_ERROR} Аукцион не начат\n".encode())

    def _broadcast(self, message):
        for client in list(self.clients.keys()):
            try:
                client.send(f"{message}\n".encode())
            except:
                self._remove_client(client)

    def _remove_client(self, client):
        if client in self.clients:
            nickname = self.clients[client]["nickname"]
            del self.clients[client]
            try:
                client.close()
            except:
                pass
            if nickname:
                self._broadcast(f"{RESP_BROADCAST}|Система|{nickname} покинул аукцион")

    def _auction_loop(self):
        while self.running:
            if not self.current_lot:
                # Запуск первого лота
                if self.lot_index < len(self.lots):
                    self.current_lot = self.lots[self.lot_index]
                    self.current_price = self.current_lot["price"]
                    self.current_leader = None
                    self.lot_start_time = time.time()
                    self.lot_index += 1
                    self._broadcast(
                        f"{RESP_BROADCAST}|Система|Новый лот: {self.current_lot['name'].replace('_', ' ')}, старт: {self.current_price:.2f}")
                    print(f"Начался лот: {self.current_lot['name']}")
                else:
                    self._broadcast(f"{RESP_BROADCAST}|Система|Аукцион завершен!")
                    self.running = False

            elif time.time() - self.lot_start_time > self.lot_duration:
                # Завершение текущего лота
                if self.current_leader:
                    self._broadcast(f"{RESP_WINNER}|{self.current_leader}|{self.current_price:.2f}")
                    self._broadcast(
                        f"{RESP_BROADCAST}|Система|Победитель: {self.current_leader} с ценой {self.current_price:.2f}")
                else:
                    self._broadcast(
                        f"{RESP_BROADCAST}|Система|Лот '{self.current_lot['name'].replace('_', ' ')}' не продан")

                # Переход к следующему лоту
                if self.lot_index < len(self.lots):
                    self.current_lot = self.lots[self.lot_index]
                    self.current_price = self.current_lot["price"]
                    self.current_leader = None
                    self.lot_start_time = time.time()
                    self.lot_index += 1
                    self._broadcast(
                        f"{RESP_BROADCAST}|Система|Новый лот: {self.current_lot['name'].replace('_', ' ')}, старт: {self.current_price:.2f}")
                    print(f"Начался лот: {self.current_lot['name']}")
                else:
                    self.current_lot = None
                    self._broadcast(f"{RESP_BROADCAST}|Система|Аукцион завершен!")
                    self.running = False

            time.sleep(1)

    def shutdown(self):
        self.running = False
        self._broadcast(f"{RESP_BROADCAST}|Система|Сервер остановлен")
        for client in list(self.clients.keys()):
            try:
                client.close()
            except:
                pass
        self.server.close()
        print("Сервер остановлен")


if __name__ == "__main__":
    import sys

    host = sys.argv[1] if len(sys.argv) > 1 else 'localhost'
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 8888

    server = AuctionServer(host, port)


    def signal_handler(sig, frame):
        print("\nЗавершение...")
        server.shutdown()
        sys.exit(0)


    signal.signal(signal.SIGINT, signal_handler)
    server.start()