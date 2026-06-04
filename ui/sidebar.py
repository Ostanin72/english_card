# ============================================================
# ИНТЕРФЕЙС ПРИЛОЖЕНИЯ
# ============================================================
import contextlib
import io
import random as rnd

import pandas as pd
import streamlit as st

from db.user import add_personal_word, delete_personal_word
from db.user import get_statistics, update_stats, render_schema

from streamlit.runtime.scriptrunner_utils.exceptions import RerunException
from streamlit.runtime.scriptrunner_utils.script_requests import RerunData


def render_sidebar():
    """
    TODO: Реализовать боковую панель с авторизацией
    - Поле для ввода имени
    - Кнопка входа
    - Приветствие после входа
    - Кнопка выхода
    """

    st.sidebar.title("Профиль")
    is_auth = st.session_state.get("is_auth", False)
    if is_auth:
        username = st.session_state.get("username", "Гость")
        st.sidebar.success(f"✅ Привет, {username}!")
        if st.sidebar.button("Выйти"):
            st.session_state["is_auth"] = False
            st.session_state["user_id"] = None
            raise RerunException(RerunData())
    else:
        st.sidebar.info("🔑 Введите имя для входа")
        with st.sidebar.form("login_form"):
            username = st.text_input("Имя пользователя")
            submit = st.form_submit_button("Войти")
            return {"submit": submit, "username": username}
    return None


# ============================================================
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ============================================================
#  Функция генерации вариантов ответов
def generate_options(correct_word, all_words):
    """
    TODO: Сгенерировать 4 варианта ответа для викторины
    Один вариант - правильный перевод, остальные - случайные слова из словаря
    Если слов не хватает, можно добавить слова-заглушки
    """
    dummy_words = ["слово1", "слово2", "слово3", "слово4", "слово5"]
    options_pool = [word.get('english_word') for word in all_words
                    if word.get('english_word') != correct_word]
    needed = 3 - len(options_pool)
    if needed > 0:
        options_pool += dummy_words[:needed]
    random_options = rnd.sample(options_pool, 3)
    options = random_options + [correct_word]
    rnd.shuffle(options)
    return options


#  Функция отображения схемы БД
def capture_render_schema():
    """
    Вызывает render_schema() и перехватывает её вывод (stdout) в строку.
    """
    buffer = io.StringIO()

    with contextlib.redirect_stdout(buffer):
        result = render_schema()

    captured_output = buffer.getvalue()
    return result if result is not None else captured_output


# ============================================================
# ОСНОВНЫЕ ФУНКЦИИ
# ============================================================
# Главная страница
def render_study_tab(words):
    """
    TODO: Реализовать вкладку изучения слов
    - Отображение текущего слова на русском
    - 4 кнопки с вариантами перевода
    - Обработка правильных/неправильных ответов
    - Кнопка следующего слова
    """
    if 'current_index' not in st.session_state:
        st.session_state.current_index = 0
        st.session_state.score = 0
        st.session_state.options = []
        st.session_state.correct_answers = 0
        st.session_state.wrong_answers = 0

    if not words:
        st.warning("Ваша база слов пуста. "
                   "Добавьте слова на вкладке '➕ Добавить слово'.")
        return

    current_index = st.session_state.current_index
    current_word_dict = words[current_index]
    original_word = current_word_dict.get('russian_word')
    correct_translation = current_word_dict.get('english_word')
    word_id = current_word_dict.get('id')
    word_type = current_word_dict.get('word_type')

    if not st.session_state.options:
        st.session_state.options = generate_options(correct_translation, words)
    options = st.session_state.options

    st.markdown(f"### 📖 Изучаем слова **{current_index + 1}** из {len(words)}")
    st.subheader(f"Как будет по-английски слово: **{original_word}**?")

    with st.form(key="answer_form"):
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            submit1 = st.form_submit_button(options[0], key="button_1")
        with col2:
            submit2 = st.form_submit_button(options[1], key="button_2")
        with col3:
            submit3 = st.form_submit_button(options[2], key="button_3")
        with col4:
            submit4 = st.form_submit_button(options[3], key="button_4")

        st.info("Если выбрали ПРАВИЛЬНЫЙ ответ, "
                "для перехода к следующему слову нажмите кнопку ниже ⬇️")

        submitted = st.form_submit_button("Следующее слово", type="secondary")

    if submitted or any([submit1, submit2, submit3, submit4]):
        user_choice = None
        if submit1:
            user_choice = options[0]
        if submit2:
            user_choice = options[1]
        if submit3:
            user_choice = options[2]
        if submit4:
            user_choice = options[3]

        if user_choice is not None and st.session_state.user_id:
            if user_choice == correct_translation:
                st.success("✅ Верно!")
                st.info(f"Слово **{original_word}** переводится как"
                        f" **{correct_translation}**")
                st.session_state.correct_answers += 1
                st.balloons()
                update_stats(
                    user_id=st.session_state.user_id,
                    word_id=word_id,
                    word_type=word_type,
                    is_correct=True
                )

                if current_index < len(words) - 1:
                    st.session_state.current_index += 1
                else:
                    st.info("Вы закончили все слова! Можем начать снова.")
                    st.session_state.current_index = 0

                st.session_state.options = []
            else:
                error_msg = "❌ Неверно. Попробуй еще раз!"
                st.error(error_msg)
                st.session_state.feedback = error_msg
                st.session_state.wrong_answers += 1
                update_stats(
                    user_id=st.session_state.user_id,
                    word_id=word_id,
                    word_type=word_type,
                    is_correct=False
                )

    st.divider()
    st.subheader("Схема базы данных PostgreSQL")
    show_schema = st.checkbox("Показать схему базы данных")
    if show_schema:
        st.info("Загрузка схемы... Подождите.")
        try:
            schema_text = capture_render_schema()
            st.code(schema_text, language='text')
            st.success("Готово!")
        except Exception as e:
            st.error(f"Произошла ошибка: {e}")


