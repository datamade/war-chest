# 1. Scrape all people who are candidates in Chicago
python candidates_scraper.py

# 2. Add active candidates and pupa_ids
sqlite3 war_chest.db < officeholders.sql

# 3. Scrape all commitees and their officers active in Chicago
python committee_scraper.py
python officer_scraper.py

# 4. Find cases where people seem to have more than one candidate record
# and dump them out for manual matching
python find_duplicate_people.py


