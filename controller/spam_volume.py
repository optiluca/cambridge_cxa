import time
import paho.mqtt.client as mqtt

client_id = 'volume_spammer'

mqtt_host = '192.168.1.90'
command_topic = f'media/cxa81/command/volume'

if __name__ == '__main__':
    client = mqtt.Client(client_id=client_id)
    client.connect(mqtt_host)

    while True:
        time.sleep(1)
        client.publish(command_topic, 'up')
