from datetime import datetime
from functools import wraps


def logger(path):
    """
    Декоратор, который записывает в файл дату и время вызова,
    имя функции, аргументы и возвращаемое значение.
    """

    def __logger(old_function):
        @wraps(old_function)
        def new_function(*args, **kwargs):
            start = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            result = old_function(*args, **kwargs)

            # Формируем строку для записи в файл
            log_entry = (
                f"дата и время вызова функции {start}\n"
                f"имя функции: {old_function.__name__}\n"
                f"аргументы: {args}\n"
                f"именованные аргументы: {kwargs}\n"
                f"возвращаемое значение: {result}\n"
            )

            # Записываем данные в файл
            with open(path, 'a', encoding='utf-8') as log_file:
                log_file.write(log_entry)

            return result

        return new_function

    return __logger