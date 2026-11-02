# GGE Marketplace

## О системе
GGE Marketplace — демонстрационное приложение бэкенда маркетплейса.

Приложение состоит из модулей:
- каталог товаров
- заказы
- ETL модуль

Приложение написано по методологии DDD (Domain-Driven Design) и паттерну Unit of Work. 

ETL модуль предназначен для построчной обработки больших объемов данных (XLSX) через промежуточные staging-таблицы без перегрузки оперативной памяти (RAM).

Технологический стек:
- Backend: Python 3.13 / Django 5+ / Django REST Framework
- Пакетный менеджер: UV (быстрая синхронизация зависимостей)
- Асинхронные задачи: Celery
- Брокер сообщений: RabbitMQ (с разделением задач по очередям)
- База данных: SQLite

## Инструкция по быстрому запуску через Docker Compose


### 1. Подготовка окружения

Перед запуском убедитесь, что в корне проекта создан файл .env, а на жестком диске создана локальная папка для хранения файлов.
Пример содержимого .env:
```env
RABBITMQ_DEFAULT_USER=myuser
RABBITMQ_DEFAULT_PASS=mypassword

DJANGO_SECRET_KEY=your_secret_key_here
CELERY_BROKER_URL=amqp://myuser:mypassword@rabbitmq:5672//

DJANGO_DEBUG=True
```

### 2. Сборка и запуск контейнеров

Запустите всю инфраструктуру (Web-сервер, Celery-воркер тяжелых пайплайнов и RabbitMQ) одной командой:
```bash
docker compose up -d --build
```
Флаг --build принудительно пересоберет образы с учетом актуальных Python-зависимостей, а флаг -d запустит процессы в фоновом режиме.

### 3. Инициализация базы данных и создание администратора

Выполните миграции и настройте суперпользователя напрямую внутри работающего контейнера без запуска интерактивной сессии:
bash
#### Применение миграций Django
```bash
docker compose exec web python gge_marketplace/manage.py migrate
```

#### Создание суперпользователя
Создание пользователя с реквизитами:
- логин: admin, 
- пароль: admin

```bash
docker compose exec -e DJANGO_SUPERUSER_USERNAME=admin -e DJANGO_SUPERUSER_EMAIL=admin@email.ru -e DJANGO_SUPERUSER_PASSWORD=admin web python gge_marketplace/manage.py createsuperuser --no-input
```
Теперь панель администратора доступна по адресу: http://localhost:8000/admin/

### 4. Полезные команды для мониторинга и остановки

- Просмотр логов обработки файлов в Celery (в реальном времени):
```bash
docker compose logs -f celery
```
- Просмотр логов веб-сервера API:
```bash
docker compose logs -f web
```
- Остановка проекта с сохранением всех данных:
```bash
docker compose down
```
- Полный сброс проекта (остановка с удалением всех папок и баз данных):
```bash
docker compose down -v
```

## API
API описано в Swagger: http://localhost:8000/api/docs/