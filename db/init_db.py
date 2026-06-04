# ============================================================
# РАБОТА С БАЗОЙ ДАННЫХ
# ============================================================
import os

import psycopg2
import streamlit as st

from dotenv import load_dotenv
from psycopg2 import OperationalError


load_dotenv()


def get_db_connection():
    """
    TODO: Реализовать подключение к PostgreSQL
    Параметры подключения:
    - host: localhost
    - database: english_card
    - user: postgres
    - password: postgres
    """

    host = os.getenv('host')
    database = os.getenv('database')
    user = os.getenv('user')
    password = os.getenv('password')

    try:
        conn = psycopg2.connect(
            database=database,
            host=host,
            user=user,
            password=password
        )
        print('✅ Соединение с базой данных установлено')
        return conn
    except OperationalError as e:
        st.error(f" ❌ Ошибка подключения к базе данных: {e}")
        st.stop()


def init_database():
    """
    TODO: Реализовать создание таблиц, если они не существуют
    Необходимые таблицы:
    1. users (id, username, created_at)
    2. common_words (id, russian_word, english_word, created_at)
    3. user_words (id, user_id, russian_word, english_word, created_at)
    4. learning_stats
        (id, user_id, word_id, word_type,
        correct_answers, total_attempts, last_reviewed)

    Также заполнить common_words начальными словами (минимум 10 слов)
    """

    conn = get_db_connection()
    with conn.cursor() as cur:

        # Таблица пользователей
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users(
                id SERIAL PRIMARY KEY,
                username VARCHAR(40) NOT NULL UNIQUE,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # Таблица слов
        cur.execute("""
            CREATE TABLE IF NOT EXISTS common_words(
                id SERIAL PRIMARY KEY,
                russian_word VARCHAR(40) NOT NULL,
                english_word VARCHAR(40) NOT NULL,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # Таблица слов, добавленных конкретным пользователем
        cur.execute("""
            CREATE TABLE IF NOT EXISTS user_words(
                id SERIAL PRIMARY KEY,
                user_id int NOT NULL,
                russian_word VARCHAR(40) NOT NULL,
                english_word VARCHAR(40) NOT NULL,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            );
        """)

        # Таблица статистики обучения
        cur.execute("""
            CREATE TABLE IF NOT EXISTS learning_stats(
                id SERIAL PRIMARY KEY,
                user_id int NOT NULL,
                word_id int NOT NULL,
                word_type VARCHAR(20) NOT NULL,
                correct_answers BOOLEAN NOT NULL,
                total_attempts INT NOT NULL DEFAULT 0,
                last_reviewed TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            );
        """)

        # Проверяем, есть ли уже данные в таблице слов
        cur.execute("SELECT COUNT(*) FROM common_words;")
        row_count = cur.fetchone()[0]

        # Если таблица слов пуста, выполняем инициализацию
        if row_count == 0:
            print("Таблица common_words пуста. "
                  "Выполняем первоначальное заполнение.")
            words = [
                ('Красный', 'Red'),
                ('Желтый', 'Yellow'),
                ('Зеленый', 'Green'),
                ('Синий', 'Blue'),
                ('Черный', 'Black'),
                ('Белый', 'White'),
                ('Город', 'City'),
                ('Улица', 'Street'),
                ('Дом', 'House'),
                ('Я', 'Me'),
                ('Ты', 'You'),
                ('Он', 'He'),
                ('Она', 'She'),
                ('Они', 'They')
            ]
            cur.executemany("""
                INSERT INTO common_words(russian_word, english_word)
                VALUES (%s, %s)
            """, words)
            conn.commit()
            print("Данные успешно добавлены.")
        else:
            print("Таблица common_words уже содержит данные. "
                  "Пропускаем заполнение.")
