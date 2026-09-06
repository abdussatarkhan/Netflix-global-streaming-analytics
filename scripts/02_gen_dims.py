#!/usr/bin/env python3
import os, sys
sys.stdout.reconfigure(encoding='utf-8')
import pandas as pd
import numpy as np

def generate_dimensions(output_dir='../data'):
    os.makedirs(output_dir, exist_ok=True)
    np.random.seed(42)

    regions = [
        {'region_id': 1, 'region_code': 'UCAN', 'region_name': 'United States and Canada', 'hq_location': 'Los Gatos, CA', 'currency_code': 'USD'},
        {'region_id': 2, 'region_code': 'EMEA', 'region_name': 'Europe, Middle East and Africa', 'hq_location': 'Amsterdam, Netherlands', 'currency_code': 'EUR'},
        {'region_id': 3, 'region_code': 'LATAM', 'region_name': 'Latin America', 'hq_location': 'Sao Paulo, Brazil', 'currency_code': 'BRL'},
        {'region_id': 4, 'region_code': 'APAC', 'region_name': 'Asia Pacific', 'hq_location': 'Singapore', 'currency_code': 'USD'}
    ]
    df_region = pd.DataFrame(regions)
    df_region.to_csv(os.path.join(output_dir, 'dim_region.csv'), index=False)
    print("[+] [02] Created dim_region.csv")

    countries = [
        {'country_id': 1, 'region_id': 1, 'country_code': 'US', 'country_name': 'United States', 'tier': 'Tier 1', 'broadband_penetration_pct': 92.5, 'sub_base_weight': 0.32, 'avg_arpu_base': 16.50},
        {'country_id': 2, 'region_id': 1, 'country_code': 'CA', 'country_name': 'Canada', 'tier': 'Tier 1', 'broadband_penetration_pct': 91.0, 'sub_base_weight': 0.05, 'avg_arpu_base': 14.80},
        {'country_id': 3, 'region_id': 2, 'country_code': 'GB', 'country_name': 'United Kingdom', 'tier': 'Tier 1', 'broadband_penetration_pct': 95.0, 'sub_base_weight': 0.07, 'avg_arpu_base': 12.80},
        {'country_id': 4, 'region_id': 2, 'country_code': 'DE', 'country_name': 'Germany', 'tier': 'Tier 1', 'broadband_penetration_pct': 90.0, 'sub_base_weight': 0.06, 'avg_arpu_base': 12.20},
        {'country_id': 5, 'region_id': 2, 'country_code': 'FR', 'country_name': 'France', 'tier': 'Tier 1', 'broadband_penetration_pct': 88.0, 'sub_base_weight': 0.05, 'avg_arpu_base': 12.00},
        {'country_id': 6, 'region_id': 2, 'country_code': 'ES', 'country_name': 'Spain', 'tier': 'Tier 2', 'broadband_penetration_pct': 87.0, 'sub_base_weight': 0.03, 'avg_arpu_base': 10.90},
        {'country_id': 7, 'region_id': 2, 'country_code': 'IT', 'country_name': 'Italy', 'tier': 'Tier 2', 'broadband_penetration_pct': 82.0, 'sub_base_weight': 0.03, 'avg_arpu_base': 10.50},
        {'country_id': 8, 'region_id': 2, 'country_code': 'NL', 'country_name': 'Netherlands', 'tier': 'Tier 1', 'broadband_penetration_pct': 97.0, 'sub_base_weight': 0.02, 'avg_arpu_base': 13.10},
        {'country_id': 9, 'region_id': 2, 'country_code': 'PL', 'country_name': 'Poland', 'tier': 'Tier 2', 'broadband_penetration_pct': 84.0, 'sub_base_weight': 0.02, 'avg_arpu_base': 8.50},
        {'country_id': 10, 'region_id': 2, 'country_code': 'SA', 'country_name': 'Saudi Arabia', 'tier': 'Tier 2', 'broadband_penetration_pct': 98.0, 'sub_base_weight': 0.015, 'avg_arpu_base': 11.50},
        {'country_id': 11, 'region_id': 2, 'country_code': 'AE', 'country_name': 'United Arab Emirates', 'tier': 'Tier 1', 'broadband_penetration_pct': 99.0, 'sub_base_weight': 0.01, 'avg_arpu_base': 12.50},
        {'country_id': 12, 'region_id': 2, 'country_code': 'ZA', 'country_name': 'South Africa', 'tier': 'Tier 3', 'broadband_penetration_pct': 68.0, 'sub_base_weight': 0.01, 'avg_arpu_base': 6.80},
        {'country_id': 13, 'region_id': 3, 'country_code': 'BR', 'country_name': 'Brazil', 'tier': 'Tier 2', 'broadband_penetration_pct': 81.0, 'sub_base_weight': 0.08, 'avg_arpu_base': 7.80},
        {'country_id': 14, 'region_id': 3, 'country_code': 'MX', 'country_name': 'Mexico', 'tier': 'Tier 2', 'broadband_penetration_pct': 76.0, 'sub_base_weight': 0.06, 'avg_arpu_base': 8.20},
        {'country_id': 15, 'region_id': 3, 'country_code': 'AR', 'country_name': 'Argentina', 'tier': 'Tier 3', 'broadband_penetration_pct': 80.0, 'sub_base_weight': 0.02, 'avg_arpu_base': 5.40},
        {'country_id': 16, 'region_id': 3, 'country_code': 'CO', 'country_name': 'Colombia', 'tier': 'Tier 3', 'broadband_penetration_pct': 70.0, 'sub_base_weight': 0.015, 'avg_arpu_base': 6.20},
        {'country_id': 17, 'region_id': 3, 'country_code': 'CL', 'country_name': 'Chile', 'tier': 'Tier 2', 'broadband_penetration_pct': 88.0, 'sub_base_weight': 0.01, 'avg_arpu_base': 8.60},
        {'country_id': 18, 'region_id': 4, 'country_code': 'JP', 'country_name': 'Japan', 'tier': 'Tier 1', 'broadband_penetration_pct': 93.0, 'sub_base_weight': 0.04, 'avg_arpu_base': 11.20},
        {'country_id': 19, 'region_id': 4, 'country_code': 'KR', 'country_name': 'South Korea', 'tier': 'Tier 1', 'broadband_penetration_pct': 97.0, 'sub_base_weight': 0.035, 'avg_arpu_base': 10.40},
        {'country_id': 20, 'region_id': 4, 'country_code': 'IN', 'country_name': 'India', 'tier': 'Tier 3', 'broadband_penetration_pct': 55.0, 'sub_base_weight': 0.05, 'avg_arpu_base': 3.60},
        {'country_id': 21, 'region_id': 4, 'country_code': 'AU', 'country_name': 'Australia', 'tier': 'Tier 1', 'broadband_penetration_pct': 91.0, 'sub_base_weight': 0.025, 'avg_arpu_base': 13.90},
        {'country_id': 22, 'region_id': 4, 'country_code': 'ID', 'country_name': 'Indonesia', 'tier': 'Tier 3', 'broadband_penetration_pct': 62.0, 'sub_base_weight': 0.015, 'avg_arpu_base': 4.50},
        {'country_id': 23, 'region_id': 4, 'country_code': 'TH', 'country_name': 'Thailand', 'tier': 'Tier 3', 'broadband_penetration_pct': 74.0, 'sub_base_weight': 0.01, 'avg_arpu_base': 5.80},
        {'country_id': 24, 'region_id': 4, 'country_code': 'PH', 'country_name': 'Philippines', 'tier': 'Tier 3', 'broadband_penetration_pct': 65.0, 'sub_base_weight': 0.01, 'avg_arpu_base': 4.90}
    ]
    df_country = pd.DataFrame(countries)
    df_country.to_csv(os.path.join(output_dir, 'dim_country.csv'), index=False)
    print("[+] [02] Created dim_country.csv")

    plans = [
        {'plan_id': 1, 'plan_code': 'MOBILE', 'plan_name': 'Mobile-Only Plan', 'monthly_price_usd': 4.99, 'simultaneous_streams': 1, 'max_resolution': '480p SD', 'is_ad_supported': 0, 'has_downloads': 1, 'allows_extra_members': 0, 'launched_year': 2019},
        {'plan_id': 2, 'plan_code': 'BASIC', 'plan_name': 'Basic Standard Def', 'monthly_price_usd': 9.99, 'simultaneous_streams': 1, 'max_resolution': '720p HD', 'is_ad_supported': 0, 'has_downloads': 1, 'allows_extra_members': 0, 'launched_year': 2014},
        {'plan_id': 3, 'plan_code': 'STD_ADS', 'plan_name': 'Standard with Ads', 'monthly_price_usd': 6.99, 'simultaneous_streams': 2, 'max_resolution': '1080p FHD', 'is_ad_supported': 1, 'has_downloads': 1, 'allows_extra_members': 0, 'launched_year': 2022},
        {'plan_id': 4, 'plan_code': 'STANDARD', 'plan_name': 'Standard Ad-Free', 'monthly_price_usd': 15.49, 'simultaneous_streams': 2, 'max_resolution': '1080p FHD', 'is_ad_supported': 0, 'has_downloads': 1, 'allows_extra_members': 1, 'launched_year': 2014},
        {'plan_id': 5, 'plan_code': 'PREMIUM', 'plan_name': 'Premium 4K HDR + Spatial', 'monthly_price_usd': 22.99, 'simultaneous_streams': 4, 'max_resolution': '4K UHD + HDR', 'is_ad_supported': 0, 'has_downloads': 1, 'allows_extra_members': 2, 'launched_year': 2015}
    ]
    df_plan = pd.DataFrame(plans)
    df_plan.to_csv(os.path.join(output_dir, 'dim_plan.csv'), index=False)
    print("[+] [02] Created dim_plan.csv")

    devices = [
        {'device_id': 1, 'device_type': 'Smart TV', 'device_category': 'Living Room', 'stream_share_pct': 48.0, 'avg_bitrate_mbps': 14.5},
        {'device_id': 2, 'device_type': 'Connected TV (Roku/Apple TV/FireTV)', 'device_category': 'Living Room', 'stream_share_pct': 22.0, 'avg_bitrate_mbps': 12.8},
        {'device_id': 3, 'device_type': 'Mobile Phone (iOS/Android)', 'device_category': 'Handheld', 'stream_share_pct': 16.0, 'avg_bitrate_mbps': 4.5},
        {'device_id': 4, 'device_type': 'Tablet (iPad/Android Tab)', 'device_category': 'Handheld', 'stream_share_pct': 6.0, 'avg_bitrate_mbps': 6.2},
        {'device_id': 5, 'device_type': 'Web Browser (PC/Mac/Chromebook)', 'device_category': 'Desktop', 'stream_share_pct': 5.0, 'avg_bitrate_mbps': 8.0},
        {'device_id': 6, 'device_type': 'Gaming Console (PS5/Xbox)', 'device_category': 'Living Room', 'stream_share_pct': 3.0, 'avg_bitrate_mbps': 11.5}
    ]
    df_device = pd.DataFrame(devices)
    df_device.to_csv(os.path.join(output_dir, 'dim_device.csv'), index=False)
    print("[+] [02] Created dim_device.csv")

    genres = ['Drama', 'Sci-Fi & Fantasy', 'Thriller & Mystery', 'Comedy', 'Action & Adventure', 'Crime & Docuseries', 'Romance', 'Animation & Anime', 'Horror', 'Reality TV & Lifestyle']
    types = ['TV Series', 'Movie', 'Docuseries', 'Animation', 'Stand-up Comedy', 'Live Event']
    languages = ['English', 'Spanish', 'Korean', 'Japanese', 'French', 'Hindi', 'German', 'Portuguese', 'Arabic']
    
    anchor_titles = [
        ('Squid Game', 'TV Series', 'Sci-Fi & Fantasy', 'Korean', 2021, 21.4, 8.0, 9, 1),
        ('Stranger Things (Season 4)', 'TV Series', 'Sci-Fi & Fantasy', 'English', 2022, 270.0, 8.7, 9, 1),
        ('Wednesday', 'TV Series', 'Comedy', 'English', 2022, 35.0, 8.1, 8, 1),
        ('Red Notice', 'Movie', 'Action & Adventure', 'English', 2021, 200.0, 6.3, 1, 1),
        ('Glass Onion: A Knives Out Mystery', 'Movie', 'Thriller & Mystery', 'English', 2022, 40.0, 7.1, 1, 1),
        ('The Crown (Season 5-6)', 'TV Series', 'Drama', 'English', 2022, 130.0, 8.6, 20, 1),
        ('Bridgerton (Season 2-3)', 'TV Series', 'Romance', 'English', 2022, 140.0, 7.4, 16, 1),
        ('Money Heist: Korea', 'TV Series', 'Crime & Docuseries', 'Korean', 2022, 45.0, 6.8, 12, 1),
        ('Lupin (Part 3)', 'TV Series', 'Thriller & Mystery', 'French', 2023, 30.0, 7.5, 7, 1),
        ('One Piece (Live Action)', 'TV Series', 'Action & Adventure', 'English', 2023, 138.0, 8.3, 8, 1),
        ('Baby Reindeer', 'TV Series', 'Drama', 'English', 2024, 15.0, 7.8, 7, 1),
        ('The Night Agent', 'TV Series', 'Thriller & Mystery', 'English', 2023, 25.0, 7.5, 10, 1),
        ('Extraction 2', 'Movie', 'Action & Adventure', 'English', 2023, 70.0, 7.0, 1, 1),
        ('Leave the World Behind', 'Movie', 'Thriller & Mystery', 'English', 2023, 40.0, 6.5, 1, 1),
        ('Fool Me Once', 'TV Series', 'Thriller & Mystery', 'English', 2024, 20.0, 6.8, 8, 1),
        ('Society of the Snow', 'Movie', 'Drama', 'Spanish', 2023, 65.0, 7.8, 1, 1),
        ('Avatar: The Last Airbender', 'TV Series', 'Action & Adventure', 'English', 2024, 120.0, 7.2, 8, 1),
        ('3 Body Problem', 'TV Series', 'Sci-Fi & Fantasy', 'English', 2024, 160.0, 7.6, 8, 1),
        ('Formula 1: Drive to Survive', 'Docuseries', 'Crime & Docuseries', 'English', 2021, 28.0, 8.5, 30, 1),
        ('Beef', 'TV Series', 'Comedy', 'English', 2023, 35.0, 8.0, 10, 1),
        ('Culinary Class Wars', 'Reality TV & Lifestyle', 'Reality TV & Lifestyle', 'Korean', 2024, 18.0, 8.4, 12, 1),
        ('Jake Paul vs. Mike Tyson (Live)', 'Live Event', 'Action & Adventure', 'English', 2024, 50.0, 6.2, 1, 1),
        ('Beverly Hills Cop: Axel F', 'Movie', 'Comedy', 'English', 2024, 150.0, 6.5, 1, 1),
        ('Squid Game (Season 2)', 'TV Series', 'Sci-Fi & Fantasy', 'Korean', 2024, 100.0, 8.2, 7, 1),
        ('The Diplomat (Season 2)', 'TV Series', 'Drama', 'English', 2024, 45.0, 8.0, 6, 1)
    ]
    
    content_list = []
    content_id = 1
    
    for item in anchor_titles:
        title, c_type, genre, lang, rel_yr, budget, rating, eps, is_orig = item
        content_list.append({
            'content_id': content_id,
            'title_name': title,
            'content_type': c_type,
            'genre': genre,
            'original_language': lang,
            'release_year': rel_yr,
            'production_budget_m_usd': budget,
            'imdb_rating': rating,
            'episodes_count': eps,
            'is_netflix_original': is_orig,
            'content_tier': 'Blockbuster Tentpole' if budget > 80 else ('Mid-Tier Hit' if budget > 25 else 'Core Catalog')
        })
        content_id += 1
        
    adjectives = ['Dark', 'Silent', 'Golden', 'Hidden', 'Infinite', 'Midnight', 'Crimson', 'Lost', 'Electric', 'Dangerous', 'Secret', 'Eternal', 'Shattered', 'Quantum', 'Forbidden', 'Royal', 'Wild', 'Shadow', 'Neon', 'Last']
    nouns = ['Mirror', 'Empire', 'Legacy', 'Heist', 'Kingdom', 'Protocol', 'Code', 'Horizon', 'Syndicate', 'Echoes', 'Chronicles', 'Game', 'Project', 'Detective', 'City', 'Signal', 'Dynasty', 'Island', 'Voyage', 'Frontier']
    
    while content_id <= 400:
        c_type = np.random.choice(types, p=[0.45, 0.30, 0.12, 0.08, 0.03, 0.02])
        genre = np.random.choice(genres)
        lang = np.random.choice(languages, p=[0.45, 0.15, 0.12, 0.08, 0.05, 0.05, 0.04, 0.03, 0.03])
        rel_yr = int(np.random.choice([2021, 2022, 2023, 2024, 2025], p=[0.15, 0.20, 0.25, 0.25, 0.15]))
        title_name = f"{np.random.choice(adjectives)} {np.random.choice(nouns)}"
        if np.random.rand() > 0.6:
            title_name += f": Chapter {np.random.randint(2, 5)}"
            
        is_orig = 1 if np.random.rand() > 0.3 else 0
        eps = 1 if c_type in ['Movie', 'Stand-up Comedy', 'Live Event'] else int(np.random.randint(6, 18))
        budget = round(float(np.random.lognormal(mean=2.8, sigma=0.8)), 1)
        budget = max(2.0, min(budget, 220.0))
        rating = round(float(np.random.normal(loc=7.1, scale=0.9)), 1)
        rating = max(4.2, min(rating, 9.4))
        
        tier = 'Blockbuster Tentpole' if budget > 80 else ('Mid-Tier Hit' if budget > 25 else 'Core Catalog')
        
        content_list.append({
            'content_id': content_id,
            'title_name': title_name,
            'content_type': c_type,
            'genre': genre,
            'original_language': lang,
            'release_year': rel_yr,
            'production_budget_m_usd': budget,
            'imdb_rating': rating,
            'episodes_count': eps,
            'is_netflix_original': is_orig,
            'content_tier': tier
        })
        content_id += 1
        
    df_content = pd.DataFrame(content_list)
    df_content.to_csv(os.path.join(output_dir, 'dim_content.csv'), index=False)
    print(f"[+] [02] Created dim_content.csv with {len(df_content)} titles")

if __name__ == '__main__':
    base_dir = os.path.dirname(os.path.abspath(__file__))
    generate_dimensions(output_dir=os.path.join(base_dir, '..', 'data'))
