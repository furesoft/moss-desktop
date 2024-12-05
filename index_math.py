import itertools
import json


def generate_indexes():
    char_first = chr(ord('a') - 1)
    chars = ['b', char_first]
    target = 1
    n_ord = ord('n')
    z_ord = ord('z')
    a_ord = ord('a')

    def increment_char(char):
        return chr(ord(char) + 1)

    while True:
        chars[target] = increment_char(chars[target])
        yield ''.join(chars)

        z_index = target
        while chars[z_index] == 'z':
            if z_index == 0:
                chars.insert(0, 'a')
                target += 1
                z_index += 1
            chars[z_index-1] = increment_char(chars[z_index-1])
            chars[z_index] = char_first



# Extract indexes
indexes = []
gen = generate_indexes()

# with open('sync_exports\\a9998bd1-7174-4998-a0ce-613b8959209e\\1bc80041-4ccf-45c6-8d22-585848b898d2\\1bc80041-4ccf-45c6-8d22-585848b898d2.content.json') as f:
#     data = json.load(f)
#     for page in data['cPages']['pages']:
#         indexes.append(page['idx']['value'])

with open('indexes.txt', 'r') as f:
    indexes = [index.strip() for index in f.readlines()]

# with open('indexes.txt', 'w') as f:
#     f.writelines([
#         index + '\n'
#         for index in indexes
#     ])

for index in indexes[:500]:
    val = next(gen)
    correct = val == index
    if not correct:
        print(f"{index}: {correct} -> {val}")
    else:
        print(f"{index}")
