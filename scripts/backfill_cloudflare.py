import json
import urllib.request
import os

def backfill():
    token = os.environ.get('CLOUDFLARE_API_TOKEN')
    if not token:
        print("No CLOUDFLARE_API_TOKEN found, skipping Cloudflare Radar backfill")
        return
        
    # Backfill with 52 weeks (max possible via this endpoint without pagination)
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
            
        os.makedirs('data', exist_ok=True)
        with open('data/cloudflare.json', 'w') as f:
            json.dump(data, f, indent=2)
            
        print("Cloudflare backfill complete. Total entries:", len(data))
    except Exception as e:
        print(f"Error fetching Cloudflare data: {e}")

if __name__ == '__main__':
    backfill()
