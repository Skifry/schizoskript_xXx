from loguru import logger
from rsinterpreter.interpreter import (
    Lexer,
    Parser,
    LexerError,
    ParserError,
    SemanticAnalyzer,
    SemanticError,
    Error,
)

from rsinterpreter.game import CircusMission, Mission

import pika.exceptions
import multiprocessing
import environs
import typing
import json
import pika

env: environs.Env = environs.Env()
RABBITMQ_CONNECTION_URI: str = env.str("RABBITMQ_CONNECTION_URI")
N_WORKERS: int = env.int("N_WORKERS")
MISSIONS: typing.Dict[str, Mission] = {"circus": CircusMission}


parameters = pika.URLParameters(RABBITMQ_CONNECTION_URI)
while True:
    try:
        connection = pika.BlockingConnection(parameters=parameters)
        break
    except pika.exceptions.AMQPConnectionError:
        continue

channel = connection.channel(0)
task_queue = multiprocessing.Queue()


def event_callback(__, method, _, body):
    decoded_body = json.loads(body)
    task_queue.put_nowait({"data": decoded_body, "delivery_tag": method.delivery_tag})


def consumer():
    channel.queue_declare(queue="play_mission")
    channel.basic_consume(queue="play_mission", on_message_callback=event_callback)
    channel.start_consuming()


def work(event: dict) -> dict:
    code = event["code"]
    lexer = Lexer(code)
    try:
        parser = Parser(lexer)
        tree = parser.parse()
    except (LexerError, ParserError) as e:
        return {"error": e.message}

    mission = MISSIONS.get(event["level"])
    if mission is None:
        return {"error": "Mission not found!"}

    try:
        mission = mission(tree)
    except SemanticError as e:
        return {"error": e.message}

    try:
        result = mission.play()
    except Error as e:
        return {"error": e.message}

    if result["result"]:
        return {"result": 1, "texts": mission.get_text(), "n_steps": mission.n_steps}
    return {"result": 0, "texts": mission.get_text(), "n_steps": mission.n_steps}


def worker():
    while True:
        try:
            event = task_queue.get()
            response = work(event["data"])
            channel.basic_publish(
                "",
                routing_key=event["data"]["response_queue"],
                body=json.dumps(response),
            )
            channel.basic_ack(event["delivery_tag"])
        except Exception as ex:
            logger.exception(ex)


if __name__ == "__main__":
    logger.info(f"Starting {N_WORKERS} workers.")
    for i in range(N_WORKERS):
        multiprocessing.Process(target=worker).start()
    consumer_process = multiprocessing.Process(target=consumer)
    consumer_process.start()
    consumer_process.join()
