import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import threading
import queue
import json
import re
from collections import Counter
import time

# ========== НАСТРОЙКИ ==========
MAX_THREADS = 3  # сколько страниц качаем одновременно (не грузим сайт сильно)
MAX_DEPTH = 2  # глубина обхода: 0 - только стартовая, 1 - стартовая и её ссылки и т.д.
TIMEOUT = 10  # сколько ждём ответа от сайта (секунд)


# ========== КЛАСС КРАУЛЕРА ==========
class SimpleCrawler:
    def __init__(self, start_url):
        # запоминаем с чего начинаем
        self.start_url = start_url
        # вырезаем имя сайта из адреса (например, google.com)
        self.domain = urlparse(start_url).netloc

        # очередь для страниц, которые надо скачать (каждый элемент это (ссылка, глубина))
        self.to_visit = queue.Queue()
        self.to_visit.put((start_url, 0))

        # тут храним ссылки которые уже видели (чтобы не повторяться)
        self.visited = set()
        self.visited.add(start_url)

        # тут храним готовые результаты по каждой странице
        self.results = []

        # блокировка для потоков (чтобы не сломали общие данные)
        self.lock = threading.Lock()

        # флаг что пора заканчивать
        self.stop = False

    # чистим ссылку от мусора типа #вниз и лишних слэшей
    def clean_url(self, url):
        parts = urlparse(url)
        # убираем якорь (#что-то) и приводим к обычному виду
        clean = parts._replace(fragment="").geturl()
        return clean

    # проверяем что ссылка ведёт на тот же сайт (не уходим на сторонние)
    def is_same_site(self, url):
        site = urlparse(url).netloc
        return site == self.domain or site == ''

    # вытаскиваем все ссылки со страницы
    def get_links(self, soup, page_url):
        links = set()
        # ищем все теги <a> у которых есть href
        for tag in soup.find_all('a', href=True):
            raw_link = tag['href']
            # превращаем относительную ссылку в абсолютную
            full_link = urljoin(page_url, raw_link)
            # чистим от мусора
            full_link = self.clean_url(full_link)
            # оставляем только ссылки внутри нашего сайта
            if self.is_same_site(full_link):
                links.add(full_link)
        return links

    # вытаскиваем чистый текст из html (убираем теги, скрипты, стили)
    def get_plain_text(self, html):
        soup = BeautifulSoup(html, 'html.parser')

        # удаляем ненужные части страницы (скрипты, стили, навигацию)
        for garbage in soup(["script", "style", "nav", "footer", "header", "aside"]):
            garbage.decompose()

        # берём просто текст
        text = soup.get_text(separator=' ')
        # убираем лишние пробелы и переносы строк
        text = re.sub(r'\s+', ' ', text).strip()
        return text

    # анализируем текст (считаем самые частые слова)
    def analyze(self, text, url):
        # приводим всё к нижнему регистру и находим слова (только буквы)
        words = re.findall(r'[a-zа-яё]+', text.lower())

        # считаем сколько раз каждое слово встретилось
        word_counts = Counter(words)

        # берём топ-10 самых частых слов
        top10 = word_counts.most_common(10)

        # возвращаем результат для этой страницы
        return {
            'адрес': url,
            'всего_слов': len(words),
            'уникальных_слов': len(set(words)),
            'топ_10_слов': top10
        }

    # качаем и обрабатываем одну страницу
    def process_page(self, url, depth):
        print(f"[ГЛУБИНА {depth}] Качаю: {url}")

        try:
            # скачиваем страницу
            response = requests.get(url, timeout=TIMEOUT)

            # проверяем что ответ нормальный (не 404, не 500)
            if response.status_code != 200:
                print(f"  Ошибка {response.status_code} для {url}")
                return

            # проверяем что это html страница, а не картинка или pdf
            if 'text/html' not in response.headers.get('Content-Type', ''):
                print(f"  Пропускаем (не html): {url}")
                return

            # вытаскиваем чистый текст
            clean_text = self.get_plain_text(response.text)

            # анализируем текст
            analysis = self.analyze(clean_text, url)

            # сохраняем результат (с блокировкой чтобы потоки не мешали)
            with self.lock:
                self.results.append(analysis)
                print(f"  Готово! Найдено слов: {analysis['всего_слов']}")

            # если не достигли максимальной глубины - ищем ссылки дальше
            if depth < MAX_DEPTH:
                soup = BeautifulSoup(response.text, 'html.parser')
                links = self.get_links(soup, url)

                # добавляем новые ссылки в очередь
                for link in links:
                    if link not in self.visited:
                        with self.lock:
                            if link not in self.visited:
                                self.visited.add(link)
                                self.to_visit.put((link, depth + 1))
                                print(f"  Нашёл новую ссылку: {link}")

        except requests.exceptions.Timeout:
            print(f"  Таймаут! {url} не ответил за {TIMEOUT} сек")
            # записываем ошибку в файл
            with open('errors.log', 'a', encoding='utf-8') as f:
                f.write(f"Таймаут: {url}\n")

        except requests.exceptions.ConnectionError:
            print(f"  Не могу подключиться к {url}")
            with open('errors.log', 'a', encoding='utf-8') as f:
                f.write(f"Ошибка подключения: {url}\n")

        except Exception as e:
            print(f"  Неизвестная ошибка: {e}")
            with open('errors.log', 'a', encoding='utf-8') as f:
                f.write(f"Ошибка на {url}: {e}\n")

    # что делает каждый рабочий поток
    def worker(self):
        while not self.stop:
            try:
                # берём следующую страницу из очереди (ждём не больше 2 секунд)
                url, depth = self.to_visit.get(timeout=2)
                self.process_page(url, depth)
                self.to_visit.task_done()
            except queue.Empty:
                # очередь пуста - пора выходить
                break
            except Exception as e:
                print(f"Ошибка в потоке: {e}")

    # запускаем краулер
    def start(self):
        print(f"Старт! Начинаем с {self.start_url}")
        print(f"Максимальная глубина: {MAX_DEPTH}")
        print(f"Потоков: {MAX_THREADS}")
        print("-" * 50)

        start_time = time.time()

        # создаём и запускаем потоки
        threads = []
        for i in range(MAX_THREADS):
            t = threading.Thread(target=self.worker)
            t.daemon = True  # чтобы потоки закрылись при завершении программы
            t.start()
            threads.append(t)

        # ждём пока обработается вся очередь
        self.to_visit.join()

        # говорим потокам что пора закругляться
        self.stop = True

        # ждём завершения потоков
        for t in threads:
            t.join(timeout=1)

        elapsed = time.time() - start_time

        print("-" * 50)
        print(f"ЗАВЕРШЕНО! Время: {elapsed:.2f} секунд")
        print(f"Обработано страниц: {len(self.results)}")

    # сохраняем результаты в файл
    def save_to_file(self, filename='results.json'):
        # подготовка данных для сохранения
        output = {
            'стартовый_адрес': self.start_url,
            'глубина': MAX_DEPTH,
            'всего_страниц': len(self.results),
            'результаты': self.results
        }

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(output, f, ensure_ascii=False, indent=2)

        print(f"Результаты сохранены в {filename}")


# ========== ЗАПУСК ==========
if __name__ == "__main__":
    START_URL = "https://ura.news/"

    # создаём краулер
    crawler = SimpleCrawler(START_URL)

    # запускаем обход
    crawler.start()

    # сохраняем результаты
    crawler.save_to_file()

    # первые 5 результатов
    print("\nПЕРВЫЕ 5 РЕЗУЛЬТАТОВ:")
    for i, res in enumerate(crawler.results[:5]):
        print(f"{i + 1}. {res['адрес']}")
        print(f"   Слов: {res['всего_слов']}, Уникальных: {res['уникальных_слов']}")
        print(f"   Топ-5 слов: {res['топ_10_слов'][:5]}")
        print()