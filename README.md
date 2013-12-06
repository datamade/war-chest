war-chest
=========

API for Chicago Aldermen's Campaign Funds

Installation
```console
pip install -r requirements.txt
```

Setting up the databse
```console
python candidates_scraper.py
python prime_db.py
python committee_scraper.py
sqlite3 war_chest.db < officeholders.sql
```

Usage
```console
python app.py
```

Navigate to [http://localhost:9999](http://localhost:9999)
