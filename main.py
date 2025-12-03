from smartcard.System import readers
from smartcard.util import toHexString
from smartcard.ATR import ATR
import requests

reader_list = readers()
for reader in reader_list:
    print(reader)
#reader_id = int(input("enter the reader id"))
reader = readers()[0]
connection = reader.createConnection()

connection.connect()

atr = connection.getATR()
print(toHexString(atr))

SUCCESS_SW1 = 0x90
SUCCESS_SW2 = 0x00
class MifareClassicPCSC:
    def __init__(self, reader_index=0):
        r = readers()
        if not r:
            raise RuntimeError("No PC/SC readers found")
        if reader_index >= len(r):
            raise IndexError(f"reader_index {reader_index} out of range (found {len(r)})")
        self.reader = r[reader_index]
        self.connection = self.reader.createConnection()
        self.connection.connect()

    @staticmethod
    def _check_sw(resp, sw1, sw2):
        return (sw1 == SUCCESS_SW1 and sw2 == SUCCESS_SW2)

    def load_authentication_key(self):
        key_number= 0x00
        apdu = [0xFF, 0x82, 0x00, key_number, 0x06] + list([0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF])
        resp, sw1, sw2 = self.connection.transmit(apdu)
        return self._check_sw(resp, sw1, sw2)


    def authenticate_block(self, block_number):
        key_type_code = 0x60 

        apdu = [0xFF, 0x86, 0x00, 0x00, 0x05,
        0x01, 0x00, block_number & 0xFF, key_type_code, 0x00]
        resp, sw1, sw2 = self.connection.transmit(apdu)
        return self._check_sw(resp, sw1, sw2)

    def write_block(self, block_number, data16):
        self.authenticate_block(block_number)
        if len(data16) != 16:
            raise ValueError("write_block requires exactly 16 bytes")
        apdu = [0xFF, 0xD6, 0x00, block_number] + list(data16)
        resp, sw1, sw2 = self.connection.transmit(apdu)
        return self._check_sw(resp, sw1, sw2)

    def read_block(self, block_number):
        self.authenticate_block(block_number)
        """Read 16 bytes from a block. Returns bytes list on success, raises on failure."""
        apdu = [0xFF, 0xB0, 0x00, block_number]
        resp, sw1, sw2 = self.connection.transmit(apdu)
        if not self._check_sw(resp, sw1, sw2):
            raise RuntimeError(f"Read failed: SW1={hex(sw1)} SW2={hex(sw2)}")
        return resp
    
    def string_to_3_blocks(self, s: str):

        b = s.encode("utf-8")

        blocks = []
        for i in range(3):
            chunk = b[i*16 : (i+1)*16]
            # pad to 16 bytes
            padded = list(chunk.ljust(16, b"\x00"))
            blocks.append(padded)

        return blocks
    
if __name__ == '__main__':


    mc = MifareClassicPCSC()
    mc.load_authentication_key()

    try:

        

        email = "mohamed@gmail.com"
        password = "12345678"

        email_data = mc.string_to_3_blocks(email)
        pass_data = mc.string_to_3_blocks(password)

        read_data = []
  
        for i in range( 3 ):
            mc.write_block( i + 4 , email_data[i])
            mc.write_block( i + 8 , pass_data[i])


        parsed_email = []
        for i in range( 3 ):
            read_data.append(mc.read_block( i + 4 ) )
            for j in range (len(read_data[i])):
                byte = read_data[i][j]
                if byte :
                    parsed_email.append(byte)
                else:
                    break 
            if byte == 0 : break

        email = bytes(parsed_email).decode('utf-8')
        


        read_data = []
        parsed_password = []
        for i in range( 3 ):
            read_data.append(mc.read_block( i + 8 ) )
            for j in range (len(read_data[i])):
                byte = read_data[i][j]
                if byte :
                    parsed_password.append(byte)
                else:
                    break 
            if byte == 0 : break

        password = bytes(parsed_password).decode('utf-8')

        print("Email: " + email)
        print("Password: " + password)



        url = "http://webauth.test/login"
        payload = {
            "email": email,
            "password": password, 
            }
        
        response = requests.post(url, json=payload)
        print(response.text)
        print(response.status_code)




    except Exception as e:
        print("Error:", e)


    finally:
        try:
            mc.connection.disconnect()
        except Exception:
            pass







































'''# app.py
from flask import Flask, jsonify, render_template_string

app = Flask(__name__)



@app.route("/")
def home():
    return jsonify(message=str(reader_list))

@app.route("/api/hello")
def api_hello():
    return jsonify(message="Hello Zord")

if __name__ == "__main__":
    # dev server
    app.run(host="0.0.0.0", port=5000, debug=True)'''


