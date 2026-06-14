"""
EnglishCard - Приложение для изучения английского языка
"""
import streamlit as st
from streamlit.runtime.scriptrunner import RerunException, RerunData
from db.init_db import init_database
from db.user import login_user
from ui.sidebar import render_sidebar, render_study_tab, render_add_word_tab
from ui.sidebar import render_statistics_tab, render_delete_word_tab
from ui.sidebar import capture_render_schema


# ============================================================
# НАСТРОЙКА СТРАНИЦЫ
# ============================================================
st.set_page_config(
    page_title="EnglishCard - Изучение английского",
    page_icon="📚",
    layout="wide"
)
st.title("📚 EnglishCard - Изучай английский с удовольствием!")


# ============================================================
# ГЛАВНАЯ ФУНКЦИЯ
# ============================================================
def main():
    """
    Главная функция приложения
    Реализовать основную логику:
    1. Инициализация БД
    2. Авторизация пользователя
    3. Отображение вкладок с функционалом
    4. Приветственное сообщение для неавторизованных пользователей
    """

    # Инициализация состояния сессии
    if "is_auth" not in st.session_state:
        st.session_state.is_auth = False
    if "user_id" not in st.session_state:
        st.session_state.user_id = None
    if "username" not in st.session_state:
        st.session_state.username = ""

    # Инициализация БД
    init_database()

    # Боковая панель с авторизацией
    form_data = render_sidebar()
    if form_data and form_data["submit"]:
        username = form_data["username"].strip()
        if username:
            user_id = login_user(username)

            if user_id is not None:
                st.session_state["is_auth"] = True
                st.session_state["username"] = username
                st.session_state["user_id"] = user_id
                raise RerunException(RerunData())
            else:
                st.sidebar.error("Произошла ошибка. Попробуйте другое имя.")

    # Основной контент в зависимости от авторизации
    if 'user_id' in st.session_state and st.session_state.user_id:
        user_id = st.session_state.user_id

        tab1, tab2, tab3, tab4 = st.tabs(
            ["📖 Изучение",
             "➕ Добавить слово",
             "🗑️ Удалить слово",
             "📊 Статистика"
             ])
        with tab1:
            render_study_tab()
        with tab2:
            render_add_word_tab()
        with tab3:render_delete_word_tab()
        with tab4:
            render_statistics_tab(user_id)
    else:
        st.title("Тренажер словарного запаса")
        st.markdown("Привет 👋 Давай попрактикуемся в английском языке.")
        st.markdown("Тренировки можешь проходить в удобном для себя темпе.")
        st.markdown("")
        st.markdown("У тебя есть возможность использовать тренажёр, "
                    "как конструктор, и собирать свою собственную базу "
                    "для обучения")
        st.markdown("Для этого воспользуйся инструментами:")
        st.markdown("- добавить слово ➕,")
        st.markdown("- удалить слово 🗑️.")
        st.markdown("")
        st.markdown("Ну что, начнём ⬇️")
        st.info("Авторизуйся в боковой панели, чтобы начать.")

    st.divider()

    st.subheader("Схема базы данных PostgreSQL")
    show_schema = st.checkbox("Показать схему базы данных", key="schema")
    if show_schema:
        st.info("Загрузка схемы... Подождите.")
        try:
            schema_text = capture_render_schema()
            st.code(schema_text, language='text')
            st.success("Готово!")
        except Exception as e:
            st.error(f"Произошла ошибка: {e}")

    st.divider()
    st.caption(
        "Приложение для изучения английских слов. Copyright © 2026 Останин КЮ"
    )


if __name__ == "__main__":
    main()
