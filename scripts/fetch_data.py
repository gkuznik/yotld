import urllib.request
import urllib.parse
import csv
import json
import time
import datetime
from io import StringIO
import os
import re
import urllib.error


def fetch_statcounter(existing_data):
    current_date = datetime.datetime.now()
    year = current_date.year
    month = current_date.month - 1
    if month == 0:
        month = 12
        year -= 1
        
    target_str = f"{year}-{month:02d}"
    
    url = f"https://gs.statcounter.com/os-market-share/desktop/worldwide/chart.php?device_hidden=desktop&statType_hidden=os&region_hidden=ww&granularity=monthly&csv=1&fromMonthYear={target_str}&toMonthYear={target_str}"
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
                    
    data_dict = {d['date']: d for d in existing_data} if existing_data else {}
    for d in data:
        data_dict[d['date']] = d
        
    merged = list(data_dict.values())
    merged.sort(key=lambda x: x['date'])
    return merged

def fetch_hn_mentions(existing_data):
    queries = [
        '"year of the linux desktop"',
        '"year of desktop linux"',
        '"year of linux on the desktop"',
        '"linux desktop year"',
        '"year of linux"',
        'yotld'
    ]
    today = datetime.date.today()
    first = datetime.datetime(today.year, today.month, 1)
    last_month = first - datetime.timedelta(days=1)
    month = last_month.month
    year = last_month.year
    start_ts = int(datetime.datetime(year, month, 1).timestamp())
    end_ts = int(first.timestamp()) - 1
    
    data = existing_data if existing_data else []    
    
    total_mentions = 0
    for q in queries:
        encoded_query = urllib.parse.quote(q)
        url = f"https://hn.algolia.com/api/v1/search?query={encoded_query}&numericFilters=created_at_i>{start_ts},created_at_i<{end_ts}"
        
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            response = urllib.request.urlopen(req)
            result = json.loads(response.read().decode('utf-8'))
            total_mentions += result.get('nbHits', 0)
            time.sleep(0.1) # Be gentle with API
        except Exception as e:
            print(f"Error fetching HN data for {q} in {year}-{month:02d}: {e}")
    
    date_str = f"{year}-{month:02d}"
    
    found = False
    for d in data:
        if d.get('date') == date_str or d.get('year') == date_str: # fallback if 'year' was used previously
            d['mentions'] = total_mentions
            if 'year' in d: # update legacy key
                d['date'] = d.pop('year')
            found = True
            break
    if not found:
        data.append({
            'date': date_str,
            'mentions': total_mentions
        })
        
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

def fetch_cloudflare_radar(existing_data):
    token = os.environ.get('CLOUDFLARE_API_TOKEN')
    if not token:
        print("No CLOUDFLARE_API_TOKEN found, skipping Cloudflare Radar")
        return existing_data
        
    url = "https://api.cloudflare.com/client/v4/radar/http/timeseries_groups/os?name=main&location=US&dateRange=28d&deviceType=DESKTOP&botClass=LIKELY_HUMAN"
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
            
        data_dict = {d['date']: d for d in existing_data} if existing_data else {}
        for d in data:
            data_dict[d['date']] = d
            
        merged = list(data_dict.values())
        merged.sort(key=lambda x: x['date'])
        return merged
    except Exception as e:
        print(f"Error fetching Cloudflare data: {e}")
        return existing_data

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
    sc_existing = load_data('data/statcounter.json')
    sc_data = fetch_statcounter(sc_existing)
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
    cf_existing = load_data('data/cloudflare.json')
    cf_data = fetch_cloudflare_radar(cf_existing)
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
