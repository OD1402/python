import requests
from bs4 import BeautifulSoup
import csv
from collections import defaultdict
import re


def get_animals_from_wikipedia():
    base_url = "https://ru.wikipedia.org/wiki/Категория:Животные_по_алфавиту"
    result = defaultdict(int)

    # Функция для обработки одной страницы
    def process_page(url):
        print(f"Парсим url {url}")
        response = requests.get(url)
        soup = BeautifulSoup(response.text, "html.parser")

        # Находим все ссылки в основном содержимом категории
        content_div = soup.find("div", id="mw-pages")
        if not content_div:
            return None

        # Извлекаем все названия животных
        animal_links = content_div.find_all("a")

        for link in animal_links:
            animal_name = link.text.strip()
            if animal_name:  
                # print(animal_name)
                
                # Получаем первую букву названия
                first_letter = animal_name[0].upper()
                result[first_letter] += 1

        # Находим ссылку на следующую страницу (если есть)
        next_link = None
        links = content_div.find_all("a")
        for link in links:
            if link.text == "Следующая страница":
                next_link = "https://ru.wikipedia.org" + link["href"]
                break
                # match = re.search(r"pagefrom=[А-Я]", link["href"])
                # if match:
                #     # после Я начинается англ алфавит
                #     # https://ru.wikipedia.org/w/index.php?title=Категория:Животные_по_алфавиту&pagefrom=Японская+трясогузка#mw-pages
                #     next_link = "https://ru.wikipedia.org" + link["href"]
                #     break
        return next_link

    # Начинаем с первой страницы
    next_page = base_url

    # Обрабатываем все страницы
    while next_page:
        next_page = process_page(next_page)

    return result


def save_to_csv(result, filename="beasts.csv"):
    # Сортируем буквы по алфавиту
    sorted_letters = sorted(result.keys())

    # Записываем результаты в CSV
    with open(filename, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        for letter in sorted_letters:
            writer.writerow([letter, result[letter]])

    print(f"Результаты сохранены в файл {filename}")


if __name__ == "__main__":
    # Получаем данные с Википедии
    result = get_animals_from_wikipedia()

    # Сохраняем результаты в CSV
    save_to_csv(result)

    # Выводим результаты для проверки
    for letter, count in sorted(result.items()):
        print(f"{letter}: {count}")
