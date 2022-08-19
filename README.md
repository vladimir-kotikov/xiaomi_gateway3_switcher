# Xiaomi Gateway3 mode switcher

A script to flash Xiaomi Gateway3 and switch between ZHA and Zigbee2MQTT modes
without Home Assistant.

The script will flash the gateway if needed and then switch to the new mode.

## ZHA mode

This is the only mode that is currently supported. Once switched, the gateway's
Zigbee Chip will be available via TCP socket at `socket://<gateway_ip_address>:8888`

See more details [here](https://github.com/AlexxIT/XiaomiGateway3#zigbee-home-automation-mode)
