from prompt_toolkit import print_formatted_text, HTML
from prompt_toolkit import PromptSession
from prompt_toolkit.lexers import PygmentsLexer
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.shortcuts import clear
from pygments.lexers.pascal import DelphiLexer

import aio_pika
import asyncio
import environs
import uuid
import json

TIMEOUT = 120
FACE = (
    r"   __",
    r" / * /",
    "/°/ °\\",
    r"\{—} / ",
)

COLORS = {
    'dust': 'gray',
    'player_1': 'lime',
}

env: environs.Env = environs.Env()
RABBITMQ_CONNECTION_URI: str = env.str('RABBITMQ_CONNECTION_URI')


def tip_say(text: str):
    text = [
        list(line)
        for line in (
            " " * 8
            + "<b><white>Ю. Дицкий</white></b>\n"
            + "\n".join(f'{" " * 8}{i}' for i in text.split("\n"))
        ).split("\n")
    ]
    for y, line in enumerate(FACE):
        for x, symbol in enumerate(line):
            if FACE[y][x] == "*":
                text[y - len(text)][x] = "<orange>*</orange>"
            elif FACE[y][x] == "—":
                text[y - len(text)][x] = "<red>—</red>"
            else:
                text[y - len(text)][x] = f"<b><white>{FACE[y][x]}</white></b>"
    return HTML("\n".join("".join(i) for i in text))


class ShizoLexer(DelphiLexer):
    KEYWORDS = {
        'program', 'use',
        'do', 'begin', 'end',
        'while', 'if', 'then'
    }

    BUILTIN = {
        'legs': {'up', 'down', 'left', 'right'}
    }

    def __init__(self, **options):
        super().__init__()
        self.keywords = set()
        self.keywords.update(self.KEYWORDS)
        self.builtins = set()


async def input_code() -> str:
    session = PromptSession()
    completer = WordCompleter(["program", "begin", "use", "do", "then", "if", "end", "while"])
    print_formatted_text(HTML('\n<b>Введите код:</b>'))
    return await session.prompt_async(
        HTML('<lime>.</lime> '), multiline=True, is_password=False,
        prompt_continuation=lambda _, __, ___: HTML('<lime>.</lime> '),
        lexer=PygmentsLexer(ShizoLexer), completer=completer,
        complete_in_thread=True
    )


async def eval_code(mission: str, code: str):
    connection = await aio_pika.connect_robust(RABBITMQ_CONNECTION_URI)
    async with connection:
        channel = await connection.channel()
        response_queue = f'game_result.{uuid.uuid4().hex}'
        queue = await channel.declare_queue(response_queue, auto_delete=True)
        await channel.default_exchange.publish(
            aio_pika.Message(
                body=json.dumps(
                    {
                        'code': code,
                        'level': mission,
                        'response_queue': response_queue
                    }
                ).encode('utf-8')
            ), routing_key='play_mission'
        )

        for i in range(TIMEOUT * 2):
            event = await queue.get(no_ack=True, fail=False)
            if event is not None:
                break
            await asyncio.sleep(0.5)

        data = json.loads(event.body.decode('utf-8'))
    return data


async def play_frames(frames: list):
    for frame in frames:
        clear()
        print_formatted_text(
            HTML('\n'.join(
                ''.join(f'<{color}>{char}</{color}>' for char, color in line) for line in frame
            ))
        )
        await asyncio.sleep(0.5)
