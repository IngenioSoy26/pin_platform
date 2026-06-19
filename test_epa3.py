import csv
with open(r'c:\Users\gusta\Desktop\Maestria\0.1. Practicas\pin_platform\dataset\EPA_Disaster_Debris_Recovery_Data_903120106498694009.csv', 'r', encoding='utf-8-sig') as f:
    reader = csv.DictReader(f)
    c = 0
    for row in reader:
        is_epa_file = ('OBJECTID' in row) or ('Tires' in row and 'Latitude' in row)
        if is_epa_file:
            c += 1
    print('is_epa_file count:', c)
