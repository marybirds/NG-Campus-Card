from smartcard.System import readers
from smartcard.util import toHexString
import pdb
# --- CONFIGURATION ---
# We define our Application ID (AID) and File ID here.
# DESFire AIDs are 3 bytes. We will use 0x10, 0x20, 0x30.
APP_AID = [0x00, 0x00, 0x01]

# File ID is 1 byte. We will use file ID 01.
FILE_ID = 0x02

# The text we want to write
TEXT_TO_WRITE = "Hello World!"
# Convert text to byte array
DATA_BYTES = [ord(c) for c in TEXT_TO_WRITE]

print(">>> Scanning for readers...")
r = readers()
if len(r) == 0:
    print(">>> No readers found. Please connect a reader.")
    exit()

reader = r[1]
print(f">>> Using reader: {reader}")

connection = reader.createConnection()
connection.connect()
print(">>> Card connected.")

# ==============================================================================
# IMPORTANT NOTE ON ISO WRAPPING FOR DESFIRE
# ==============================================================================
# Since your reader requires 7816-4 APDUs, we wrap DESFire native commands.
# Structure: CLA  INS  P1  P2  Lc  [Data]  Le
# CLA = 0x90 (NXP Proprietary / DESFire Wrapping)
# INS = The DESFire Command Code (e.g., 0xCA for Create Application)
# P1  = 0x00
# P2  = 0x00
# Data = The specific parameters for the command
# ==============================================================================


# ------------------------------------------------------------------------------
# STEP 1: SELECT THE MASTER APPLICATION (PICC LEVEL)
# ------------------------------------------------------------------------------
# Before doing anything, we ensure we are at the root level (AID 00 00 00).
# DESFire Command: SelectApplication (0x5A)
# Data: 00 00 00
# Wrapped APDU: 90 5A 00 00 03 00 00 00 00

print("\n--- Step 1: Selecting Master Application ---")
apdu = [0x90, 0x5A, 0x00, 0x00, 0x03, 0x00, 0x00, 0x00, 0x00]
response, sw1, sw2 = connection.transmit(apdu)
print(f"Status: {hex(sw1)} {hex(sw2)}")

# DESFire Successful Operation in Wrapped mode usually returns SW1=0x91, SW2=0x00
if sw1 == 0x91 and sw2 == 0x00:
    print(">>> Success: Master Application Selected")
else:
    print(">>> Error selecting Master App. (Is the card on the reader?)")
    exit()


# ------------------------------------------------------------------------------
# STEP 2: CREATE A NEW APPLICATION
# ------------------------------------------------------------------------------
# We will create an application with AID [10 20 30].
# DESFire Command: CreateApplication (0xCA)
# Params: AID (3 bytes) | Settings (1 byte) | KeyType (1 byte)
# Settings: 0x0F (Allow changing keys, config changeable, typical default)
# KeyType:  0x21 (AES keys, 1 key required). 
# Note: On a brand new card, no authentication is needed to create apps.

print(f"\n--- Step 2: Creating Application {toHexString(APP_AID)} ---")

# Command Construction
cmd_code = [0xCA]
params = APP_AID + [0x0F, 0x21] # AID + Settings + KeyType
L_c = len(params) # Length of data
apdu = [0x90] + cmd_code + [0x00, 0x00, L_c] + params + [0x00]

response, sw1, sw2 = connection.transmit(apdu)
print(f"Status: {hex(sw1)} {hex(sw2)}")

if sw1 == 0x91 and sw2 == 0x00:
    print(">>> Success: Application Created.")
elif sw1 == 0x91 and sw2 == 0xDE: 
    # 0x91DE is the specific error for "Duplicate Error" (App already exists)
    print(">>> Notice: Application already exists. Proceeding...")
else:
    print(f">>> Error creating application. Code: {hex(sw2)}")
    exit()


# ------------------------------------------------------------------------------
# STEP 3: SELECT THE NEW APPLICATION
# ------------------------------------------------------------------------------
# Now we must "enter" the folder we just created (or verified).
# DESFire Command: SelectApplication (0x5A)
# Data: AID (10 20 30)

print(f"\n--- Step 3: Selecting Application {toHexString(APP_AID)} ---")

cmd_code = [0x5A]
params = APP_AID
L_c = len(params)
apdu = [0x90] + cmd_code + [0x00, 0x00, L_c] + params + [0x00]

response, sw1, sw2 = connection.transmit(apdu)
print(f"Status: {hex(sw1)} {hex(sw2)}")

