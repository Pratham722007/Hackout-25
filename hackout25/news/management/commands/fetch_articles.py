# news/management/commands/fetch_forest_news.py

import feedparser
from dateutil.parser import parse as parse_datetime
from django.core.management.base import BaseCommand
from news.models import Article

# Use HTTPS for forest-related RSS feeds - try multiple sources
FEED_URLS = [
    "https://news.mongabay.com/feed/",  # General Mongabay feed (environmental news)
    "https://www.sciencedaily.com/rss/earth_climate/forests_and_trees.xml",  # ScienceDaily forests
    "https://www.worldwildlife.org/initiatives/forests/feed",  # WWF forests
    "https://news.nationalgeographic.com/rss/",  # National Geographic
    "https://www.nature.com/subjects/forest-ecology/ncomms/rss",  # Nature Forest Ecology
    "https://www.eurekalert.org/rss/forestry.xml",  # EurekAlert forestry
]

class Command(BaseCommand):
    help = "Fetch latest forest news from Mongabay RSS and save to the DB (with debug)"

    def handle(self, *args, **options):
        total_imported = 0
        
        for feed_url in FEED_URLS:
            self.stdout.write(f"\n[INFO] Trying feed: {feed_url}")
            # 1) Parse the RSS feed
            feed = feedparser.parse(feed_url)

            # Debug: show feed title and number of entries
            self.stdout.write(f"[INFO] Feed title: {feed.feed.get('title', '—no title—')}")
            self.stdout.write(f"[INFO] Total entries fetched: {len(feed.entries)}\n")
            
            if len(feed.entries) == 0:
                self.stdout.write("[INFO] No entries found, trying next feed...\n")
                continue

            entries = feed.entries[:30]  # limit to 30 newest articles

            count = 0
            for idx, entry in enumerate(entries, start=1):
                # Debug: show available keys on the first entry (disabled in production)
                # if idx == 1:
                #     self.stdout.write(f"[DEBUG] Entry[0] keys: {list(entry.keys())}\n")

                title = entry.get('title', '').strip()
                link  = entry.get('link', '').strip()
                # some feeds use 'description', some 'summary'
                description = entry.get('description', entry.get('summary', '')).strip()

                # try thumbnail then media_content
                image_url = ''
                thumb = entry.get('media_thumbnail')
                if thumb and isinstance(thumb, list):
                    image_url = thumb[0].get('url', '').strip()
                elif entry.get('media_content'):
                    image_url = entry['media_content'][0].get('url', '').strip()
                
                # Use a default image if none found
                if not image_url:
                    image_url = 'https://via.placeholder.com/400x200/228B22/FFFFFF?text=Forest+News'

                # published or updated
                published_raw = entry.get('published') or entry.get('updated') or ''
                try:
                    published_dt = parse_datetime(published_raw)
                except Exception:
                    published_dt = None

                # Debug: show which fields passed (disabled in production)
                # self.stdout.write(
                #     f"[DEBUG][{idx}] title={'OK' if title else 'MISSING'} "
                #     f"link={'OK' if link else 'MISSING'} "
                #     f"image={'OK' if image_url else 'MISSING'} "
                #     f"pub_dt={'OK' if published_dt else 'MISSING'}"
                # )

                # Skip if essential fields are missing (title, link, published date)
                if not (title and link and published_dt):
                    # self.stdout.write(f"  → Skipping entry {idx}\n")
                    continue

                # Finally, save/update the Article
                obj, created = Article.objects.update_or_create(
                    link=link,
                    defaults={
                        'title':       title,
                        'description': description,
                        'image_url':   image_url,
                        'published':   published_dt,
                        'category':    'forest',
                    }
                )
                count += 1
                # self.stdout.write(f"  → {'Created' if created else 'Updated'} article #{idx}: {title}\n")
            
            total_imported += count
            self.stdout.write(f"[INFO] Imported {count} articles from this feed\n")
            
            # Continue to next feed to get more diverse content
            # We'll try all feeds to get maximum variety
            if total_imported >= 50:  # Stop after 50 articles to avoid too many
                break

        self.stdout.write(self.style.SUCCESS(f"\nTotal imported: {total_imported} forest articles"))
