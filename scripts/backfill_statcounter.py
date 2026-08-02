import csv
import json
import urllib.request
from io import StringIO
import os

def backfill():
    url = "https://gs.statcounter.com/os-market-share/desktop/worldwide/chart.php?device_hidden=desktop&statType_hidden=os&region_hidden=ww&granularity=monthly&csv=1"
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    req = urllib.request.Request(url, headers=headers)
    response = urllib.request.urlopen(req)
    csv_data = response.read().decode('utf-8')
        
    reader = csv.DictReader(StringIO(csv_data))
    data = []
    for row in reader:
        if 'Date' in row:
            date = row.get('Date')
            if not date:
                continue
            
            win_share = sum(float(row.get(k, 0) or 0) for k in row.keys() if k and k.startswith('Win'))
            mac_share = float(row.get('OS X', 0) or 0) + float(row.get('macOS', 0) or 0)
            linux_share = float(row.get('Linux', 0) or 0)
            chrome_share = float(row.get('Chrome OS', 0) or 0)
            
            if win_share == 0 and mac_share == 0 and linux_share == 0 and chrome_share == 0:
                continue
            
            data.append({
                'date': date,
                'linux_share': linux_share,
                'windows_share': win_share,
                'macos_share': mac_share,
                'chromeos_share': chrome_share
            })
                    
    data.sort(key=lambda x: x['date'])
    
    os.makedirs('data', exist_ok=True)
    with open('data/statcountr.json', 'w') as f:
        json.dump(data, f, indent=2)
        
    print("StatCounter backfill complete. Total entries:", len(data))

if __name__ == '__main__':
    backfill()
