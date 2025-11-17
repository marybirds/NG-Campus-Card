from smartcard.System import readers
from smartcard.util import toHexString
from smartcard.ATR import ATR

reader_list = readers()
for reader in reader_list:
    print(reader)
reader_id = int(input("enter the reader id"))
reader = readers()[reader_id]
connection = reader.createConnection()

connection.connect()

atr = connection.getATR()
print(toHexString(atr))
