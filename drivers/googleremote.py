# This file is part of multiRemote.
#
# multiRemote is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 2 of the License, or
# (at your option) any later version.
#
# multiRemote is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with multiRemote.  If not, see <http://www.gnu.org/licenses/>.
#
"""
nVidia Shield driver

Uses a persistant ADB shell connection to issue input events as well
as managing what app to run.

Does not support power functions, but will automatically navigate home
when getting power off (to avoid streaming stuff when noone is watching)

This is the first driver to support the driver-extras directive. This
information is provided by the applyExtras() API call and is called
whenever a device selected. Meaning you may get setPower() once but
applyExtras() multiple times if you have plenty of shield scenes.

The information in driver-extras should be:
  app=<name of app>

This will cause the driver to automatically start the correct app
when user activates the scene.

App should be the package name you want to launch, use the pm command
in adb shell to find what packages you have.

Acknowledgements:
The code to successfully pair and communicate with a Google TV device
was inspired by the following resources:
- https://github.com/Aymkdn/assistant-freebox-cloud/wiki/Google-TV-(aka-Android-TV)-Remote-Control-(v2)
- https://github.com/laxathom/google-tv-pairing-protocol

"""

if __name__ != "__main__":
  from .base import driverBase
  from modules.commandtype import CommandType
else:
  # Prototype classes
  class driverBase:
      def __init__(self):
          pass
        
    
import logging
import subprocess
import time
import select
import fcntl
import os

import ssl
import socket
import json
import struct
import string
import time
import os
import argparse
import logging
import select
import queue

from cryptography import x509
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.serialization import load_pem_public_key
import binascii
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.serialization import Encoding, PrivateFormat, NoEncryption
from datetime import datetime, timedelta
import threading

# Extended dictionary mapping tags to their meanings
class Tag:
    class TagValue:
        def __init__(self, number, description, length=None):
            self.number = number
            self.description = description
            self.length = length

        def toInt(self):
            return self.number

        def toString(self):
            return self.description

    PROTOCOL_VERSION = TagValue(8, "Protocol Version Tag", length=1)
    STATUS_CODE = TagValue(16, "Status Code Tag", length=2)
    PAIRING_MESSAGE = TagValue(82, "Pairing Message Tag")
    SERVICE_NAME = TagValue(10, "Service Name Tag")
    DEVICE_NAME = TagValue(18, "Device Name Tag")
    OPTION_MESSAGE = TagValue(162, "Option Message Tag")
    CONFIGURATION_MESSAGE = TagValue(242, "Configuration Message Tag")
    ENCODED_SECRET = TagValue(194, "Encoded Secret Tag", length=5)
    COMMAND_MESSAGE = TagValue(82, "Command Message Tag")
    LAUNCH_APPLICATION_COMMAND = TagValue(210, "Launch Application Command Tag")
    PING_MESSAGE = TagValue(66, "Ping Message Tag")
    PONG_RESPONSE = TagValue(74, "Pong Response Tag")
    DEVICE_INFO = TagValue(146, "Device Info Tag?")

    # Add a dictionary to map tag numbers to tag tuples
    _tag_map = {value[0]: value for key, value in vars().items() if isinstance(value, tuple) and isinstance(value[0], int)}

    @classmethod
    def from_number(cls, number):
        for tag_value in vars(cls).values():
            if isinstance(tag_value, cls.TagValue) and tag_value.number == number:
                return tag_value
        return cls.TagValue(number, f"Unknown Tag ({number})")

