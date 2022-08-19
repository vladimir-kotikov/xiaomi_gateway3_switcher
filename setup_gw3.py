#!/usr/bin/env python

import asyncio
import sys

from aiohttp.client import ClientSession
from homeassistant import (
    config_entries,
)  # unused but is required to load homeassistant first to avoid circular imports issue
from xiaomi_gateway3.core import shell
from xiaomi_gateway3.core.gateway import XGateway

from xiaomi_gateway3.core.xiaomi_cloud import MiCloud
from xiaomi_gateway3.core.utils import (
    NCP_URL,
    flash_zigbee_firmware,
    check_gateway,
)

import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


POST_1_46_TELNET_CMD = r'{"method":"set_ip_info","params":{"ssid":"\"\"","pswd":"123123 ; passwd -d admin ; echo enable > /sys/class/tty/tty/enable; telnetd"}}'


async def flash_custom_zigbee_firmware(host: str):
    """Update zigbee firmware for both ZHA and zigbee2mqtt modes"""

    try:
        async with shell.Session(host) as session:
            sh = await session.login()
            assert await sh.run_zigbee_flash()
    except Exception as e:
        logger.error("Can't update zigbee firmware", exc_info=e)
        return False

    await asyncio.sleep(0.5)

    args = [
        host,
        [8115, 8038],
        NCP_URL % "mgl03_ncp_6_7_10_b38400_sw.gbl",
        "v6.7.10",
        8038,
    ]

    for _ in range(3):
        if await asyncio.get_event_loop().run_in_executor(
            None, flash_zigbee_firmware, *args
        ):
            return True
    return False


def first(coll):
    try:
        return next(iter(coll))
    except StopIteration:
        return None


async def main(user: str, password: str, device_model: str = "lumi.gateway.mgl03"):
    async with ClientSession() as session:
        cloud = MiCloud(session, servers=["cn"])
        success = await cloud.login(user, password)
        if not success:
            sys.exit("Failed to authenticate in MiCloud")

        devices = await cloud.get_devices()
        gateway_device = first(d for d in devices if d["model"] == device_model)
        if gateway_device is None:
            sys.exit("Couldn't find gateway device")

        gateway_host = gateway_device["localip"]
        error = await check_gateway(
            gateway_host,
            gateway_device["token"],
            telnet_cmd=POST_1_46_TELNET_CMD,
        )
        if not error:
            print("Gateway ok")
        else:
            sys.exit("Can't connect to gateway: " + error)

        success = await flash_custom_zigbee_firmware(gateway_host)
        if not success:
            sys.exit("Can't flash zigbee firmware")

        gateway = XGateway(
            gateway_host,
            gateway_device["token"],
            debug="true",
            ble=False,
            zha=True,
            telnet_cmd=POST_1_46_TELNET_CMD,
        )

        if not await gateway.prepare_gateway():
            sys.exit("Can't prepare gateway")


if __name__ == "__main__":
    from argparse import ArgumentParser

    parser = ArgumentParser()
    parser.add_argument("-u", "--user", dest="user", help="MiCloud user", required=True)
    parser.add_argument(
        "-p", "--password", dest="password", help="MiCloud password", required=True
    )
    parser.add_argument(
        "-d",
        "--device",
        dest="device_model",
        help="Gateway device model",
        default="lumi.gateway.mgl03",
    )
    args = parser.parse_args()

    asyncio.run(main(args.user, args.password, device_model=args.device_model))
