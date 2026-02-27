# Python Django + Telegram Bot
## Система складу для деталей до моделей iPhone

Цей проєкт складається з:
- **Django бекенду**, який за допомогою admin панелі дозволяє додавати типи запчастин і керувати їхньою кількістю;
- **Telegram-бот** (на `pytelegrambotapi`), працює з BackEnd частиною через ендпоінти, може списувати деталі та створювати списки закупівлі;
- **Docker-оточення** для зручного запуску;

---

## Стек технологій

- [Django 5.2.11](https://www.djangoproject.com/download/)
- [Python 3.11.5](https://www.python.org/)
- [PyTelegramBotAPI](https://pypi.org/project/pyTelegramBotAPI/)
- [Docker & Docker Compose](https://www.docker.com/)


### 1. Клонування репозиторію
```bash
git clone https://github.com/GrinikNazar/Flarken-2.0.git
cd Flarken-2.0
```

### 2. Створення віртуального оточення
````
python -m venv venv
source venv/bin/activate  # Linux / Mac
venv\Scripts\activate     # Windows
````

### 3. Встановлення залежностей
```
pip install -r requirements.txt
```
### 3.1. Створити файл requirements
```
 pip freeze > requirements.txt
```

### 4. Створення .env файлу
У корені проєкту створіть .env файл
```
BOT_TOKEN=your_telegram_bot_token
```

## API Ендпоінти
| Метод  | Ендпоінт | Опис                                                    |
|--------|-----|---------------------------------------------------------|
| `POST` | `warehouse/write-off` | Списати позицію                                         |
| `GET`  | `/warehouse/purchase-list` | Отримати список закупівлі для конкретного постачальника |
| `GET`  | `/warehouse/purchase-list-part-type` | Отримати список закупівлі по типу запчастини            |
| `GET`  | `/warehouse/list-of-part-types/` | Отримати список наявної кількості по типу запчастини    |


---
## Перенесення бази даних

### Зробити бекап
❗ **Примітка:** робити з командного рядка не з IDE ❗
```
python -X utf8 manage.py dumpdata --indent 4 --exclude contenttypes --exclude auth.permission --exclude sessions > data.json
```
### Завантажити з файлу data.json
```
python manage.py loaddata data.json
```