
def custom_hash(s):
    h = 1337
    for char in s:
        h = (h * 31 + ord(char)) ^ (h >> 7)
        h = h & 0xFFFFFFFF  # force unsigned 32-bit
    return hex(h)[2:]

def make_flag(name):
    clean_name = name.strip() or "anon"
    h = custom_hash(clean_name)
    return f"ictf{{{h}}}"

print(make_flag("Eth007"))