# Страница добавления слова
def render_add_word_tab():
    """
    TODO: Реализовать вкладку добавления слова
    - Поле для ввода слова на русском
    - Поле для ввода перевода
    - Кнопка добавления
    - Уведомление об успешном добавлении
    """
    st.info("Добавьте русское слово и его перевод на английский язык ➕  ")

    if 'show_success' not in st.session_state:
        st.session_state.show_success = False

    with st.form("add_word_form"):
        russian_word = st.text_input("Русское слово").strip()
        english_word = st.text_input("Перевод на английский язык").strip()
        is_submitted = st.form_submit_button("Добавить")

    user_id = st.session_state.user_id

    if is_submitted:
        if russian_word and english_word:
            success = add_personal_word(user_id, russian_word, english_word)
            if success is True:
                st.success(f"✅ Слово '{russian_word}' и его перевод "
                           f"'{english_word}' добавлены в ваш словарь!")
            elif success is False:
                st.error(f"Слово '{russian_word}' уже есть в вашем словаре.")
            else:
                st.error("Произошла непредвиденная ошибка "
                         "при добавлении слова. Попробуйте еще раз.")
        else:
            st.warning("⚠️ Пожалуйста, заполните оба поля перед добавлением.")

        if st.button("Добавить еще слово"):
            st.rerun()


