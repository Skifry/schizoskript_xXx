import typing
import random

from colorama import Fore
from pydantic import BaseModel
from .interpreter import (
    Interpreter,
    SemanticAnalyzer,
    Parser,
    Lexer,
    LexerError,
    ParserError,
    SemanticError,
)
from abc import ABC, abstractmethod

colors = {
    "dust": Fore.LIGHTBLACK_EX,
    "player_0": Fore.LIGHTMAGENTA_EX,
    "default": Fore.LIGHTBLACK_EX,
}

PLAYER_POSITION: typing.List[typing.List[int]] = [[0, 0], [1, 1], [0, 1], [1, 0]]


class Tile:
    def __init__(self, game, items: list = None):
        self.game = game
        self.items = items or []

    def on_player_enter(self, player):
        for item in self.items:
            item.trigger(player)

    def get_char(self):
        if not self.items:
            return ".", "dust"
        else:
            return self.items[0].get_char()


class Mission(ABC):
    name: str
    description: str
    game = None

    @abstractmethod
    def check(self):
        raise NotImplemented


class CircusMission(Mission):
    name: str = "Волк слабее робота, но в цирке не выступает"
    description = "Вставить текст вставить текст"

    game = None
    player = None
    n_steps = 0
    step = 0

    player_cords = [
        [0, 0],
        [1, 0],
        [2, 0],
        [2, 1],
        [2, 2],
        [1, 2],
        [0, 2],
        [0, 1],
        [0, 0],
    ]

    def __init__(self, ast):
        build = [LegsModule()]
        semantic_analyzer = SemanticAnalyzer({module.name: module for module in build})
        semantic_analyzer.visit(ast)
        self.player = Player(ast, build=build)
        self.player.init_cords(0, 0)
        self.texts = []
        self.game = RustyScriptInterpreter(players=[self.player], field_size=3)

    def get_text(self):
        return self.texts

    def play(self):
        for step, _ in enumerate(self.game.turn()):
            self.n_steps = step + 1
            if self.check():
                self.texts.append(self.game.get_field())
                break
            if step == 200:
                self.texts.append(self.game.get_field())
                return {"result": 0, "description": "You lose!"}
            if step % 2 == 0:
                self.texts.append(self.game.get_field())
        else:
            return {"result": 0, "description": "You lose!"}
        return {"result": 1, "description": "You win!"}

    def check(self):
        if self.step == 0 and self.player.cords == self.player_cords[self.step]:
            self.step = 1
            return False
        if self.player.cords == self.player_cords[self.step - 1]:
            return False
        elif self.player.cords == self.player_cords[self.step]:
            self.step += 1
        else:
            self.step = 0
        if self.step == 9:
            return True


class BasicParams(BaseModel):
    health: int
    cpu: int
    weigh: int


class RobotModule(ABC):
    func: typing.Dict[str, typing.Callable]
    other: typing.Dict[str, dict]
    basic_params: BasicParams
    name: str

    def __init__(self):
        self.func, self.other = self.build_func()
        self.player = None

    def init_player(self, player):
        self.player = player

    @abstractmethod
    def build_func(self):
        raise NotImplemented


class Debug(RobotModule):
    name: str = "debug"
    basic_params: BasicParams = BasicParams(health=0, cpu=0, weigh=1)

    def build_func(self):
        return {"writeln": self.writeln}, {"writeln": {"n_params": -1}}

    @staticmethod
    def writeln(*args):
        print(*args)
        yield from range(1)


