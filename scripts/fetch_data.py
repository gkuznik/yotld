import urllib.request
import csv
import json
import time
import datetime
from io import StringIO
import os
import re
import urllib.error


def fetch_statcounter():
    url = "https://gs.statcounter.com/os-market-share/desktop/worldwide/chart.php?device=Desktop&device_hidden=desktop&statType_hidden=os&region_hidden=ww&granularity=monthly&statType=Operating%20System&region=Worldwide&csv=1"
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
    return data

def fetch_hn_mentions(existing_data):
    query = 'the year of linux'
    start_year = 2009
    current_year = datetime.datetime.now().year
    
    data = existing_data if existing_data else []
    existing_years = {d['year'] for d in data}
    
    for year in range(start_year, current_year + 1):
        if year in existing_years and year != current_year:
            continue
            
        start_ts = int(datetime.datetime(year, 1, 1).timestamp())
        end_ts = int(datetime.datetime(year + 1, 1, 1).timestamp()) - 1
        url = f"https://hn.algolia.com/api/v1/search?query=the%20year%20of%20linux&numericFilters=created_at_i>{start_ts},created_at_i<{end_ts}"
        
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        response = urllib.request.urlopen(req)
        result = json.loads(response.read().decode('utf-8'))
        
        found = False
        for d in data:
            if d['year'] == year:
                d['mentions'] = result.get('nbHits', 0)
                found = True
                break
        if not found:
            data.append({
                'year': year,
                'mentions': result.get('nbHits', 0)
            })
        time.sleep(0.5)
        
    return data

def fetch_steam_hardware_survey():
    url = "https://store.steampowered.com/hwsurvey/"
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    req = urllib.request.Request(url, headers=headers)
    response = urllib.request.urlopen(req)
    html = response.read().decode('utf-8')
        
    try:
        def extract(os_name):
            match = re.search(r'<div class="stats_col_mid"[^>]*>' + os_name + r'</div>\s*<div class="stats_col_right">([0-9\.]+)%</div>', html, re.IGNORECASE)
            if match:
                return float(match.group(1))
            return 0.0
            
        win = extract('Windows')
        mac = extract('OSX')
        linux = extract('Linux')
        
        if linux == 0.0:
            match2 = re.search(r'Linux.*?([0-9]+\.[0-9]+)%', html, re.IGNORECASE)
            if match2:
                linux = float(match2.group(1))
                
        if linux or win or mac:
            return {
                'windows_share': win,
                'macos_share': mac,
                'linux_share': linux
            }
    except Exception as e:
        print(f"Error fetching Steam data: {e}")
    return None

def fetch_cloudflare_radar():
    token = os.environ.get('CLOUDFLARE_API_TOKEN')
    if not token:
        print("No CLOUDFLARE_API_TOKEN found, skipping Cloudflare Radar")
        return None
        
    url = "https://api.cloudflare.com/client/v4/radar/http/timeseries_groups/os?name=main&location=US&dateRange=52w&deviceType=DESKTOP&botClass=LIKELY_HUMAN"
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    req = urllib.request.Request(url, headers=headers)
    try:
        response = urllib.request.urlopen(req)
        api_result = json.loads(response.read().decode('utf-8'))
        raw_data = api_result.get('result', {})
        main_data = raw_data.get('main', {})
        timestamps = main_data.get('timestamps', [])
        linux_vals = main_data.get('LINUX', [])
        windows_vals = main_data.get('WINDOWS', [])
        mac_vals = main_data.get('MACOSX', [])
        chrome_vals = main_data.get('CHROMEOS', [])
        
        data = []
        for i, ts in enumerate(timestamps):
            data.append({
                'date': ts,
                'linux_share': float(linux_vals[i]) if i < len(linux_vals) else 0.0,
                'windows_share': float(windows_vals[i]) if i < len(windows_vals) else 0.0,
                'macos_share': float(mac_vals[i]) if i < len(mac_vals) else 0.0,
                'chromeos_share': float(chrome_vals[i]) if i < len(chrome_vals) else 0.0
            })
            
        return data
    except Exception as e:
        print(f"Error fetching Cloudflare data: {e}")
        return None

def main():
    os.makedirs('data', exist_ok=True)
    
    def load_data(filename):
        if os.path.exists(filename):
            try:
                with open(filename, 'r') as f:
                    return json.load(f)
            except:
                pass
        return None

    print("Fetching StatCounter data...")
    sc_data = fetch_statcounter()
    if sc_data is not None:
        with open('data/statcounter.json', 'w') as f:
            json.dump(sc_data, f, indent=2)
    
    print("Fetching Hacker News mentions...")
    hn_existing = load_data('data/hackernews.json')
    hn_data = fetch_hn_mentions(hn_existing)
    if hn_data is not None:
        with open('data/hackernews.json', 'w') as f:
            json.dump(hn_data, f, indent=2)
            
    print("Fetching Cloudflare Radar data...")
    cf_data = fetch_cloudflare_radar()
    if cf_data is not None:
        with open('data/cloudflare.json', 'w') as f:
            json.dump(cf_data, f, indent=2)
            
    print("Fetching Steam Hardware Survey...")
    steam_share = fetch_steam_hardware_survey()
    steam_history = load_data('data/steam.json') or []
    current_month = datetime.datetime.now().strftime('%Y-%m')
    
    if steam_share is not None:
        if not any(d.get('date') == current_month for d in steam_history):
            steam_entry = {'date': current_month}
            steam_entry.update(steam_share)
            steam_history.append(steam_entry)
        else:
            for d in steam_history:
                if d.get('date') == current_month:
                    d.update(steam_share)
                    
        with open('data/steam.json', 'w') as f:
            json.dump(steam_history, f, indent=2)

    print("Data fetch complete.")

if __name__ == '__main__':
    main()
