from collections import defaultdict, Counter
from bs4 import BeautifulSoup
from nltk.tokenize import RegexpTokenizer
from nltk.stem import PorterStemmer 
from urllib.parse import urldefrag
from math import log
import glob
import json
import pickle


zones = {'title':3,'h1':2,'h2':2,'h3':2,'b':1,'strong':1}
partial_indexes = ["index1.txt","index2.txt","index3.txt"]


class posting:
    def __init__(self, docid, tfidf, zone = 0):
        self.docid = docid
        self.tfidf = tfidf
        self.zone = zone


def save_urls():
    url_file = open("url.pickle","wb")
    pickle.dump(dict((y,x) for x,y in urls.items()), url_file)
    url_file.close()

def read_urls():
    url_file = open("url.pickle","rb")
    url_dict = pickle.load(url_file)
    url_file.close()
    return url_dict

def save_offsets():
    offset_file = open("offset.pickle","wb")
    pickle.dump(offsets, offset_file)
    offset_file.close()

def read_offsets():
    offset_file = open("offset.pickle","rb")
    offset_dict = pickle.load(offset_file)
    offset_file.close()
    return offset_dict


def parse(document, docid, index):
    soup = BeautifulSoup(document, "lxml") #get the html content
    tokenizer = RegexpTokenizer('[a-zA-Z0-9]+') #set up the regular expression based tokenizer 
    stemmer = PorterStemmer() #set up the porter stemmer 

    for tag in soup.find_all(['script', 'style']):
        tag.extract()

    tokens = [stemmer.stem(word) for word in tokenizer.tokenize(soup.get_text().lower())] #tokenize and stem every word in the page

    count = Counter(tokens) #make a frequency dictionary of tokens in the doc

    #find the zones in the document
    word_zones = defaultdict(int)
    for line in soup.find_all(['title','h1','h2','h3','strong','b']):
        for word in tokenizer.tokenize(line.text.lower()):
            word = stemmer.stem(word)
            zone = zones[line.name]
            if word not in word_zones:
                word_zones[word] = zone
            else:
                #choose highest word zone
                if zone > word_zones[word]:
                    word_zones[word] = zone

    #initialize the postings and add them to the index
    for token, frequency in count.items():
        p = posting(docid, frequency)
        if token in word_zones:
            p.zone = word_zones[token]
        index[token].append(p)


def calculate_tfidf(docs_size, postings): 
    docs_with_term = len(postings) 
    for post in postings:
        tf = 1 + log(post[1],10) #term frequency
        idf = log(docs_size/docs_with_term,10) #inverse document frequency: total number of documents/number of documents that contain the term
        post[1] = round(tf * idf,3) #tf.idf

#split the posting lists into 2 tiers
def champion_list(posting):
    high_list = list()
    low_list = list()
    for post in posting:
        if post[2] != 0:
            high_list.append(post)
        else:
            low_list.append(post)
    return str(high_list) + "-" + str(low_list)


def offload(file,index):
    with open (file,"w") as f:
        for k,v in index.items():
            f.write(str(k)+':')
            temp = list()
            for i in v:
                temp.append([i.docid, i.tfidf, i.zone])
            f.write(str(temp)+'\n')


def binary_merge(file1,file2,output_file, final, N):
    with open(file1,"r") as f1, open(file2,"r") as f2, open(output_file,"w") as output:
        line1 = f1.readline()
        line2 = f2.readline()
        while line1 and line2:
            invertedlist1 = line1.split(":")
            invertedlist2 = line2.split(":")
            term1 = invertedlist1[0]
            term2 = invertedlist2[0]
            postings1 = eval(invertedlist1[1])
            postings2 = eval(invertedlist2[1])
            line = ""
            if term1 == term2:
                postings1.extend(postings2)
                postings = str(postings1)
                if final:
                    calculate_tfidf(N, postings1)
                    postings = champion_list(postings1)
                line = str(term1)+':'+postings+'\n'
                line1 = f1.readline()
                line2 = f2.readline()
            elif term1 < term2:
                line = line1
                postings = str(postings1)
                if final:
                    calculate_tfidf(N, postings1)
                    postings = champion_list(postings1)
                    line = str(term1)+':'+postings+'\n'
                line1 = f1.readline()
            else:
                line = line2
                postings = str(postings2)
                if final:
                    calculate_tfidf(N, postings2)
                    postings = champion_list(postings2)
                    line = str(term2)+':'+postings+'\n'
                line2 = f2.readline()

            output.write(line)


def build_index():
    index = defaultdict(list)
    docid = 0
    file_no = 0
    #Traversing all files in the direcotry recursively
    for path in glob.iglob(r'/Users/haowu/Desktop/DEV/**/*.json', recursive=True):
        with open(path, encoding = "utf-8") as file:
            data = json.load(file) #load the json file

        url = urldefrag(data['url'])[0] #defrag the url
        if url in urls:
            continue
        
        docid = docid + 1 

        urls[url] = docid  #map a unique id to the document

        parse(data['content'], docid, index) 

        if docid == 18000 or docid == 36000:
            offload(partial_indexes[file_no],dict(sorted(index.items()))) #when the limit is reached, sort and write the index to disk
            file_no += 1
            index.clear()

    offload(partial_indexes[file_no],dict(sorted(index.items())))

    #merge the partial index
    docs_size = len(urls)
    binary_merge("index1.txt","index2.txt","index4.txt",False,docs_size)
    binary_merge("index4.txt","index3.txt","combinedindex.txt",True,docs_size)
    
    #map a byte offset to each term
    with open("combinedindex.txt","r") as f:
        line = "."
        while line:
            offset = f.tell()
            line = f.readline()
            if len(line) != 0:
                offsets[line.split(":")[0]] = offset


if __name__ == "__main__":   
    urls = dict()
    offsets = dict()
    build_index()
    save_urls()
    save_offsets()
    
