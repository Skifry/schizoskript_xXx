from prompt_toolkit import PromptSession
from prompt_toolkit import print_formatted_text as print
from prompt_toolkit import HTML


async def login(session: PromptSession):
    print("Войдите в аккаунт:")
    username = await session.prompt_async(
        HTML(" <magenta>-</magenta> Имя пользователя: ")
    )
    password = await session.prompt_async(
        HTML(" <magenta>-</magenta> Пароль: "), is_password=True
    )
    return username, password
