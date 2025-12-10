import socket
import time

class PhoneMifareReader:
    def __init__(self, phone_ip: str):
        self.phone_ip = phone_ip
        self.port = 8765
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.settimeout(5.0)
        self.sock.connect((phone_ip, self.port))
        print(f"✅ Connected to phone at {phone_ip}")
    
    def auth(self, sector: int, key: str) -> bool:
        """key is 12 hex chars, e.g., 'FFFFFFFFFFFF'"""
        resp = self._send(f"AUTH,{sector},{key}")
        return resp == "OK"
    
    def read(self, block: int) -> bytes:
        resp = self._send(f"READ,{block}")
        if resp.startswith("ERROR"):
            raise RuntimeError(resp)
        return bytes.fromhex(resp)
    
    def write(self, block: int, data: bytes):
        if len(data) != 16:
            raise ValueError("Data must be 16 bytes")
        resp = self._send(f"WRITE,{block},{data.hex()}")
        if resp != "OK":
            raise RuntimeError(resp)
    
    def get_uid(self) -> bytes:
        resp = self._send("GET_UID")
        return bytes.fromhex(resp)
    
    def _send(self, cmd: str) -> str:
        self.sock.sendall(cmd.encode() + b'\n')
        return self.sock.recv(1024).decode().strip()
    
    def close(self):
        self.sock.close()

# Test script
if __name__ == "__main__":
    PHONE_IP = "192.168.137.19"  # CHANGE THIS
    
    reader = PhoneMifareReader(PHONE_IP)
    try:
        print(f"UID: {reader.get_uid().hex()}")
        
        # Test with default key
        if reader.auth(1, "FFFFFFFFFFFF"):
            print("Sector auth: OK")
            block0 = reader.read(4)
            print(f"Block : {block0.hex()}")
        else:
            print("Auth failed - try different key")
    finally:
        reader.close()