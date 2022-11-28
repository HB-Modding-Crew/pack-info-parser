import logging

logging.basicConfig(filename=f'logs.log', encoding='utf-8', level=logging.DEBUG)

logging_commands = {
    "error": logging.error,
    "warning": logging.warning,
    "info": logging.info,
    "debug": logging.debug
}

# Explicit display
def display(message, level="info"):
    print(message, flush=True)
    log(message, level)

# Implicit display
def log(message, level="info"):
    logging_commands[level](message)
    