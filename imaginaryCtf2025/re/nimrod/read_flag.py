
with open("nimrod", "rb") as f:
    f.seek(0x116e8)
    data = f.read(34)
    print(data.hex())