class GoogleRemote:
    def __init__(self, server):
        self.server = server
        self.ssock = None
        self.sock = None
        self.cert = 'client.pem'
        self.queue = queue.Queue()

        # Ensure we have a certificate
        if not os.path.exists(self.cert):
            self.generate_cert(self.cert)

    def generate_cert(self, filename):

        # Distinguished Name details
        dn = x509.Name([
            x509.NameAttribute(NameOID.COMMON_NAME, "atvremote"),
            x509.NameAttribute(NameOID.COUNTRY_NAME, "US"),
            x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "California"),
            x509.NameAttribute(NameOID.LOCALITY_NAME, "Montain View"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Google Inc."),
            x509.NameAttribute(NameOID.ORGANIZATIONAL_UNIT_NAME, "Android"),
            x509.NameAttribute(NameOID.EMAIL_ADDRESS, "example@google.com")
        ])

        # Generate private key
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
        )

        # Self-signed certificate
        certificate = x509.CertificateBuilder().subject_name(
            dn
        ).issuer_name(
            dn
        ).public_key(
            private_key.public_key()
        ).serial_number(
            x509.random_serial_number()
        ).not_valid_before(
            datetime.utcnow()
        ).not_valid_after(
            # Certificate valid for 10 years
            datetime.utcnow() + timedelta(days=3650)
        ).sign(private_key, hashes.SHA256())

        # Export public key (certificate)
        cert_pem = certificate.public_bytes(Encoding.PEM)

        # Export private key
        key_pem = private_key.private_bytes(
            Encoding.PEM,
            PrivateFormat.TraditionalOpenSSL,
            NoEncryption()
        )

        with open('client.pem', 'wb') as file:
            file.write(cert_pem)
            file.write(key_pem)


    def encode_secret(self, server_cert, secret):
        # Load the client's certificate
        with open('client.pem', 'rb') as file:
            client_cert = x509.load_pem_x509_certificate(file.read(), default_backend())
        client_pub_key = client_cert.public_key()

        server_pub_key = server_cert.public_key()

        # Extracting modulus and exponent from RSA public keys
        client_rsa_key = client_pub_key.public_numbers()
        client_modulus = client_rsa_key.n
        client_exponent = client_rsa_key.e

        server_rsa_key = server_pub_key.public_numbers()
        server_modulus = server_rsa_key.n
        server_exponent = server_rsa_key.e

        # Hashing using SHA-256
        digest = hashes.Hash(hashes.SHA256(), backend=default_backend())
        digest.update(client_modulus.to_bytes((client_modulus.bit_length() + 7) // 8, byteorder='big'))
        digest.update(client_exponent.to_bytes((client_exponent.bit_length() + 7) // 8, byteorder='big'))
        digest.update(server_modulus.to_bytes((server_modulus.bit_length() + 7) // 8, byteorder='big'))
        digest.update(server_exponent.to_bytes((server_exponent.bit_length() + 7) // 8, byteorder='big'))

        # Assuming `code` is the variable containing the code from the server
        code_bin = binascii.unhexlify(secret[2:6])
        digest.update(code_bin)
        alpha = digest.finalize()

        # Convert alpha to an array of bytes for the payload
        alpha_hex = binascii.hexlify(alpha)
        payload = [int(alpha_hex[i:i+2], 16) for i in range(0, len(alpha_hex), 2)]
        return payload

    def parse_message(self, message: bytearray):
        i = 0
        parsed_message = {}

        while i < len(message):
            tag_number = message[i]
            tag = Tag.from_number(tag_number)
            i += 1

            length = tag.length if tag.length is not None else message[i]
            i += 1 if tag.length is None else 0

            data = message[i:i+length]
            i += length

            parsed_message[tag.toInt()] = data

        return parsed_message

    def recvall(self, sock, n):
        data = bytearray()
        while len(data) < n:
            packet = sock.recv(n - len(data))
            if not packet:
                raise ValueError("Socket connection closed prematurely")
            data.extend(packet)
        return data

    def send_message(self,  message):
        # Automatically prefix length
        fullmsg = len(message).to_bytes(1, byteorder='big')+message
        total_sent = 0
        while total_sent < len(fullmsg):
            sent = self.ssock.send(fullmsg[total_sent:])
            if sent == 0:
                raise RuntimeError("Socket connection broken")
            total_sent += sent

    def receive_message(self):
        """
        Receives a message from the server using the specified protocol.

        Returns:
        tuple: A tuple containing the status code and the payload of the message.
        """

        # Read the payload size (assuming it is 1 byte; adjust if it's more)
        size_data = self.recvall(self.ssock, 1)
        if size_data is None:
            raise ConnectionError("Failed to read payload size from socket.")

        payload_size = int.from_bytes(size_data, byteorder='big', signed=False)

        # Read the payload based on the received size
        payload = self.recvall(self.ssock, payload_size)
        if payload is None:
            raise ConnectionError("Failed to read payload from socket.")

        return payload

    def cmd_pair_remote(self, service_name: str, device_name: str):
        """
        Pairs a remote with the server using the specified protocol.

        Args:
        self.ssock (socket.socket): The socket object used for communication.
        service_name (str): The name of the service to pair with.
        device_name (str): The name of the device initiating the pairing.

        Returns:
        bool: True if pairing is successful, False otherwise.
        """

        # Convert service and device names to bytes
        service_bytes = service_name.encode()
        device_bytes = device_name.encode()

        logging.info('Sending pariring message')

        # Construct the pairing message payload
        payload = bytearray([
            Tag.PROTOCOL_VERSION.toInt(), 2,  # Protocol version
            Tag.STATUS_CODE.toInt(), 200, 1,  # Status code OK
            Tag.PAIRING_MESSAGE.toInt(),  # Message tag for pairing
            len(service_bytes) + len(device_bytes) + 6,  # Length of the message
            Tag.SERVICE_NAME.toInt(), len(service_bytes), *service_bytes,  # Service name
            Tag.DEVICE_NAME.toInt(), len(device_bytes), *device_bytes  # Device name
        ])

        # Send payload size followed by the payload
        self.send_message(payload)

    def cmd_send_option(self):
        logging.info('Sending option message')
        payload = bytearray([
            Tag.PROTOCOL_VERSION.toInt(), 2,
            Tag.STATUS_CODE.toInt(), 200, 1,
            Tag.OPTION_MESSAGE.toInt(),
            1, # No idea
            8, # Size? Would make sense (Henric)
            10, #??
            4, # ??
            8, # Tag type??
            3, #  encoding type (0 for ENCODING_TYPE_UNKNOWN, 1 for ENCODING_TYPE_ALPHANUMERIC, 2 for ENCODING_TYPE_NUMERIC, 3 for ENCODING_TYPE_HEXADECIMAL, 4 for ENCODING_TYPE_QRCODE)
            16, # Size tag? (not likely)
            6, # Symbol length? Not likely
            24, # Preferred role tag (possibly)
            1 # Preferred role (1 = ROLE_TYPE_INPUT)
        ])
        # Send payload size followed by the payload
        self.send_message(payload)

    def cmd_send_config(self):
        logging.info('Sending config message')
        payload = bytearray([
            Tag.PROTOCOL_VERSION.toInt(), 2,
            Tag.STATUS_CODE.toInt(), 200, 1,
            Tag.CONFIGURATION_MESSAGE.toInt(),
            1, # No idea
            8, # Size? Would make sense (Henric)
            10, #??
            4, # ??
            8, # Tag type??
            3, #  encoding type (0 for ENCODING_TYPE_UNKNOWN, 1 for ENCODING_TYPE_ALPHANUMERIC, 2 for ENCODING_TYPE_NUMERIC, 3 for ENCODING_TYPE_HEXADECIMAL, 4 for ENCODING_TYPE_QRCODE)
            16, # Size tag? (not likely)
            6, # Symbol length? Not likely
            16, # Preferred role tag (possibly)
            1 # Preferred role (1 = ROLE_TYPE_INPUT, 2 = ROLE_TYPE_DISPLAY)
        ])
        self.send_message(payload)

    def cmd_send_secret(self, secret):
        logging.info('Sending secret')
        server_cert_bin = self.ssock.getpeercert(binary_form=True)
        server_cert = x509.load_der_x509_certificate(server_cert_bin, default_backend())
        secret = self.encode_secret(server_cert, secret)

        payload = bytearray([
            Tag.PROTOCOL_VERSION.toInt(), 2,
            Tag.STATUS_CODE.toInt(), 200, 1,
            Tag.ENCODED_SECRET.toInt(),
            2, # Size?
            34, # ?
            10, # ?
            len(secret),
            *secret
        ])
        self.send_message(payload)

    def cmd_start_application(self, intent):
        logging.info(f'Start application {intent}')
        payload = bytearray([
            Tag.LAUNCH_APPLICATION_COMMAND.toInt(), 5,
            2+len(intent), # Size of all to come
            10, # Tag
            len(intent),
            *(intent.encode())
        ])
        self.send_message(payload)

    def cmd_send_app_info(self):
        logging.info(f'Sending app info')

        tags = bytearray([
            1, 49,
            42, 11, *('multiremote'.encode()),
            50, 5, *('1.0.0'.encode())
        ])

        payload = bytearray([
            10, len(tags) + 8,
            8, 238, 4, 18,
            len(tags) + 3,
            24, 1, 34,
            *tags
        ])
        #logging.info("\n".join(str(e) for e in payload))
        self.send_message(payload)

    def cmd_send_ack(self):
        logging.info(f'Sending ack')

        payload = bytearray([
            18, 3, 8, 238, 4
        ])
        self.send_message(payload)

    def cmd_send_key(self, keycode):
        logging.info(f'Sending keycode {keycode}')

        payload = bytearray([
            82, 4, 8, keycode, 16, 3
        ])
        self.send_message(payload)

    def print_result(self, result):
        for k,v in result.items():
            logging.debug(f'{Tag.from_number(k).toString()} ({k}): {", ".join(str(e) for e in v)}')

    def print_payload(self, payload):
        # This assumes that all data is in the format of:
        # 1 byte = tag
        # 1 byte = length
        # n bytes = data
        i = 0
        print(f'Payload size {len(payload)}:')
        try:
            while i < len(payload):
                tag = payload[i]
                i += 1
                length = payload[i]
                i += 1
                data = payload[i:i+length]
                i += length
                logging.debug(f'Tag {tag}, length {length}, data:')
                self.print_hex(data)
        except Exception as e:
            logging.error(f"Failed to parse payload: {e}")

    def print_hex(self, byte_array):
        hex_values = [f'{b:02x}' for b in byte_array]
        printable_chars = ['.' if chr(b) not in string.printable or chr(b) in string.whitespace else chr(b) for b in byte_array]

        for i in range(0, len(hex_values), 8):
            hex_row = ' '.join(hex_values[i:i+8])
            char_row = ''.join(printable_chars[i:i+8])
            logging.debug(f'{hex_row}  {char_row}')

    def pair(self):
        self.ssock = self.create_ssl_connection(self.server, 6467)
        if self.ssock is not None:
            self.state_machine(0)
            self.ssock.close()

    def control_start(self):
        # Create a new thread that runs the state machine
        self.thread = threading.Thread(target=self.run_state_machine , args=(5,))
        self.thread.start()

    def control_stop(self):
        if self.thread is None:
            return
        
        self.queue.put({'cmd':'exit'})

        # Wait for the thread to finish
        self.thread.join()
        self.ssock.close()
        self.thread = None
        self.ssock = None

    def run_state_machine(self, state):
        restart = True
        retries = 0
        while restart:
          try:
            self.ssock = self.create_ssl_connection(self.server, 6466)
            if self.ssock is not None:
              witherror = self.state_machine(state)
              if witherror:
                  logging.error('Statemachine ended with error, retry connection')
                  restart = True
              else:
                  logging.debug('State machine ended')
                  restart = False
                  retries = 0
            else:
              logging.error('No socket connection')
              restart = True
          except Exception as e:
            logging.exception(f"Failed to run state machine")
            restart = True
          if restart:
            retries += 1
            if retries > 10:
              logging.error('Maximum retry attempts reached, sleeping 5min')
              time.sleep(300)
              retries = 1
            logging.info(f'Restarting connection, attempt {retries}')
            time.sleep(0.1 * retries) # 100ms delay
        logging.error('Statemachine is no longer running')

    def create_ssl_connection(self, host, port, state=0):
        # Step 1: Create SSL context
        ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)

        # Step 2: Load client certificate and key
        ssl_context.load_cert_chain(certfile=self.cert, keyfile=self.cert)

        ssl_context.check_hostname = False

        # Step 3: Disable server certificate verification (for self-signed certs)
        ssl_context.verify_mode = ssl.CERT_NONE

        # Step 4: Create a socket and connect to server
        ssock = None
        sock = socket.create_connection((host, port))
        if sock is not None:
            ssock = ssl_context.wrap_socket(sock, server_hostname=host)
        return ssock
        
    def state_machine(self, state):
        running = True
        should_restart = False
        while running:
            expect_status = True
            waitfor = None
            if state == 0:
                self.cmd_pair_remote('multiremote', 'multiremote')
            elif state == 1:
                self.cmd_send_option()
            elif state == 2:
                self.cmd_send_config()
            elif state == 3:
                secret = ''
                while len(secret) != 6:
                    secret = input('Please enter the six digit code shown on the display: ')
                self.cmd_send_secret(secret)
            elif state == 4:
                logging.info('Remote has paired')
                break
                
            elif state == 5:
                expect_status = False
                pass # Let's get the info from chromecast
            elif state == 6:
                self.cmd_send_app_info()
                expect_status = False
                waitfor = 18
            elif state == 7:
                self.cmd_send_ack()
                waitfor = [194, 162, 146]
                expect_status = False
            elif state == 8:
                logging.info('Statemachine is ready for input')
                state = 9
            elif state == 9:
                # Check if the queue has any commands
                if not self.queue.empty():
                    command = self.queue.get()
                    try:
                      if command['cmd'] == 'keyinput':
                          self.cmd_send_key(command['value'])
                          if command['callback'] is not None:
                              command['callback'](command.get('args', None))
                      elif command['cmd'] == 'exit':
                          running = False
                          break
                      elif command['cmd'] == 'launch_app':
                          self.cmd_start_application(command['value'])
                    except e:
                        logging.exception(f"Failed to execute command {command}")

                expect_status = False
            else:
                logging.info("State machine done")
                break

            # This loop is HORRIBLE, need to refactor later
            atleastonce = True
            nodata = True
            while waitfor is not None or atleastonce:
                #logging.debug(f'Reading message for state {state} (waitfor = {waitfor}, atleastonce = {atleastonce})')
                atleastonce = False
                # if state is 9, we don't wait for a response
                if state == 9:
                    # See if there's data, otherwise continue
                    ready_to_read, _, _ = select.select([self.ssock], [], [], 0.05)
                    if not ready_to_read:
                        break

                nodata = False
                payload = self.receive_message()
                #logging.debug(f'Payload received ({len(payload)}):\n  {", ".join(str(e) for e in payload)}')
                #self.print_hex(payload)
                result = self.parse_message(payload)
                # Handle unsolicited messages
                if payload[0] == Tag.PING_MESSAGE.toInt():
                    #print('Received ping message, responding with pong')
                    payload = bytearray([
                        Tag.PONG_RESPONSE.toInt(),
                        2, 8, 25
                    ])
                    self.send_message(payload)
                elif payload[0] == Tag.OPTION_MESSAGE.toInt():
                    logging.debug('Received option message')
                    # Don't know what the first 6 are, but the 7th byte is the size of the message
                    logging.debug(f'Running package is: {payload[7:].decode()}')
                elif payload[0] == Tag.ENCODED_SECRET.toInt():
                    logging.debug('Received information about the state of the player')
                    # Again, we have NO CLUE really, except byte 5 indicates on/off (1/0)
                    if payload[4] == 0:
                        logging.info('Player is off')
                        self.cmd_send_key(23) # Power on? Sort of? Select key on the dpad
                        # SWALLOW THIS MESSAGE
                        continue
                    else:
                        logging.info('Player is on')
                elif payload[0] == Tag.DEVICE_INFO.toInt():
                    logging.debug(f'Received device info(?) tag')
                    self.print_payload(payload)

                if waitfor is not None:
                    if isinstance(waitfor, list):
                        if payload[0] in waitfor:
                            #print('Get the expected message, continuing')
                            waitfor.remove(payload[0])
                            if not waitfor:
                                #print('All expected messages received, continuing')
                                waitfor = None
                    elif payload[0] == waitfor:
                        #print('Get the expected message, continuing')
                        waitfor = None
            #logging.debug(f'Payload read for state {state}')

            if nodata:
                #logging.error('No data received')
                time.sleep(0.05) # Wait 50ms
                # Ideally, we have a loop which waits on either data from the socket or from
                # the remote itself. We should not be busy waiting like this.
            else:
                if Tag.STATUS_CODE.toInt() not in result and expect_status:
                    logging.warning('No result')
                    #running = False
                elif expect_status:
                    status_code = result[Tag.STATUS_CODE.toInt()][0]
                    if status_code != 200: # 144,3 = Error, 143,3 = Bad Configuration
                        logging.error(f'Command failed, code {status_code}, payload size is {len(payload)}')
                        self.print_hex(payload)
                        self.print_payload(payload)
                        running = False
                        shouldrestart = True
                    else:
                        self.print_result(result)
                        state += 1
                else:
                    state += 1
                if state > 9:
                    # Keep statemachine running
                    state = 9
        return shouldrestart

    def launch_app(self, app):
        self.queue.put({'cmd':'launch_app', 'value':app}) 

    def send_keyinput(self, direction, callback=None, cbArgs=None):
      map = {
        'up': 19,
        'down': 20,
        'left': 21,
        'right': 22,
        'center': 23,
        'back': 4,
        'home': 3,
        'menu': 82,
        'search': 84,
        'play_pause': 85,
        'rewind': 89,
        'fast_forward': 90,
        'volume_up': 24,
        'volume_down': 25,
        'volume_mute': 164,
        'power': 26,
        'notifications': 83,
        'quick_settings': 95,
        'recent_apps': 187,
        'enter': 66,
        'delete': 67,
        'escape': 111,
        'tab': 61,
        'space': 62,
        'page_up': 92,
        'page_down': 93,
        'move_home': 122,
        'move_end': 123,
        'media_play': 126,
        'media_pause': 127,
        'media_play_pause': 85,
        'media_stop': 86,
        'media_next': 87,
        'media_previous': 88,
        'media_rewind': 89,
        'media_fast_forward': 90,
        'media_record': 130,
        'media_close': 128,
        'media_eject': 129,
        'media_audio_track': 222,
        'media_audio_next': 87,
        'media_audio_previous': 88,
        'media_audio_forward': 90,
        'media_audio_rewind': 89,
        'media_audio_repeat': 127,
        'media_audio_shuffle': 126,
        'media_audio_play': 85,
        'media_audio_pause': 85,
        'media_audio_play_pause': 85,
        'media_audio_stop': 86,
        'media_audio_rewind': 89,
        'media_audio_fast_forward': 90,
        'media_audio_record': 130,
        'media_audio_close': 128,
        'media_audio_eject': 129,
        'media_audio_track': 222,
        'media_audio_repeat': 127,
        'media_audio_shuffle': 126,
        'media_video_next': 87,
        'media_video_previous': 88
      }

      if direction not in map:
        logging.error(f"Invalid direction: {direction}")
        return

      self.queue.put({'cmd':'keyinput', 'value':map[direction], 'callback':callback, 'args':cbArgs})

class driverGoogleremote(driverBase):
  def init(self, server):

    self.server = server
    self.adb = None

    self.addCommand("up",     CommandType.NAVIGATE_UP,      self.navUp)
    self.addCommand("down",   CommandType.NAVIGATE_DOWN,    self.navDown)
    self.addCommand("left",   CommandType.NAVIGATE_LEFT,    self.navLeft)
    self.addCommand("right",  CommandType.NAVIGATE_RIGHT,   self.navRight)
    self.addCommand("select", CommandType.NAVIGATE_ENTER,   self.navEnter)
    self.addCommand("back",   CommandType.NAVIGATE_BACK,    self.navBack)

    #self.addCommand("info",     CommandType.PLAYBACK_OSD,           self.playbackInfo)
    self.addCommand("play",     CommandType.PLAYBACK_PLAYPAUSE,     self.playbackPlay)
    self.addCommand("rewind",   CommandType.PLAYBACK_REWIND,        self.playbackRW)
    self.addCommand("forward",  CommandType.PLAYBACK_FASTFORWARD,   self.playbackFF)

    #self.addCommand("text",     CommandType.NAVIGATE_TEXTINPUT,     self.navTextInput, None, None, None, 1)
    self.remote = GoogleRemote(self.server)
    self.remote.control_start()
    self.setup_adb()

  def setup_adb(self):
    # First, flush any running adb process
    logging.debug("Killing any running ADB server")
    try:
      subprocess.run(['adb', 'kill-server'])
    except subprocess.CalledProcessError as e:
      logging.error(f"Failed to kill ADB server: {e}")
      return False
    
    # Then connect to the device
    logging.debug(f"Connecting to ADB device at {self.server}")
    connect_process = subprocess.run(['adb', 'connect', f'{self.server}:5555'], capture_output=True, text=True)
    
    if 'connected to' not in connect_process.stdout:
      logging.error("Failed to connect to ADB device: %s", connect_process.stdout)
      return False

    logging.debug("Starting ADB shell session...")
    self.adb = subprocess.Popen(['adb', 'shell'], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    # Ensure we are connected
    if self.adb is not None and self.adb.poll() is not None:
      logging.error("Failed to start ADB shell")
      self.adb = None
      return False
    logging.debug("ADB shell session started")

    # Set stdout to non-blocking
    flags = fcntl.fcntl(self.adb.stdout, fcntl.F_GETFL)
    fcntl.fcntl(self.adb.stdout, fcntl.F_SETFL, flags | os.O_NONBLOCK)
    return True

  def exec_command(self, command, ignore_result=False):
    if self.adb is None:
      logging.error("ADB shell not started, trying to start")
      if not self.setup_adb():
        logging.error("Failed to start ADB shell")
        return None
      
    # Let's see if the ADB instance works still
    try:
      self.adb.stdin.write('\n')
      self.adb.stdin.flush()
    except BrokenPipeError:
      logging.error("ADB shell connection broken, trying to restart")
      if not self.setup_adb():
        logging.error("Failed to start ADB shell")
        return None

    try:
      logging.debug(f"Executing command: {command}")
      self.adb.stdin.write(command + '\n')
      self.adb.stdin.flush()
      if ignore_result:
        return None
      logging.debug(f"Waiting for result")
      output = ''
      while select.select([self.adb.stdout], [], [], 0.1)[0]:
        logging.debug(f"Reading output")
        while True:
          try:
            chunk = self.adb.stdout.read(1024)
            if not chunk:
              break
            output += chunk
          except IOError:
            break
        logging.debug(f"Command: {command} -> Output: {output}")
        return output
    except Exception as e:
      logging.exception(f"Failed to execute command: {command}. Error: {e}")
    return None

  def launch_app(self, package_name, ambiguous=False):
    if ambiguous:
      result = self.exec_command(f'pm resolve-activity -a android.intent.action.MAIN --brief {package_name}')
    else:
      result = self.exec_command(f'pm resolve-activity -a android.intent.action.MAIN -c android.intent.category.LAUNCHER --brief {package_name}')
    if result is None:
      logging.warning(f"Failed to resolve activity for package {package_name}, trying more ambitious approach")
      return
    found = False
    intent = None
    for line in result.splitlines():
      if line.startswith('priority=0'):
        found = True
        continue
      if found:
        intent = line
        break
    if intent is None:
      logging.error(f"Failed to find intent for package {package_name}")
      if not ambiguous:
        logging.warning("Trying more ambitious approach")
        self.launch_app(package_name, True)
      return

    # First, make sure it's not running        
    #self.exec_command(f'am force-stop {package_name}')
    # Then launch it
    self.exec_command(f'am start -S -a android.intent.action.MAIN -n {intent}')

  def eventOn(self):
    logging.debug('Power on, send home button')
    # Let's not, assume it's always running
    event = threading.Event()
    self.remote.send_keyinput('home', self.eventOnCallback, event)
    event.wait()

  def eventOnCallback(self, event):
     event.set()

  def eventOff(self):
    logging.debug('Power off, send home button (should track active app)')
    self.remote.send_keyinput('home')

  def eventExtras(self, extras):
    """
    By setting app in extras, we will automatically launch the app
    You must provide the packasge name of the app you want to launch
    """
    if "app" in extras:
        self.launch_app(extras["app"])

  def navUp(self, zone):
    self.remote.send_keyinput('up')

  def navDown(self, zone):
    self.remote.send_keyinput('down')

  def navLeft(self, zone):
    self.remote.send_keyinput('left')

  def navRight(self, zone):
    self.remote.send_keyinput('right')

  def navEnter(self, zone):
    self.remote.send_keyinput('center')

  def navBack(self, zone):
    self.remote.send_keyinput('back')

  def navHome(self, zone):
    self.remote.send_keyinput('home')

  def playbackPlay(self, zone):
    self.remote.send_keyinput('play_pause')

  def playbackFF(self, zone):
    self.remote.send_keyinput('fast_forward')

  def playbackRW(self, zone):
    self.remote.send_keyinput('rewind')

if __name__ == "__main__":
    print('Running in standalone mode')
    argparse = argparse.ArgumentParser(description='Test the remote control protocol')
    argparse.add_argument('ip', type=str, help='IP address of the remote')
    argparse.add_argument('cmd', type=str, choices=['pair', 'control'], help='What we want to do')

    args = argparse.parse_args()

    remote = GoogleRemote(args.ip)

    if args.cmd == 'pair':
        remote.pair()
    elif args.cmd == 'control':
        print('This just demos the remote control')
        remote.control_start()
        time.sleep(5)
        remote.send_keyinput(22)
        remote.send_keyinput(22)
        remote.send_keyinput(22)
        remote.send_keyinput(22)
        time.sleep(1)
        remote.control_stop()

