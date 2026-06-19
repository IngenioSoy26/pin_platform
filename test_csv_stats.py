import csv
with open(r'c:\Users\gusta\Desktop\Maestria\0.1. Practicas\pin_platform\dataset\Monthly_Transportation_Statistics_20260604.csv', 'r', encoding='utf-8-sig') as f:
    reader = csv.DictReader(f)
    c = 0
    for r in reader:
        t = r.get('Transportation Employment - Truck Transportation')
        d = r.get('Highway Fuel Price - On-highway Diesel')
        f_at = r.get('Highway Fatalities')
        if t or d or f_at:
            print(r.get('Date'), "Truck:", t, "Diesel:", d, "Fatal:", f_at)
            c += 1
            if c > 5: break
