import requests
import math
import pymongo
from copy import deepcopy

client = pymongo.MongoClient('localhost', 27017)
db = client.itunes_reviews

app_ids = [
    '550842012', # Wanelo
    '470412147', # Poshmark
    '393328150', # Sephora to Go
    '836767708', # Wayfair
    '499978982', # Polyvore
    '567647280', # Touch of Modern: Shopping
    '386656478', # Express
    '339041767', # Abercrombie & Fitch
    '452209341', # Aeropostale
    '341036067', # Macys
    '365886172', # Forever 21
    '651508224', # Nasty Gal
    '334876990', # Gucci Style
    '589351740', # H&M
    '920017327', # Charlotte Russe
    '358821736', # Urban Outfitters
    '899156093', # Spring
    '383915209', # Hollister
]

def main():
    # Example URL: https://itunes.apple.com/rss/customerreviews/page=1/id=454638411/sortby=mosthelpful/json?l=en&cc=us
    base_url = "https://itunes.apple.com/rss/customerreviews/"
    country_code = "us"
    language = "en"
    sort_by = "mosthelpful"
    querystring = "sortby=%s/json?l=%s&cc=%s" % (sort_by, language, country_code)
    
    for app_id in app_ids:
        for page in range(1, 11):
            url = '%spage=%s/id=%s/%s' % (base_url, page, app_id, querystring)
            response = requests.get(url)
            
            print url
            
            if response.status_code > 400:
                print 'Failed Request: %s with status code: %s' % (url, response.status_code)
                continue
            
            data = response.json()
            
            if 'entry' in data['feed'] and len(data['feed']['entry']) > 1:
                reviews = {
                    'app': {
                        'name': data['feed']['entry'][0]['im:name']['label'],
                        'price': data['feed']['entry'][0]['im:price']['attributes']['amount'],
                        'id': data['feed']['entry'][0]['id']['attributes']['im:id'],
                        'category': data['feed']['entry'][0]['category']['attributes']['label'],
                        'release_date': data['feed']['entry'][0]['im:releaseDate']['label']
                    },
                    'reviews': [{
                            'app_version': entry['im:version']['label'],
                            'rating': entry['im:rating']['label'],
                            'id': entry['id']['label'],
                            'title': entry['title']['label'],
                            'content': entry['content']['label'],
                            'vote_sum': entry['im:voteSum']['label'],
                            'vote_count': entry['im:voteCount']['label']
                        } for entry in data['feed']['entry'][1:]]
                }

                for review in reviews['reviews']:
                    review['downvotes'] = math.ceil((float(review['vote_count']) - float(review['vote_sum'])) / 2)
                    review['upvotes'] = int(review['vote_count']) - int(review['downvotes'])

                found = db.reviews.find({'app.id': reviews['app']['id']})

                print 'Found: ' + str(found.count())

                if found.count() > 0:
                    print 'Reviews: ' + str(len(found[0]['reviews']))

                    existing_review = deepcopy(found[0])
                    existing_review['reviews'].extend(reviews['reviews'])
                    db.reviews.replace_one({'app.id': reviews['app']['id']}, existing_review)
                else:
                    db.reviews.insert_one(reviews)

                print 'Document Count: ' + str(db.reviews.find().count())
                print 'Review Count: ' + str(len([r['reviews'] for r in db.reviews.find()]))
main()