# Страница удаления слова
def render_delete_word_tab(words):
    """
    TODO: Реализовать вкладку удаления слова
    - Выпадающий список с персональными словами пользователя
    - Кнопка удаления
    - Подтверждение удаления
    """

    if 'show_confirm' not in st.session_state:
        st.session_state.show_confirm = False
    if 'word_to_delete' not in st.session_state:
        st.session_state.word_to_delete = None
    if 'delete_in_progress' not in st.session_state:
        st.session_state.delete_in_progress = False
    if 'delete_error' not in st.session_state:
        st.session_state.delete_error = None

    st.info("Вы можете 🗑️ удалить любое слово, которое ранее добавили.")

    if not words:
        st.info("У вас пока нет добавленных слов.")
        return

    word_options = {f"{word['russian_word']} (ID: {word['id']})":
                    word for word in words}

    widget_key = f"delete_select_{hash(frozenset([w['id'] for w in words]))}"

    selected_option = st.selectbox(
        "Выберите слово из выпадающего списка",
        options=[""] + list(word_options.keys()),
        key=widget_key
    )

    delete_button_visible = (bool(
        selected_option)
        and not st.session_state.show_confirm
        and not st.session_state.delete_in_progress)

    if delete_button_visible and st.button("Удалить выбранное слово"):
        st.session_state.word_to_delete = word_options[selected_option]
        st.session_state.show_confirm = True
        st.rerun()

    if (st.session_state.show_confirm
            and not st.session_state.delete_in_progress):
        st.warning(
            f"Вы собираетесь удалить слово: "
            f"**{st.session_state.word_to_delete['russian_word']}**. "
            f"Это действие необратимо.")
        if st.button("Подтвердить удаление"):
            st.session_state.delete_in_progress = True
            st.rerun()

        if st.button("Отмена"):
            st.session_state.show_confirm = False
            st.session_state.word_to_delete = None
            st.rerun()

    if (st.session_state.delete_in_progress
            and st.session_state.word_to_delete):
        with st.spinner(
                f"Удаляется слово "
                f"'{st.session_state.word_to_delete['russian_word']}'"
        ):
            try:
                user_id = st.session_state.user_id
                word_id = st.session_state.word_to_delete['id']
                success = delete_personal_word(user_id, word_id)
                if success:
                    st.success("Слово успешно удалено!")
                    print("Слово успешно удалено!")

                    st.session_state.show_confirm = False
                    st.session_state.word_to_delete = None
                    st.session_state.delete_in_progress = False
                    if st.button("Перейти к списку слов"):
                        st.rerun()
                else:
                    raise Exception("Функция удаления вернула False. "
                                    "Не удалось выполнить операцию.")
            except Exception as e:
                st.error(f"Произошла ошибка при удалении: {e}")
                st.session_state.delete_error = str(e)
                st.session_state.delete_in_progress = False


# Страница статистики
def render_statistics_tab(user_id):
    """
    TODO: Реализовать вкладку статистики (дополнительное требование)
    - Количество изученных слов
    - Количество попыток
    - Процент правильных ответов
    - История последних попыток
    """
    st.title("Ваша статистика обучения")
    st.write("Здесь вы можете увидеть свой прогресс и последние результаты.")

    st.subheader("Ключевые показатели")
    col1, col2 = st.columns(2)
    stats = get_statistics(user_id)

    if stats is None:
        st.error("Произошла ошибка при загрузке вашей статистики.")
        return

    with col1:
        total_attempts = stats.get('total_attempts', 0)
        st.metric(label="Всего попыток", value=total_attempts)
        learned_words_count = stats.get('learned_words_count', 0)
        st.metric(label="Изучено слов", value=learned_words_count)

    with ((((col2)))):
        avg_accuracy = stats.get('avg_accuracy_percent')
        accuracy_value = (
            f"{avg_accuracy}%" if avg_accuracy is not None else "Нет данных"
        )
        st.metric(label="Точность ответов", value=accuracy_value)

    st.divider()

    st.subheader("История последних попыток")

    history_df = None

    if stats:
        words_history = stats.get('last_reviewed_words', [])
        if words_history:
            history_df = pd.DataFrame(words_history)
            history_df = history_df.rename(columns={
                'word_id': 'ID слова',
                'russian_word': 'Слово',
                'english_word': 'Перевод',
                'word_type': 'Тип',
                'correct_answers': 'Результат',
                'last_reviewed': 'Дата'
            })

            history_df = history_df[[
                'ID слова',
                'Слово',
                'Перевод',
                'Тип',
                'Результат',
                'Дата'
            ]]

            history_df['Результат'] = history_df['Результат'].map({
                True: '✅ Правильно',
                False: '❌ Ошибка'
            })

            history_df['Дата'] = (
                pd.to_datetime(history_df['Дата'], errors='coerce')
                .dt.strftime('%Y-%m-%d %H:%M:%S')
            )
        else:
            history_df = pd.DataFrame(columns=[
                'ID слова', 'Слово', 'Перевод', 'Тип', 'Результат', 'Дата'
            ])
    else:
        history_df = pd.DataFrame(columns=[
            'ID слова', 'Слово', 'Перевод', 'Тип', 'Результат', 'Дата'
        ])

    if history_df is not None and not history_df.empty:
        st.dataframe(history_df, width='stretch')
    else:
        st.info("Пока нет данных о попытках. "
                "Начните обучение, чтобы увидеть здесь свою историю!")


if st.button("Показать схему базы данных"):
    st.info("Загрузка схемы... Подождите.")
    try:
        schema_text = capture_render_schema()
        st.code(schema_text, language='text')
        st.success("Готово!")
    except Exception as e:
        st.error(f"Произошла ошибка: {e}")
