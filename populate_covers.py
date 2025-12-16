import time
import requests
from app import create_app, db
from app.models import Book
import random

def populate_covers():
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    api_url = "https://bookcover.longitood.com/bookcover"

    app = create_app()
    with app.app_context():

        from sqlalchemy import or_
        books = Book.query.filter(or_(Book.image_url == None, Book.image_url == '')).all()
        
        print(f"Found {len(books)} books to check.")
        
        updated_count = 0
        
        for i, book in enumerate(books):
            # If it already has an image and we just assume we want to fill NULLs, 
            # we might skip. But user said "update all". However, typically we only need to fill missing ones.
            # I will prioritize filling missing ones, but if the user ran the SQL to clear them, they are all missing.
            
            try:
                print(f"Searching for book ID {book.id}...", end=' ', flush=True)
            except:
                print(f"Searching for book ID {book.id}...", end=' ', flush=True)
            
            try:
                params = {
                    'book_title': book.title,
                    'author_name': book.author
                }
                
                # API call
                r = requests.get(api_url, params=params, headers=headers)
                
                if r.status_code == 200:
                    data = r.json()
                    img_url = data.get('url')
                    
                    if img_url:
                        book.image_url = img_url
                        updated_count += 1
                        print(f"Found! -> {img_url}")
                    else:
                        print("Not found (API returned no URL).")
                else:
                    print(f"Failed (Status {r.status_code})")

            except Exception as e:
                print(f"Error: {e}")
            
            # Commit every 5 updates to save progress
            if updated_count > 0 and updated_count % 5 == 0:
                db.session.commit()

            # Sleep to be polite to the API
            time.sleep(0.5)
        
        # Commit remaining changes
        if updated_count > 0:
            db.session.commit()
            print(f"\nSuccess! Updated {updated_count} books.")
        else:
            print("\nNo books were updated.")

if __name__ == '__main__':
    populate_covers()
