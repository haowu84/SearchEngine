Eeny Meany Miny Moe Search! Version 1.0 03/08/2021

INTRODUCTION
--------------

The Eeny Meany Miny Moe Search! is a UCI web search engine that is capable of handling tens of thousands of documents or
Web pages and has an average query response time < 100ms. Programming languages used include Python, HTML, Javascript, and
CSS.


REQUIREMENTS
--------------

In order to run the Eeany Meany Miny Moe Search! engine, the following Python modules are required:

* Beautiful Soup 4 
* NLTK
* Eel

If you do not have python or pip installed, install them before running the following command to install the dependencies

pip install beautifulsoup4

pip install lxml

pip install --user -U nltk

python -m nltk.downloader popular

pip install eel


GENERAL USAGE
--------------

The Python files are the main part of the Eeny Meany Miny Moe Search! engine and must be ran in the following order for 
the engine to work properly:

1) indexer.py : Upon running this Python file, the program will begin to parse through a collection of documents and/or
		webpages to build and inverted index that maps tokens-> document postings. To avoid running out of memory,
		the program will begin to off load the inverted index from main memory to a partial index on disk. Towards
		the end of the program's execution, the partial indexes will be merged to create a single, complete index.

2) search.py  : The search component of the search engine uses the inverted index built by indexer.py from which to 
		retrieve urls related to the user typed query. The program uses the Python module Eel to display a Web
		gui to the user that depicts a search bar for the user to type their query into. The search engine can
		receive single word queries as well as free text queries and responds with a full page of the top 10 URLs 
		related to the query within ~100 ms.
		

To execute the indexing portion, run the indexer.py command
python3 indexer.py

To execute the searching portion, run the search.py command
python3 search.py


You may need to change the file path in build_index() function to correctly index the folder in your operating system/machine

def build_index():
	...
	for path in glob.iglob(r'YourPathHere/**/*.json', recursive=True):
	...