if sw1 == 0x91 and sw2 == 0x00:
    print(">>> Success: Application Selected.")
else:
    print(">>> Error selecting application.")
    exit()


# ------------------------------------------------------------------------------
# STEP 4: CREATE A STANDARD DATA FILE
# ------------------------------------------------------------------------------
# We will create a "Standard Data File" (ID 01) inside the app.
# DESFire Command: CreateStdDataFile (0xCD)
# Params: FileID(1) | ISOFileID(2) | CommSettings(1) | AccessRights(2) | FileSize(3)
#
# Details:
# FileID: 0x01
# ISOFileID: 0x00 00 (Not using ISO 7816-4 file referencing for this file)
# CommSettings: 0x00 (Plain communication - no encryption for data transfer)
# AccessRights: 0xE0 0xE0 (Read/Write is "Free" for everyone - 0xE is the nibble for 'Free')
# FileSize: 50 bytes. DESFire is LITTLE ENDIAN. 50 = 0x32. So: 32 00 00

print(f"\n--- Step 4: Creating File ID {hex(FILE_ID)} ---")

file_id_byte = [FILE_ID]
iso_file_id = [0x00, 0x00]
comm_settings = [0x00]
access_rights = [0xE0, 0xE0] # Free Read/Write
file_size = [0x32, 0x00, 0x00] # 50 Bytes (Little Endian)

params = file_id_byte + iso_file_id + comm_settings + access_rights + file_size
L_c = len(params)

apdu = [0x90, 0xCD, 0x00, 0x00, L_c] + params + [0x00]

response, sw1, sw2 = connection.transmit(apdu)
print(f"Status: {hex(sw1)} {hex(sw2)}")

if sw1 == 0x91 and sw2 == 0x00:
    print(">>> Success: File Created.")
elif sw1 == 0x91 and sw2 == 0xDE:
    print(">>> Notice: File already exists. Proceeding...")
else:
    print(f">>> Error creating file. Code: {hex(sw2)}")
    exit()


# ------------------------------------------------------------------------------
# STEP 5: WRITE DATA TO THE FILE
# ------------------------------------------------------------------------------
# DESFire Command: WriteData (0x3D)
# Params: FileID(1) | Offset(3) | Length(3) | Data(N)
# Note: Offset and Length are Little Endian!

print(f"\n--- Step 5: Writing '{TEXT_TO_WRITE}' to File {hex(FILE_ID)} ---")

# Calculate lengths
data_len_int = len(DATA_BYTES)
# Convert length to 3-byte Little Endian
data_len_bytes = [data_len_int, 0x00, 0x00]
# Offset = 0
offset_bytes = [0x00, 0x00, 0x00]

params = [FILE_ID] + offset_bytes + data_len_bytes + DATA_BYTES
L_c = len(params)

apdu = [0x90, 0x3D, 0x00, 0x00, L_c] + params + [0x00]

response, sw1, sw2 = connection.transmit(apdu)
print(f"Status: {hex(sw1)} {hex(sw2)}")

if sw1 == 0x91 and sw2 == 0x00:
    print(">>> Success: Data Written.")
else:
    print(f">>> Error writing data. Code: {hex(sw2)}")
    exit()


# ------------------------------------------------------------------------------
# STEP 6: READ DATA (VERIFICATION)
# ------------------------------------------------------------------------------
# DESFire Command: ReadData (0xBD)
# Params: FileID(1) | Offset(3) | Length(3)
# Note: Length 00 00 00 means "Read entire file"

print(f"\n--- Step 6: Reading back data from File {hex(FILE_ID)} ---")

params = [FILE_ID] + [0x00, 0x00, 0x00] + [0x00, 0x00, 0x00]
L_c = len(params)

apdu = [0x90, 0xBD, 0x00, 0x00, L_c] + params + [0x00]

response, sw1, sw2 = connection.transmit(apdu)

# When reading, the 'response' list contains the data read from the card
if sw1 == 0x91 and sw2 == 0x00:
    # Convert byte array back to string
    # We trim null bytes if any (though we wrote exact length)
    read_str = "".join([chr(x) for x in response if x != 0])
    print(f">>> Success! Read Data: {read_str}")
    print(f">>> Hex Data: {toHexString(response)}")
    
    if read_str == TEXT_TO_WRITE:
        print("\n*** VERIFICATION SUCCESSFUL ***")
    else:
        print("\n*** VERIFICATION FAILED (Data mismatch) ***")
else:
    print(f">>> Error reading data. Code: {hex(sw2)}")