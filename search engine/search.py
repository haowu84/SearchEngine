from indexer import read_urls, read_offsets
from nltk.tokenize import RegexpTokenizer
from nltk.stem import PorterStemmer 
from nltk.corpus import stopwords
from heapq import heapify, nlargest, heappush
import pickle
import time
import eel

zone_weights = {0:1, 1:1.5, 2:2, 3:2.5}

def compute_scores(query,index):
    scores = dict()
    zones = dict()

    #compute the scores for docs weighted tf-idf 
    term = query[0]
    for post in index[term]:
        docid = post[0]
        scores[docid] = post[1] 
        zones[docid] = post[2]

    #only consider docs that contain all of query terms
    if len(query) > 1:
        for word in query[1:]:
            newscores = dict()
            for post in index[word]:
                docid = post[0]
                if docid in scores:
                    score = post[1] 
                    newscores[docid] = scores[docid] + score
                    zones[docid] = min(zones[docid], post[2])
            scores = newscores

    return scores, zones

def search(query):
    start = time.time()
    tokenizer = RegexpTokenizer('[a-zA-Z0-9]+')
    stemmer = PorterStemmer()
    stop_words = set(stopwords.words('english'))

    parsed_query = [ stemmer.stem(word) for word in tokenizer.tokenize(query.lower()) if word not in stop_words] #parse the query and remove stop words
    if len(parsed_query) != 0:
        query = parsed_query
    else:
        query = [ stemmer.stem(word) for word in tokenizer.tokenize(query.lower()) ]

    high_index = dict()
    low_index = dict()
    
    #construct an inverted index for the query 
    with open("combinedindex.txt", "r") as f:
        for term in query:
            f.seek(offsets[term])
            invertedlist = f.readline().split(":")
            term = invertedlist[0]
            postings = invertedlist[1].split("-")
            high_index[term] = eval(postings[0])
            low_index[term] = postings[1]
    
    query = sorted(query, key = lambda x: len(high_index[x])) #sort the query terms in increasing frequency

    scores, zones = compute_scores(query,high_index)

    heap = list()
    for k in scores:
        zone_weight = zone_weights[zones[k]]
        heap.append( ( (zone_weight, scores[k] * zone_weight) , k) )
    heapify(heap) #rank the docids in zone tiers and decreasing score (largest -> smallest)

    k = 10

    #drop to low tier if necessary
    if len(heap) < k:
        for term in query:
            low_index[term] = eval(low_index[term])
        query = sorted(query, key = lambda x: len(low_index[x]))
        scores, zones = compute_scores(query,low_index)
        for s in scores:
            zone_weight = zone_weights[zones[s]]
            heappush(heap, ( (zone_weight, scores[s] * zone_weight) , s) )

    print(time.time()-start)
    #print the top 10 results to the screen
    for n in nlargest(k, heap, key = lambda x: x[0]):
        eel.printResults(urls[n[1]])
    
        
@eel.expose       
def begin_search(text):
    search(text)

if __name__ == "__main__":
    urls = read_urls()
    offsets = read_offsets()
    
    eel.init("www")
    eel.start("main.html")
    
    
