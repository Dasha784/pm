# Используем современный Python 3.13 slim
FROM python:3.12-slim


# Настройки окружения
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Устанавливаем рабочую директорию
WORKDIR /app

# Устанавливаем системные зависимости
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    tzdata \
    && rm -rf /var/lib/apt/lists/*

# Копируем зависимости и устанавливаем библиотеки
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем код бота
COPY . .

# Задаём часовой пояс и переменные окружения
ENV TZ=Europe/Kyiv \
    BOT_TOKEN=""

# Запуск бота
CMD ["python3", "предолжка.py"]
