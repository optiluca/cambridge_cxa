import socket
import serial
import lirc
import paho.mqtt.client as mqtt
import json

client_id = 'volume_controller'
mqtt_host = '192.168.1.90'
base_topic = 'media/cxa81/command/#'
volume_topic = 'media/cxa81/command/volume'
command_topic = 'media/cxa81/command/command'

response_topic = 'media/cxa81/response'

def _control_amp(command):
    lirc_client.send_once("CXA81", command)

def _send_command(command):
    print(f"Executing command: {command}")
    
    cmd = f'{command}\r'.encode('utf-8')
    print("Sending command: %s", cmd)

    with serial.Serial('/dev/ttyUSB0', 9600, timeout=2) as ser:
        if ser.inWaiting() > 0:
            ser.flushInput()
        ser.write(cmd)
        ser.flush()
        res = ser.read_until(b'\r')
    res = res.decode()
    print("Got reply: %s", res)
    return {command: res}

def on_connect(client, *args, **kwargs):
    print("on connect: subscribing to base topic...")
    client.subscribe(base_topic)
    print("on connect: subscribed!")

def on_message(client, userdata, message):
    topic = message.topic
    command = str(message.payload.decode("utf-8"))
    print(f"Message received on topic {topic}: {command}")

    if topic == volume_topic:
        _control_amp(command)
    elif topic == command_topic:
        res = _send_command(command)
        client.publish(response_topic, json.dumps(res))

if __name__ == '__main__':
    lirc_client = lirc.Client(connection=lirc.LircdConnection(address="/var/run/lirc/lircd",
                                                          socket=socket.socket(socket.AF_UNIX, socket.SOCK_STREAM),
                                                          timeout = 5.0))
    
    client = mqtt.Client(client_id=client_id)
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(mqtt_host)
    client.loop_forever()