class LegsModule(RobotModule):
    name: str = "legs"
    basic_params = BasicParams(health=0, cpu=0, weigh=1)

    def build_func(self):
        return (
            {
                "up": self.go_up,
                "down": self.go_down,
                "left": self.go_left,
                "right": self.go_right,
            },
            {
                "up": {"n_params": 0},
                "down": {"n_params": 0},
                "left": {"n_params": 0},
                "right": {"n_params": 0},
            },
        )

    def go_up(self):
        if self.player.cords[1] - 1 >= 0 and self.player.game.is_empty(
            self.player.cords[0], self.player.cords[1] - 1
        ):
            self.dust()
            self.player.cords[1] -= 1
            yield from range(2)
            return 1
        yield
        return 0

    def go_down(self):
        if self.player.cords[
            1
        ] + 1 < self.player.game.field_size and self.player.game.is_empty(
            self.player.cords[0], self.player.cords[1] + 1
        ):
            self.dust()
            self.player.cords[1] += 1
            yield from range(2)
            return 1
        yield
        return 0

    def go_left(self):
        if self.player.cords[0] - 1 >= 0 and self.player.game.is_empty(
            self.player.cords[0] - 1, self.player.cords[1]
        ):
            self.dust()
            self.player.cords[0] -= 1
            yield from range(2)
            return 1
        yield
        return 0

    def go_right(self):
        if self.player.cords[
            0
        ] + 1 < self.player.game.field_size and self.player.game.is_empty(
            self.player.cords[0] + 1, self.player.cords[1]
        ):
            self.dust()
            self.player.cords[0] += 1
            yield from range(2)
            return 1
        yield
        return 0

    def dust(self):
        if random.randint(0, 3) != 0:
            particle = random.choice("%")
            self.player.game.add_particle(*self.player.cords, (particle, "dust"))


class Player:
    def __init__(self, ast, build: typing.List[RobotModule]):
        self.cords = None
        self.timeout = 0
        self.scope = {}
        self.game = None
        for module in build:
            module.init_player(self)

        self.build = {module.name: module for module in build}
        self.interpreter = Interpreter(ast, modules=self.build).interpret()

    def init_cords(self, x, y):
        self.cords = [x, y]

    @staticmethod
    def get_char():
        return "@"

    def init_game(self, game):
        self.game = game


class RustyScriptInterpreter:
    def __init__(
        self,
        players: typing.List[Player],
        field_size: int = 7,
        field: typing.List[typing.List[Tile]] = None,
        step_per_turn: int = 10,
    ):
        self.step_per_turn = step_per_turn
        self.field = field or [
            [Tile(self) for __ in range(field_size)] for _ in range(field_size)
        ]
        self.particles = [[None for __ in range(field_size)] for _ in range(field_size)]
        self.players = players
        self.field_size = field_size
        for player in players:
            player.init_game(self)

    def get_field(self):
        field = [["." for _ in range(self.field_size)] for _ in range(self.field_size)]
        for x in range(self.field_size):
            for y in range(self.field_size):
                field[y][x] = self.field[y][x].get_char()

        for i, player in enumerate(self.players):
            xy = player.cords
            field[xy[1]][xy[0]] = (player.get_char(), f"player_{i}")

        for y in range(self.field_size):
            for x in range(self.field_size):
                if self.particles[x][y] is not None:
                    field[y][x] = self.particles[x][y]
                    self.particles[x][y] = None

        return field

    def turn(self):
        playable = set(self.players)
        while len(playable) != 0:
            for player in self.players:
                for step in range(self.step_per_turn):
                    try:
                        yield next(player.interpreter)
                    except StopIteration:
                        playable.remove(player)
                        break
                    if step == 10:
                        break

    def add_particle(self, x, y, particle):
        if x < 0 or x >= self.field_size or y < 0 or y >= self.field_size:
            return
        self.particles[x][y] = particle

    def is_empty(self, x, y):
        for player in self.players:
            if player.cords == (x, y):
                return False
        return True

    def trigger_move(self):
        for player in self.players:
            xy = player.cords
            self.field[xy[0]][xy[1]].on_player_enter(player)


if __name__ == "__main__":
    text = open("prog.pas").read()

    lexer = Lexer(text)
    try:
        parser = Parser(lexer)
        tree = parser.parse()
    except (LexerError, ParserError) as e:
        print(e.message)
        exit(1)

    modules = [LegsModule()]
    semantic_analyzer = SemanticAnalyzer({module.name: module for module in modules})
    try:
        semantic_analyzer.visit(tree)
    except SemanticError as e:
        print(e.message)
        exit(1)

    result = CircusMission(tree).play()
    if result["result"]:
        print(Fore.LIGHTGREEN_EX + result["description"] + Fore.RESET)
    else:
        print(Fore.LIGHTRED_EX + result["description"] + Fore.RESET)
