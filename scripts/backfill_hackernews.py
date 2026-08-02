import json
import urllib.request
import urllib.parse
import time
import datetime
import os

def backfill():
    queries = [
        '"year of the linux desktop"',
        '"year of desktop linux"',
        '"year of linux on the desktop"',
        '"linux desktop year"',
        '"year of linux"',
        'yotld'
    ]
    start_year = 2009
    current_date = datetime.datetime.now()
    
    data = []
    
    for year in range(start_year, current_date.year + 1):
        for month in range(1, 13):
            if year == current_date.year and month > current_date.month:
                break
                
            start_ts = int(datetime.datetime(year, month, 1).timestamp())
            if month == 12:
                end_ts = int(datetime.datetime(year + 1, 1, 1).timestamp()) - 1
            else:
                end_ts = int(datetime.datetime(year, month + 1, 1).timestamp()) - 1
            
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
            data.append({
                'date': date_str,
                'mentions': total_mentions
            })
            print(f"Processed month {date_str}")
        
    os.makedirs('data', exist_ok=True)
    with open('data/hackernews.json', 'w') as f:
        json.dump(data, f, indent=2)
        
    print("Hacker News backfill complete. Total entries:", len(data))

if __name__ == '__main__':
    backfill()
