import itertools
import json


def generate_indexes():
    while True:
        yield ''


# Extract indexes
indexes = []
gen = generate_indexes()

with open('sync_exports\\a9998bd1-7174-4998-a0ce-613b8959209e\\1bc80041-4ccf-45c6-8d22-585848b898d2\\1bc80041-4ccf-45c6-8d22-585848b898d2.content.json') as f:
    data = json.load(f)
    for page in data['cPages']['pages']:
        indexes.append(page['idx']['value'])

with open('indexes.txt', 'w') as f:
    f.writelines([
        index + '\n'
        for index in indexes
    ])

for index in indexes[:100]:
    val = next(gen) 
    correct = val == index
    print(f"{index}: {correct} -> {val}")