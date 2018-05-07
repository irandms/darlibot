import feedparser

def find_episode(name, feedurl):
    feed = feedparser.parse(feedurl)
    for entry in feed.entries:
        if name in entry.title:
            return entry.links[0]['href']
    return None
