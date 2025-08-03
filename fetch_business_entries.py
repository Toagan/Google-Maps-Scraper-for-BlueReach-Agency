import os
import sys
import pandas as pd
import requests
import json
import csv
import re
from pathlib import Path

def fetch_business_entries(api_key, query, lat, lon, zoom=13, max_pages=5):
    url = "https://google.serper.dev/maps"
    all_places = []
    for page in range(1, max_pages + 1):
        try:
            payload = json.dumps({
                "q": query,
                "hl": "de",
                "ll": f"@{lat},{lon},{zoom}z",
                "page": page
            })
            headers = {
                'X-API-KEY': api_key,
                'Content-Type': 'application/json'
            }

            response = requests.request("POST", url, headers=headers, data=payload)
            if response.status_code == 200:
                data = response.json()
                places = data.get('places', [])
                if not places:  # If no more results, break early
                    break
                all_places.extend(places)
            else:
                print(f"Error in API request for page {page}: Status code {response.status_code}")
                break
        except Exception as e:
            print(f"Error fetching data for page {page}: {str(e)}")
            break
    
    return all_places

def normalize_keyword(keyword):
    return re.sub(r'\W+', '_', keyword).lower()

def load_existing_place_ids(output_file):
    existing_ids = set()
    if output_file.exists():
        with open(output_file, mode='r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row['placeId']:
                    existing_ids.add(row['placeId'])
    return existing_ids

def main():
    try:
        print(f"Current working directory: {os.getcwd()}")
        print(f"Script location: {os.path.dirname(os.path.abspath(__file__))}")

        # Prompt for resume option
        resume = input("Would you like to resume from the last run? (yes/no): ").lower() == 'yes'
        
        paginations_above_100k = int(input("Enter the number of paginations for cities with population above 100k: "))
        paginations_10k_100k = int(input("Enter the number of paginations for cities with population between 10k and 100k: "))
        paginations_below_10k = int(input("Enter the number of paginations for cities with population below 10k: "))
        keyword = input("Enter the search keyword: ")
        api_key = input("Enter the API key: ")

        # File paths
        file_path = Path(__file__).parent / 'cities1000.txt'
        if not file_path.exists():
            print(f"Error: Cannot find {file_path}")
            print("Please ensure cities1000.txt is in the same directory as this script.")
            sys.exit(1)

        columns = [
            'geonameid', 'name', 'asciiname', 'alternatenames', 'latitude', 'longitude', 
            'feature_class', 'feature_code', 'country_code', 'cc2', 'admin1_code', 
            'admin2_code', 'admin3_code', 'admin4_code', 'population', 'elevation', 
            'dem', 'timezone', 'modification_date'
        ]

        print(f"Reading data from {file_path}...")
        cities = pd.read_csv(str(file_path), sep='\t', header=None, names=columns, low_memory=False)
        german_cities = cities[cities['country_code'] == 'DE']
        print(f"Found {len(german_cities)} German cities")

        german_cities = german_cities[['name', 'latitude', 'longitude', 'population']]
        german_cities = german_cities.sort_values(by='population', ascending=False)

        # Calculate total credits needed
        total_credits_needed = 0
        for _, city in german_cities.iterrows():
            if city['population'] >= 100000:
                total_credits_needed += 3 * paginations_above_100k
            elif 10000 <= city['population'] < 100000:
                total_credits_needed += 3 * paginations_10k_100k
            else:
                total_credits_needed += 3 * paginations_below_10k

        print(f"Estimated total credits needed: {total_credits_needed}")
        credits = int(input("Enter the maximum number of credits you want to spend: "))

        # Setup output file
        normalized_keyword = normalize_keyword(keyword)
        output_dir = Path(__file__).parent / 'output'
        output_dir.mkdir(exist_ok=True)
        output_file = output_dir / f'business_entries_{normalized_keyword}.csv'

        # Load existing progress
        unique_place_ids = load_existing_place_ids(output_file)
        print(f"Found {len(unique_place_ids)} existing entries")

        # If resuming, find the last processed city
        last_processed_city = None
        if resume and output_file.exists():
            try:
                with open(output_dir / 'last_processed.txt', 'r') as f:
                    last_processed_city = int(f.read().strip())
                print(f"Resuming from city index: {last_processed_city}")
            except:
                print("No valid resume point found, starting from beginning")
                last_processed_city = None

        fields = ['placeId', 'title', 'address', 'latitude', 'longitude', 'rating', 
                 'ratingCount', 'primaryType', 'types', 'website', 'phoneNumber']

        # Only create new file if not resuming
        if not resume or not output_file.exists():
            with open(output_file, mode='w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=fields)
                writer.writeheader()

        # Process cities
        credits_used = 0
        if resume and last_processed_city is not None:
            credits_used = last_processed_city * 9  # Estimate credits used based on last position
        
        total_cities = len(german_cities)
        
        # Skip cities if resuming
        start_index = last_processed_city + 1 if last_processed_city is not None else 0
        
        for index, city in german_cities.iloc[start_index:].iterrows():
            name, lat, lon, population = city['name'], city['latitude'], city['longitude'], city['population']
            
            if population >= 100000:
                max_pages = paginations_above_100k
            elif 10000 <= population < 100000:
                max_pages = paginations_10k_100k
            else:
                max_pages = paginations_below_10k

            credits_needed = 3 * max_pages
            if credits_used + credits_needed > credits:
                print(f"\nCredit limit reached. Stopping after processing {index} cities.")
                break

            print(f"\nProcessing city {index + 1}/{total_cities}: {name}")
            print(f"Population: {population:,}")
            print(f"Credits needed: {credits_needed}")
            
            business_entries = fetch_business_entries(api_key, keyword, lat, lon, max_pages=max_pages)
            new_entries = 0
            
            if business_entries:
                with open(output_file, mode='a', newline='', encoding='utf-8') as f:
                    writer = csv.DictWriter(f, fieldnames=fields)
                    for entry in business_entries:
                        place_id = entry.get('placeId')
                        if place_id and place_id not in unique_place_ids:
                            unique_place_ids.add(place_id)
                            new_entries += 1
                            writer.writerow({
                                'placeId': place_id,
                                'title': entry.get('title'),
                                'address': entry.get('address'),
                                'latitude': entry.get('latitude'),
                                'longitude': entry.get('longitude'),
                                'rating': entry.get('rating'),
                                'ratingCount': entry.get('ratingCount'),
                                'primaryType': entry.get('type'),
                                'types': ", ".join(entry.get('types', [])),
                                'website': entry.get('website'),
                                'phoneNumber': entry.get('phoneNumber')
                            })

            # Save the last processed city index
            with open(output_dir / 'last_processed.txt', 'w') as f:
                f.write(str(index))

            credits_used += credits_needed
            print(f"Found {new_entries} new unique entries")
            print(f"Total unique entries so far: {len(unique_place_ids)}")
            print(f"Credits used: {credits_used}/{credits}")

        print("\nScript completed successfully!")
        print(f"Total unique entries found: {len(unique_place_ids)}")
        print(f"Total credits used: {credits_used}")
        print(f"Results saved to: {output_file}")

    except KeyboardInterrupt:
        print("\nScript interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\nAn error occurred: {str(e)}")
        import traceback
        print(traceback.format_exc())
        sys.exit(1)

        
if __name__ == '__main__':
    main()