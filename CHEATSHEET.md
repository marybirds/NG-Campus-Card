# pyscard Cheat Sheet - Quick Reference

## Installation

```bash
pip install pyscard
```

## Basic Imports

```python
from smartcard.System import readers
from smartcard.util import toHexString, toBytes
from smartcard.ATR import ATR
```

## Common Operations

### List All Readers

```python
reader_list = readers()
for reader in reader_list:
    print(reader)
```

### Connect to Card

```python
# Get first reader
reader = readers()[0]

# Create connection
connection = reader.createConnection()

# Connect to card
connection.connect()
```

### Read ATR

```python
atr = connection.getATR()
print(toHexString(atr))
```

### Send APDU Command

```python
# Command as list
command = [0xFF, 0xCA, 0x00, 0x00, 0x00]

# Transmit
data, sw1, sw2 = connection.transmit(command)

# Check status
if sw1 == 0x90 and sw2 == 0x00:
    print("Success:", toHexString(data))
else:
    print(f"Error: {sw1:02X} {sw2:02X}")
```

### Disconnect

```python
connection.disconnect()
```

## Common APDU Commands

### Get UID (Contactless Cards)

```python
GET_UID = [0xFF, 0xCA, 0x00, 0x00, 0x00]
data, sw1, sw2 = connection.transmit(GET_UID)
```

### Read Binary (Block Number)

```python
# Read block 4, 16 bytes
block_number = 0x04
READ_BINARY = [0xFF, 0xB0, 0x00, block_number, 0x10]
data, sw1, sw2 = connection.transmit(READ_BINARY)
```

### Update Binary (Write Data)

```python
# Write to block 4
block_number = 0x04
write_data = [0x48, 0x65, 0x6C, 0x6C, 0x6F]  # "Hello"
UPDATE_BINARY = [0xFF, 0xD6, 0x00, block_number, len(write_data)] + write_data
data, sw1, sw2 = connection.transmit(UPDATE_BINARY)
```

### Load Authentication Key (MIFARE)

```python
# Load key FFFFFFFFFFFFh to key location 0
key = [0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF]
LOAD_KEY = [0xFF, 0x82, 0x00, 0x00, 0x06] + key
data, sw1, sw2 = connection.transmit(LOAD_KEY)
```

### Authenticate (MIFARE)

```python
# Authenticate block 4 with Key A
block = 0x04
key_type = 0x60  # Key A (0x60) or Key B (0x61)
key_location = 0x00
AUTHENTICATE = [0xFF, 0x86, 0x00, 0x00, 0x05, 0x01, 0x00, block, key_type, key_location]
data, sw1, sw2 = connection.transmit(AUTHENTICATE)
```

## Card Monitoring

### Monitor Card Events

```python
from smartcard.CardMonitoring import CardMonitor, CardObserver
import time

class MyObserver(CardObserver):
    def update(self, observable, actions):
        (added, removed) = actions
        for card in added:
            print("Card inserted:", toHexString(card.atr))
        for card in removed:
            print("Card removed:", toHexString(card.atr))

monitor = CardMonitor()
observer = MyObserver()
monitor.addObserver(observer)

# Keep running
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    monitor.deleteObserver(observer)
```

## Exception Handling

```python
from smartcard.Exceptions import (
    NoCardException,
    CardConnectionException,
    NoReadersException
)

try:
    connection.connect()
except NoCardException:
    print("No card present")
except CardConnectionException:
    print("Failed to connect")
except NoReadersException:
    print("No readers available")
except Exception as e:
    print(f"Error: {e}")
```

## Utility Functions

### Convert Hex String to Bytes

```python
from smartcard.util import toBytes

# Convert hex string to byte list
apdu = toBytes("FF CA 00 00 00")
# Result: [255, 202, 0, 0, 0]
```

### Convert Bytes to Hex String

```python
from smartcard.util import toHexString

# Convert byte list to hex string
data = [255, 202, 0, 0]
hex_str = toHexString(data)
# Result: "FF CA 00 00"
```

### ASCII Conversion

```python
# Bytes to ASCII
data = [72, 101, 108, 108, 111]
text = ''.join([chr(b) for b in data])
# Result: "Hello"

# ASCII to Bytes
text = "Hello"
data = [ord(c) for c in text]
# Result: [72, 101, 108, 108, 111]
```

## ATR Analysis

```python
from smartcard.ATR import ATR

atr = ATR(connection.getATR())

# Get historical bytes
hist = atr.getHistoricalBytes()

# Check protocols
if atr.isT0Supported():
    print("T=0 supported")
if atr.isT1Supported():
    print("T=1 supported")

# Get checksum
checksum = atr.getChecksum()
checksum_ok = atr.checksumOK
```

