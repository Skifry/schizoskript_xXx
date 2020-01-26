import asyncio
import logging

import asyncssh
from pygments.lexers.html import HtmlLexer

from shizoserver.utils import tip_say, input_code, eval_code, play_frames
from shizoserver.texts import LOGO, INTRO
from shizoserver.levels import LEVELS, levels_style
from shizoserver.menu.login import login
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.contrib.ssh import PromptToolkitSSHServer
from prompt_toolkit.lexers import PygmentsLexer
from prompt_toolkit.shortcuts import ProgressBar, print_formatted_text
from prompt_toolkit.shortcuts.dialogs import input_dialog, yes_no_dialog
from prompt_toolkit.shortcuts.prompt import PromptSession
from prompt_toolkit import HTML
from prompt_toolkit.validation import Validator


def select_level_valid(text):
    return text.isdigit() and 0 <= int(text) < len(LEVELS)


select_level_validator = Validator.from_callable(
    select_level_valid,
    error_message='Выберте уровень из списка!',
    move_cursor_to_end=True
)


async def interact() -> None:
    prompt_session = PromptSession()
    print = print_formatted_text
    print(LOGO)
    print(tip_say("Привет!\n" "Ты новенький или уже <i>codar</i>?\n\n"))

    has_account = await prompt_session.prompt_async(
        HTML("У вас есть аккаунт? " "[<b>Y</b>/n]: ")
    )

    if has_account.lower() in ["y", "д"]:
        username, password = await login(prompt_session)
    else:
        print(
            HTML(
                "Вы думали это будет регистрация, но это был я, <i>connection closed!</i>"
            )
        )
        return

    if username != "admin" and password != "admin":
        print_formatted_text(HTML("<red>Неверный логин или пароль!</red>"))
        return
    print()
    print(HTML(INTRO))
    print(HTML('\n<b><yellow>*</yellow></b> Выберите уровень:'))
    for i, level in enumerate(LEVELS):
        print(HTML(f' <b><magenta>{i})</magenta> {level["visible"]}</b>'))

    level = await prompt_session.prompt_async(HTML('[<blue><b>?</b></blue>]: '),
                                              validator=select_level_validator,
                                              is_password=False)
    level = LEVELS[int(level)]
    print(tip_say(level['description']), style=levels_style)
    while True:
        code = await input_code()
        result = await eval_code(level['name'], code)
        if result.get('error'):
            print(HTML(f'<red>{result["error"]}</red>'))
            continue
        await play_frames(result['texts'])
        print(HTML(f'[<magenta>*</magenta>] Всего шагов: {result["n_steps"]}'))
        if result['result']:
            print(HTML('<lime>Вы победили!</lime>'))
            return
        else:
            print(HTML('<red>Вы проиграли!</red>'))


def main(port=8222):
    # Set up logging.
    logging.basicConfig()
    logging.getLogger().setLevel(logging.DEBUG)

    loop = asyncio.get_event_loop()
    loop.run_until_complete(
        asyncssh.create_server(
            lambda: PromptToolkitSSHServer(interact),
            "0.0.0.0",
            port,
            server_host_keys=["ssh_host_key"],
            passphrase="12345",
        )
    )
    loop.run_forever()


if __name__ == "__main__":
    main(port=22)
