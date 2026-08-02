import csv
import json
import urllib.request
import codecs
from collections import defaultdict

def backfill():
    shs_data = defaultdict(dict)
    shs_url = 'https://raw.githubusercontent.com/jdegene/steamHWsurvey/master/shs.csv'
    with urllib.request.urlopen(shs_url) as response:
        reader = csv.DictReader(codecs.iterdecode(response, 'utf-8'))
        for row in reader:
            if row['category'] == 'OS Version':
                try:
                    val = float(row['percentage'])
                    if val > 0:
                        shs_data[row['date']][row['name']] = val
                except ValueError:
                    pass

    platform_data = defaultdict(lambda: defaultdict(dict))
    platform_url = 'https://raw.githubusercontent.com/jdegene/steamHWsurvey/master/shs_platform.csv'
    with urllib.request.urlopen(platform_url) as response:
        reader = csv.DictReader(codecs.iterdecode(response, 'utf-8'))
        for row in reader:
            if 'Version' in row['category'] and row['category'] in ['Windows Version', 'OSX Version', 'Linux Version']:
                try:
                    val = float(row['percentage'])
                    if val > 0:
                        platform_data[row['date']][row['platform']][row['name']] = val
                except ValueError:
                    pass

    results = {}
    for date, p_data in platform_data.items():
        if date not in shs_data:
            continue
            
        date_formatted = date[:7] # YYYY-MM
        shares = {'windows_share': 0.0, 'macos_share': 0.0, 'linux_share': 0.0}
        valid = False
        
        for platform, p_key in [('pc', 'windows_share'), ('mac', 'macos_share'), ('linux', 'linux_share')]:
            platform_share = 0.0
            names = p_data.get(platform, {})
            # try to find the name with highest percentage to avoid floating point errors
            best_name = None
            best_val = -1
            for name, plat_perc in names.items():
                if name in shs_data[date] and plat_perc > best_val:
                    best_name = name
                    best_val = plat_perc
                    
            if best_name is not None:
                overall_perc = shs_data[date][best_name]
                platform_share = overall_perc / best_val
                valid = True
                
            shares[p_key] = round(platform_share * 100, 2)
            
        if valid:
            total = shares['windows_share'] + shares['macos_share'] + shares['linux_share']
            if 95.0 <= total <= 105.0:
                results[date_formatted] = {
                    'date': date_formatted,
                    'linux_share': shares['linux_share'],
                    'windows_share': shares['windows_share'],
                    'macos_share': shares['macos_share']
                }

    existing = []
    try:
        with open('data/steam.json', 'r', encoding='utf-8') as f:
            existing = json.load(f)
    except:
        pass
        
    merged = {r['date']: r for r in existing}
    for date, r in results.items():
        if date not in merged:
            merged[date] = r
            
    final_list = sorted(merged.values(), key=lambda x: x['date'])
    with open('data/steam.json', 'w', encoding='utf-8') as f:
        json.dump(final_list, f, indent=2)
        
    print("Backfill complete. Total entries:", len(final_list))

if __name__ == '__main__':
    backfill()