## Status Words (SW1 SW2)

| SW1 | SW2 | Meaning                             |
| --- | --- | ----------------------------------- |
| 90  | 00  | Success                             |
| 61  | XX  | XX bytes available                  |
| 62  | 00  | Warning: No information given       |
| 63  | 00  | Warning: Operation failed           |
| 64  | 00  | Execution error                     |
| 65  | 00  | Memory failure                      |
| 67  | 00  | Wrong length                        |
| 68  | XX  | Function not supported              |
| 69  | 00  | Command not allowed                 |
| 6A  | 00  | Wrong parameters P1-P2              |
| 6A  | 81  | Function not supported              |
| 6A  | 82  | File not found                      |
| 6A  | 86  | Incorrect P1 P2                     |
| 6B  | 00  | Wrong parameters P1-P2              |
| 6D  | 00  | Instruction not supported           |
| 6E  | 00  | Class not supported                 |
| 6F  | 00  | Command aborted - technical problem |

## APDU Structure

### Command APDU

```
+------+------+------+------+------+--------+------+
| CLA  | INS  | P1   | P2   | Lc   | Data   | Le   |
+------+------+------+------+------+--------+------+
  1byte 1byte 1byte  1byte  1byte  N bytes  1byte
```

- **CLA**: Class (instruction category)
- **INS**: Instruction code
- **P1, P2**: Parameters
- **Lc**: Length of data field
- **Data**: Command data
- **Le**: Expected response length

### Response APDU

```
+--------+------+------+
| Data   | SW1  | SW2  |
+--------+------+------+
 N bytes 1byte  1byte
```

- **Data**: Response data
- **SW1, SW2**: Status words

## Common Patterns

### Retry Connection

```python
import time

def connect_with_retry(reader, retries=3):
    for i in range(retries):
        try:
            connection = reader.createConnection()
            connection.connect()
            return connection
        except:
            if i < retries - 1:
                time.sleep(0.5)
            else:
                raise
```

### Safe Command Execution

```python
def safe_transmit(connection, apdu):
    """Transmit with error handling"""
    try:
        data, sw1, sw2 = connection.transmit(apdu)
        if sw1 == 0x90 and sw2 == 0x00:
            return data, True
        else:
            print(f"Error: {sw1:02X} {sw2:02X}")
            return None, False
    except Exception as e:
        print(f"Exception: {e}")
        return None, False
```

### Card Detector Loop

```python
def wait_for_card(reader, timeout=30):
    """Wait for card insertion"""
    import time
    start = time.time()

    while time.time() - start < timeout:
        try:
            connection = reader.createConnection()
            connection.connect()
            return connection
        except:
            time.sleep(0.5)

    raise TimeoutError("No card detected")
```

## Debugging Tips

### Print APDU Communication

```python
def debug_transmit(connection, apdu, description=""):
    print(f"\n{description}")
    print(f">> TX: {toHexString(apdu)}")

    data, sw1, sw2 = connection.transmit(apdu)

    print(f"<< RX: {toHexString(data)}")
    print(f"<< SW: {sw1:02X} {sw2:02X}")

    return data, sw1, sw2
```

### Log All Reader Events

```python
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('smartcard')
```

## Platform-Specific

### Check PC/SC Service

**Linux:**

```bash
sudo systemctl status pcscd
sudo systemctl restart pcscd
```

**macOS:**

```bash
sudo killall -9 pcscd  # Restarts automatically
```

**Windows:**

```cmd
sc query SCardSvr
sc start SCardSvr
```

### Test Reader from Terminal

**Linux/macOS:**

```bash
pcsc_scan
```

**Windows (PowerShell):**

```powershell
Get-Service SCardSvr
```

## Quick Troubleshooting

| Problem                   | Solution                                                  |
| ------------------------- | --------------------------------------------------------- |
| No readers found          | Check USB, restart PC/SC service                          |
| No card exception         | Card not present or not seated properly                   |
| Permission denied (Linux) | Add user to pcscd group: `sudo usermod -a -G pcscd $USER` |
| Wrong status words        | Check card type, may need authentication                  |
| Import error              | `pip install pyscard`                                     |

## Learning Resources

- **pyscard docs**: https://pyscard.sourceforge.io/
- **PC/SC specs**: https://www.pcscworkgroup.com/
- **ISO 7816**: Smart card standards

---

**Print this out and keep it handy while coding!** 📋
