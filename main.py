import asyncio
import logging
import os
import traceback

import dotenv

from configuration.config import get_config
from configuration.types import Configuration
from observer.message import Message, MessageLevel
from observer.observer import log_message, observer_loop

LOGGER = logging.getLogger()


async def _health_handler(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
    try:
        data = await reader.read(1024)
        request_line = data.split(b"\r\n", 1)[0]
        ok = request_line.startswith(b"GET /")

        if ok:
            writer.write(b"HTTP/1.1 200 OK\r\nContent-Length: 2\r\n\r\nOK")
        else:
            writer.write(
                b"HTTP/1.1 404 Not Found\r\nContent-Length: 9\r\n\r\nNot Found"
            )
        await writer.drain()
    finally:
        try:
            writer.close()
            await writer.wait_closed()
        except Exception:
            pass


async def _run_health_server() -> asyncio.AbstractServer:
    port = int(os.getenv("PORT", "8080"))
    # host = os.getenv("HOST", "0.0.0.0")
    return await asyncio.start_server(_health_handler, port=port)


async def _main_async(config: Configuration) -> None:
    server = await _run_health_server()
    try:
        await observer_loop(config)
    finally:
        server.close()
        await server.wait_closed()


def main(config: Configuration):
    try:
        asyncio.run(_main_async(config))
    except Exception as e:
        mb = Message.builder().add(network=config.chain_id)
        message = mb.build(
            MessageLevel.CRITICAL,
            (f"observer crashed (traceback in logs) - {e}"),
        )
        log_message(config, message)
        LOGGER.exception(e)
        LOGGER.error(traceback.format_exc())


if __name__ == "__main__":
    dotenv.load_dotenv()
    config = get_config()
    main(config)
