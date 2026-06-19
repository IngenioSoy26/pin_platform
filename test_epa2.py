import csv
with open(r'c:\Users\gusta\Desktop\Maestria\0.1. Practicas\pin_platform\dataset\EPA_Disaster_Debris_Recovery_Data_903120106498694009.csv', 'r', encoding='utf-8-sig') as f:
    reader = csv.DictReader(f)
    c = 0
    for r in reader:
        lat = r.get('Latitude')
        lon = r.get('Longitude')
        tires = str(r.get('Tires', '')).strip()
        if tires == '1' and lat and lon:
            c += 1
    print('Llantas con coords:', c)
