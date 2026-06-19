import csv
with open(r'c:\Users\gusta\Desktop\Maestria\0.1. Practicas\pin_platform\dataset\US_Recycling_Infrastructure_2022_-7015395891470271269.csv', 'r', encoding='utf-8-sig') as f:
    reader = csv.DictReader(f)
    c = 0
    has_recycled = 0
    has_generated = 0
    for r in reader:
        c += 1
        if r.get('Tires Tons Recycled'): has_recycled += 1
        if r.get('Tires Tons  Generated'): has_generated += 1
    print(f'Total: {c}, Recycled: {has_recycled}, Generated: {has_generated}')
