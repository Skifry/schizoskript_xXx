from prompt_toolkit import HTML
from . import __version__, __author__

LOGO = HTML(
    r"<b><orange>"
    "\n"
    r" ___  ___  _  _  ____  ____  ____  ____      _  _  _  _  _  _ "
    "\n"
    r"/ __)/ __)( )/ )(  _ \(_  _)(  _ \(_  _)    ( \/ )( \/ )( \/ )"
    "\n"
    r"\__ \\__ \ )  (  )   / _)(_  )___/  )(  ___  )  (  )  (  )  ( "
    "\n"
    r"(___/(___/(_)\_)(_)\_)(____)(__)   (__)(___)(_/\_)(_/\_)(_/\_)"
    "\n"
    f"</orange>\n <magenta>-</magenta> <white>Version</white>: {__version__}\n"
    f" <magenta>-</magenta> <white>Game by</white>: <orange>{__author__}</orange></b>\n\n"
)
