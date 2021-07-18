import re
import difflib
from urllib.parse import urlparse, urljoin, urldefrag
from collections import defaultdict
from bs4 import BeautifulSoup

domains = [".ics.uci.edu", ".cs.uci.edu", ".informatics.uci.edu", ".stat.uci.edu", "today.uci.edu"]
crawled_set = set()
crawled_list = list()
word_dict = dict()
parent = dict()
child = defaultdict(set)
ban = set()

#Check the similairty ratio between 2 documents 
def check(text1,text2):
    return difflib.SequenceMatcher(None, text1, text2).ratio()

def quick_check(text1,text2):
    return difflib.SequenceMatcher(None, text1, text2).quick_ratio()

#Return a list of websites to be added to the frontier
def scraper(url, resp):
    links = extract_next_links(url, resp)
    return [link for link in links if is_valid(link)]

def extract_next_links(url, resp):
    scrapping = list()

    if resp.status == 200 and url not in crawled_set and is_valid(url):
        soup = BeautifulSoup(resp.raw_response.content, 'html.parser')
        word_string = soup.get_text()
        word_dict[url] = word_string

        #Duplicate page elimination 
        ratio = 0
        if crawled_list:
            previous = crawled_list[-1]
            ratio = check(word_dict[previous], word_string)
            if ratio > 0.9:
                if url not in ban:
                    ban.add(url)
                if previous not in ban:
                    ban.add(previous)
                if url in parent and previous in parent and parent[url] == parent[previous] and parent[url] in child:
                    for c in child[parent[url]]:
                        if c not in ban and quick_check(c,url) > 0.9:
                            ban.add(c)

        crawled_set.add(url)
        crawled_list.append(url)

        #Covert the page into a list of words
        word_list = list()
        for text in soup.stripped_strings:
            for word in re.findall("[a-zA-Z0-9]+", text.lower()):
                word_list.append(word)
        word_list.append(url)

        #Record current link
        with open("url.txt","a") as f, open("words.txt","a") as w:
            f.write(url+"\n")
            w.write(str(word_list)+"\n")

        #Link preprocessing
        for link in soup.find_all('a'):
            if (link.get('rel') == None) or ( link.get('rel') != None and "nofollow" not in link.get('rel') ):
                path = link.get('href')

                path = urljoin(url,path) 
                parsed = urlparse(path)

                if parsed.scheme == "http":
                    path = path.replace("http:","https:")

                if parsed.fragment != "":
                    path = urldefrag(path)[0]
                
                if path.endswith("/"):
                    path = path.rstrip("/")
                
                if url != path:
                    parent[path] = url
                    child[url].add(path)
                    scrapping.append(path)

    return scrapping

def is_valid(url):
    try:
        parsed = urlparse(url)
        
        if url in ban:
            return False

        path = parsed.path.lower()
        
        #Validate scheme
        if parsed.scheme not in {"http","https"}:
            return False

        #Filter out non-textual format
        if re.match(
            r".*\.(css|js|bmp|gif|jpe?g|ico"
            + r"|png|tiff?|mid|mp2|mp3|mp4"
            + r"|wav|avi|mov|mpeg|ram|m4v|mkv|ogg|ogv|pdf"
            + r"|ps|eps|tex|ppt|pptx|doc|docx|xls|xlsx|names"
            + r"|data|dat|exe|bz2|tar|msi|bin|7z|psd|dmg|iso"
            + r"|epub|dll|cnf|tgz|sha1"
            + r"|thmx|mso|arff|rtf|jar|csv"
            + r"|rm|smil|wmv|swf|wma|zip|rar|gz"
            + r"|m|r|c|class|cpp|cs|h|java|py|swift|sql|db|lif|z|war|apk|img|mpg|scm|rkt|ss|odc|sas|mat|rle|ppsx|htm"
            + r"|arj|pkg|rpm|tar.gz|log|mdb|bat|pl|com|svg|ico|cgi|cer|jsp|part|key|pps|sh|ods|ods|tsv|fig|bib|cp)$", path):
            return False
        
        #Check infinite directory
        check = set()
        for parent in parsed.path.split("/")[1:]:
            if parent in check:
                return False
            check.add(parent)

        #Validate domain
        if domains[-1] in parsed.netloc and "/department/information_computer_sciences/" in path:
            return True
        for domain in domains[:-1]:
            if domain in parsed.netloc:
                return True
        return False

        """
        if ("calendar" in path or "wp-login" in path or "wp-content" in path or "gallery" in path or "@" in path or "ical" in parsed.query):
            return False
        if "swiki.ics.uci.edu" in parsed.netloc and parsed.query != "":
            return False
        if "archive.ics.uci.edu" in parsed.netloc and (parsed.query != "" or "/ml/0" in path or "www.cs.man.ac.uk" in path):
            return False
        if "sli.ics.uci.edu" in parsed.netloc and (parsed.query != "" or "/Classes" in path):
            return False
        if ( ("wics.ics.uci.edu" in parsed.netloc) and 
        ("/event" in path or "share" in parsed.query or "page_id" in parsed.query) ):
            return False
        if "cbcl.ics.uci.edu" in parsed.netloc and parsed.query != "":
            return False
        if "cml.ics.uci.edu" in parsed.netloc and parsed.query != "":
            return False
        if "support.ics.uci.edu" in parsed.netloc and parsed.query != "":
            return False
        if "grape.ics.uci.edu" in parsed.netloc:
            return False
        
        if ("www.ics.uci.edu" in parsed.netloc and ("/honors" in path or "/stayconnected" in path) ):
            return False
        if "www.informatics.uci.edu" in parsed.netloc and "seminar_id" in parsed.query:
            return False
        if ("www.cs.uci.edu" in parsed.netloc and ("/events/list/page" in path or "/events/category/lectures/list" in path) ):
            return False
        """

    except TypeError:
        print ("TypeError for ", parsed)
        raise

