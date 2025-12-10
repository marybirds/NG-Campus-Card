import socket
import struct
from smartcard.System import readers as original_readers
from smartcard.CardConnection import CardConnection

class PhoneConnection(CardConnection):
    def __init__(self, phone_ip):
        self.phone_ip = phone_ip
        self.sock = None
        self.atr = None
        
    def connect(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((self.phone_ip, 8765))
        # Build synthetic ATR from UID
        uid = self._send("GET_UID")
        self.atr = self._build_atr(bytes.fromhex(uid))
        
    def getATR(self):
        return self.atr
        
    def _build_atr(self, uid):
        # Standard MIFARE Classic ATR template
        atr = [0x3B, 0x8F, 0x80, 0x01, 0x80, 0x4F, 0x0C, 
               0xA0, 0x00, 0x00, 0x03, 0x06, 0x03, 0x00, 
               0x01, 0x00, 0x00, 0x00, 0x00, 0x6A]
        # Insert UID length and bytes
        atr[7] = 0xA0 + len(uid)
        for i, b in enumerate(uid[:4]):
            atr[8 + i] = b
        return atr
        
    def _send(self, cmd):
        self.sock.sendall(cmd.encode() + b'\n')
        return self.sock.recv(1024).decode().strip()


    def transmit(self, apdu_bytes):
        try:
            # ---- LOAD KEY: FF 82 00 00 06 [6-byte key] ----
            if len(apdu_bytes) == 11 and apdu_bytes[0:5] == [0xFF, 0x82, 0x00, 0x00, 0x06]:
                self.current_key = bytes(apdu_bytes[5:11]).hex()
                return [], 0x90, 0x00

            # ---- AUTH: FF 86 00 00 05 [key slot] [key version] [sector] [key type] 00 ----
            elif len(apdu_bytes) == 10 and apdu_bytes[0:4] == [0xFF, 0x86, 0x00, 0x00]:
                if not hasattr(self, 'current_key'):
                    return [], 0x6F, 0x00  # Key not loaded
                
                sector = apdu_bytes[7]  # Correct byte position for sector
                response = self._send(f"AUTH,{sector},{self.current_key}")
                return ([], 0x90, 0x00) if response == "OK" else ([], 0x63, 0x00)

            # ---- READ BINARY: FF B0 00 <block> 0x10 ----
            elif len(apdu_bytes) == 5 and apdu_bytes[0:4] == [0xFF, 0xB0, 0x00, apdu_bytes[3]]:
                block = apdu_bytes[3]
                response = self._send(f"READ,{block}")
                if response.startswith("ERROR"):
                    return [], 0x6F, 0x00
                data = bytes.fromhex(response)
                return list(data), 0x90, 0x00

            # ---- WRITE BINARY: FF D0 00 <block> 0x10 [16 bytes] ----
            elif len(apdu_bytes) == 21 and apdu_bytes[0:4] == [0xFF, 0xD0, 0x00, apdu_bytes[3]]:
                block = apdu_bytes[3]
                data = bytes(apdu_bytes[5:21]).hex()
                response = self._send(f"WRITE,{block},{data}")
                return ([], 0x90, 0x00) if response == "OK" else ([], 0x6F, 0x00)

            # ---- GET DATA (UID): FF CA 00 00 00 ----
            elif apdu_bytes == [0xFF, 0xCA, 0x00, 0x00, 0x00]:
                response = self._send("GET_UID")
                return list(bytes.fromhex(response)), 0x90, 0x00

            else:
                return [], 0x6D, 0x00  # Command not supported

        except Exception as e:
            return [], 0x6F, 0x00  # General error
    


class PhoneReader:
    def __init__(self, phone_ip="192.168.137.19"):
        self.phone_ip = phone_ip
        
    def __str__(self):
        return f"Phone MIFARE Classic ({self.phone_ip})"
        
    def createConnection(self):
        return PhoneConnection(self.phone_ip)

# This is the magic – replaces smartcard.System.readers()
def readers():
    normal_list = original_readers()
    # Return list with one virtual reader
    return [PhoneReader()] + normal_list