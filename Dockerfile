# Используем базовый образ Python
FROM python:3.12

# Установка рабочей директории в контейнере
WORKDIR /bot

# Копирование файла зависимостей в контейнер
COPY req.txt .

# Обновление пакетов и установка зависимостей
RUN apt-get update && apt-get install -y gcc musl-dev

# Установка Python-зависимостей
RUN pip install -r req.txt

# Копирование остального кода приложения в контейнер
COPY . .

# Команда для запуска бота
CMD ["python", "main.py"]