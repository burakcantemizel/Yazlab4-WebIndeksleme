from flask import Flask, render_template, request
from bs4 import BeautifulSoup
#import requests
import re
import collections
import stopwords
import nltk
import math
import lxml
import cchardet
import grequests
#import asyncio
from requests_html import HTMLSession,AsyncHTMLSession
import nltk
from nltk.corpus import wordnet
from anytree import Node, RenderTree
from anytree.exporter import DictExporter,JsonExporter
from urllib.parse import urljoin

from werkzeug.middleware.profiler import ProfilerMiddleware
from gevent import monkey
monkey.patch_all()

nltk.download('wordnet')
requests_session = grequests.Session()
#asession = AsyncHTMLSession()


session = HTMLSession()

app = Flask(__name__)
app.wsgi_app = ProfilerMiddleware(app.wsgi_app, profile_dir="./")


@app.route('/CalculateFrequency', methods = ['POST', 'GET'])
def calculateFrequency():
    if request.method == 'POST':
        url = request.form['url']
        plainText = htmlToPlainText(url)
        words = filterWordsForFrequency(plainTextToWords(plainText))
        wordsFrequency = calculateWordsCount(words)
        return render_template('CalculateFrequency.html', result = wordsFrequency)
    else:
        return render_template('CalculateFrequency.html', result = None)

@app.route('/FindKeywords', methods = ['POST', 'GET'])
def findKeywords():
    if request.method == 'POST':
        url = request.form['url']
        plainText = htmlToPlainText(url)
        words = filterWordsForKeywords(filterWordsForFrequency(plainTextToWords(plainText)))
        wordsFrequency = calculateWordsCount(words)
        keywords = findKeywords(wordsFrequency)

        return render_template('FindKeywords.html', result = keywords)
    else:
        return render_template('FindKeywords.html', result = None)

@app.route('/CalculateSimilarity', methods = ['POST', 'GET'])
def calculateSimilarity():
    if request.method == 'POST':
        mainUrl = request.form['url']
        otherUrls = request.form['urls'].split()
        
        mainKeywords = findKeywordsFromUrl(mainUrl)
        similarityScores, otherSitesKeywords = preCalculatedSimilarityScores(mainUrl, mainKeywords, otherUrls)
        sortedSimilarityScores = sortDict(similarityScores, True)
        return render_template('CalculateSimilarity.html', result = sortedSimilarityScores , mainSiteKeywordsResult = mainKeywords, otherSitesKeywordsResult = otherSitesKeywords)
    else:
        return render_template('CalculateSimilarity.html', result = None, mainSiteKeywordsResult = None, otherSitesKeywordsResult = None)

@app.route('/Indexing', methods = ['POST', 'GET'])
def Indexing():
    if request.method == 'POST':
        mainUrl = request.form['url'] #url string olarak geliyor
        otherUrls = request.form['urls'].split() # diğer urllerde string listesi olarak gelsin
        maxSubLink = request.form['maxSubLink']

        mainSiteKeywords = findKeywordsFromUrl(mainUrl)
        root = Node('root')
        recursiveIndexing(mainUrl, mainSiteKeywords, root, otherUrls, 1, int(maxSubLink), root)

        exporter = DictExporter()
        generalScoreDict = exporter.export(root)
        #print(localScoreDict)
        #print("\n\n")
        calculateWeightedScore(generalScoreDict)
        #print(generalScoreDict)
        
        exporter = JsonExporter(indent=2, sort_keys=False)
        treeJson = exporter.export(root)
        #print(type(treeJson))

        #for pre, fill, node in RenderTree(root):
        #    print("%s%s" % (pre, node.name))
        

        return render_template('Indexing.html', result = None, tree = treeJson)
    else:
        return render_template('Indexing.html', result = None, tree = None)


def calculateWeightedScore(localScoreDict):
    if "children" in localScoreDict:
        for level1 in localScoreDict["children"]: # root içinde level1 dallar
            #level1["name"]["score"] = level1["name"]["score"] * 3
            #print(level1["name"]["score"]) # 1. dalların skoru bunu 2. dalda ve 3.dalda güncelleyeceğiz
            if "children" in level1:
                for level2 in level1["children"]: #level1 içinde level2 dallar
                    #level1["name"]["score"] = level1["name"]["score"] + level2["name"]["score"] * 2
                    level1["name"]["generalScore"] = level1["name"]["generalScore"] + level2["name"]["localScore"]
                    if "children" in level2:
                        for level3 in  level2["children"]:
                            #level1["name"]["score"] = level1["name"]["score"] + level3["name"]["score"] * 1
                            level1["name"]["generalScore"] = level1["name"]["generalScore"] + level3["name"]["localScore"]
                            level2["name"]["generalScore"] = level2["name"]["generalScore"] + level3["name"]["localScore"]

def recursiveIndexing(mainUrl, mainSiteKeywords, parentNode, otherUrls, level, maxSubLink, tree):
    #dictionary[parent] = await preCalculatedSimilarityScores(mainUrl, mainSiteKeywords, otherUrls)
    print("test")
    
    parentNodes = []
        

        
    #dictionary[parent] = altAgac
    #dictionary[parent], x = preCalculatedSimilarityScores(mainUrl, mainSiteKeywords, otherUrls)
    
    validUrls = []

    rsmetalist = (grequests.head(url) for url in otherUrls)
    for rsmeta in grequests.map(rsmetalist):
        if "text/html" in rsmeta.headers["content-type"]:
            #print("2test")
            validUrls.append(rsmeta.url)

    

    rs = (grequests.get(url) for url in validUrls)
    i = 0
    for response in grequests.map(rs):
        #localscorları burda hesaplasak
        localScore , otherKeywords  = preCalculatedSimilarityScoresResponse(mainUrl, mainSiteKeywords, response)
        parentNodes.append(Node({'url': response.url, 'localScore': localScore, 'generalScore': localScore , 'keywords' : otherKeywords}, parent = parentNode))
        #parentNodes[i].score = localScore

        if level > 2: #birinci seviyede ana urllerle karşılaştırıcaz, 2. seviyede ana urlnin altındaki 2. seviye linklerle karşılaştırıcaz 3. de 3. seviyedeki linklerle karşılaştırcaz
            return
        #parentNodes[i](score = localScore)
        #parentNodes[i].update({'score': localScore})
        try:
            recursiveIndexing(mainUrl, mainSiteKeywords, parentNodes[i], findSubLinks2(response , maxSubLink), level+1, maxSubLink, tree)
            i = i + 1
            #print("recursive girdi")
            #loop.run_until_complete(await recursiveIndexing(mainUrl, mainSiteKeywords, url, findSubLinks(url , maxSubLink), maximumLevel-1, maxSubLink, dictionary))
        except:
            print("hata")
            #recursiveIndexing(mainUrl, mainSiteKeywords, parentNodes[i], [], level+1, maxSubLink, tree)
            i = i + 1
            continue

def findSubLinks2(response, maxSubLink):
    soup = BeautifulSoup(response.content, 'lxml')
    links = []
    
    i = 0
    #for link in soup.findAll('a', attrs={'href': re.compile("^http://")}):
    for link in soup.findAll('a', attrs={'href': re.compile("")}):
            print("alt link araniyor")
            #if link.get('href').lower().endswith('.pdf'): continue
            #if link.get('href').lower().endswith('.gif'): continue
            #if link.get('href').lower().endswith('.svg'): continue
            #if link.get('href').lower().endswith('.ogg'): continue
            i = i + 1
            print(response.url)
            #print
            link = urljoin(response.url, link.get('href'))
            links.append(link)
            if maxSubLink != -1 and i >= maxSubLink : break
    return links

@app.route('/Semantics', methods = ['POST', 'GET'])
def Semantics():
    if request.method == 'POST':
        mainUrl = request.form['url'] #url string olarak geliyor
        #otherUrls = request.form['urls'].split() # diğer urllerde string listesi olarak gelsin
        mainKeywords = findKeywordsFromUrl(mainUrl)
        semanticKeywords= findSemanticsKeywords(mainKeywords)
        return render_template('Semantics.html', mainKeywordsResult = mainKeywords, semanticsKeywordsResult = semanticKeywords)
    else:
        return render_template('Semantics.html', result = None, semanticsKeywordsResult = None)
"""
def recursiveIndexing(mainUrl, mainSiteKeywords, parent, otherUrls, maximumLevel, maxSubLink, dictionary):
    #dictionary[parent] = otherUrls
    if maximumLevel > 4:
        return

    print(maximumLevel)
    dictionary[parent], x = preCalculatedSimilarityScores(mainUrl, mainSiteKeywords, otherUrls)


    for url in otherUrls:
        try:
            recursiveIndexing(mainUrl, mainSiteKeywords, url, findSubLinks(url , maxSubLink), maximumLevel+1, maxSubLink, dictionary)
        except:
            print("Dalda Hata oldu!")
            continue
"""    
def preCalculatedSimilarityScores(mainUrl, mainSiteKeywords, otherUrls):
    otherSitesKeywords = dict()
    
    for url in otherUrls:
        otherSitesKeywords[url] = findKeywordsFromUrl(url)

    similarityScores = dict()

    for site, keywords in otherSitesKeywords.items():
        mainFrequencySqSum = 0
        siteFrequencySqSum = 0

        for keyword, count in mainSiteKeywords.items():
            if keywords.get(keyword):
                mainFrequencySqSum = mainFrequencySqSum + count ** 2
                siteFrequencySqSum = siteFrequencySqSum + keywords[keyword] ** 2
           
        mainFrequencyFactor = math.sqrt(mainFrequencySqSum)
        siteFrequencyFactor = math.sqrt(siteFrequencySqSum)

        if mainFrequencyFactor == 0 or siteFrequencyFactor == 0:
            similarityScores[site] = 0
        else:
            similarityScores[site] = ((mainFrequencyFactor * siteFrequencyFactor) / (mainFrequencyFactor ** 2 + siteFrequencyFactor ** 2 - mainFrequencyFactor * siteFrequencyFactor)) 

    return similarityScores, otherSitesKeywords

def preCalculatedSimilarityScoresResponse(mainUrl, mainSiteKeywords, response):
    #bu metod tekrar düzenlenecek
    otherSiteKeywords = findKeywordsFromUrlResponse(response) # anahtar kelime dicti
    
    mainFrequencySqSum = 0
    siteFrequencySqSum = 0

    for okeyword, ocount in otherSiteKeywords.items(): #dieğr anahtar kelimeleri dolaşıyoruz
        for keyword, count in mainSiteKeywords.items(): # ana anahtar kelimeleri dolaşıyoru
            if okeyword == keyword:
                #print("ortak kelime bulundu")
                #print(okeyword)
                mainFrequencySqSum = mainFrequencySqSum + count ** 2
                siteFrequencySqSum = siteFrequencySqSum + ocount ** 2
           
        mainFrequencyFactor = math.sqrt(mainFrequencySqSum)
        siteFrequencyFactor = math.sqrt(siteFrequencySqSum)

        if mainFrequencyFactor == 0 or siteFrequencyFactor == 0:
            similarityScore = 0
        else:
            similarityScore = ((mainFrequencyFactor * siteFrequencyFactor) / (mainFrequencyFactor ** 2 + siteFrequencyFactor ** 2 - mainFrequencyFactor * siteFrequencyFactor)) * 100

    return similarityScore , otherSiteKeywords

def htmlToPlainText(url):
    html = requests_session.get(url).text #Complexity !!! Requestsi test et
    soup = BeautifulSoup(html, "lxml")

    plainText = soup.get_text().strip().lower()

    return plainText

def htmlToPlainTextResponse(response):
    html = response.text #Complexity !!! Requestsi test et
    soup = BeautifulSoup(html, "lxml")

    plainText = soup.get_text().strip().lower()

    return plainText

def plainTextToWords(plainText):
    tokenizer = nltk.RegexpTokenizer(r"\w+")
    allWords = tokenizer.tokenize(plainText)
    return allWords

def filterWordsForFrequency(words):
    filteredWords = []

    minimumChars = 1
    maximumChars = 40 #Longest Word in English has 44 characters

    for word in words:
        if (len(word) > minimumChars or word == "a") and len(word) < maximumChars and word.isdigit() == False:
            filteredWords.append(word)
    
    return filteredWords

def filterWordsForKeywords(words):
    filteredWords = []

    for word in words:
        if word not in stopwords.english:
            filteredWords.append(word)
    
    return filteredWords

def calculateWordsCount(filteredWords):
    wordsCount = dict()

    for word in filteredWords:
        if word not in wordsCount:
            wordsCount.update({word:1})
        else:
            wordsCount[word] += 1
    
            
    sortedWordsCount = {}
    sortedWordsKeys = sorted(wordsCount, key=wordsCount.get, reverse = True)

    for w in sortedWordsKeys:
        sortedWordsCount[w] = wordsCount[w]

    return sortedWordsCount

def sortDict(dictionary, isReverse):
    sortedDict = {}
    sortedKeys = sorted(dictionary, key=dictionary.get, reverse = True)

    for w in sortedKeys:
        sortedDict[w] = dictionary[w]

    return sortedDict

def findKeywords(words):
    numberOfKeyword = 10
    keywords = dict(list(words.items())[:numberOfKeyword])
    return keywords

def findKeywordsFromUrl(url):
    plainText = htmlToPlainText(url)
    words = filterWordsForKeywords(filterWordsForFrequency(plainTextToWords(plainText)))
    wordsFrequency = calculateWordsCount(words)
    keywords = findKeywords(wordsFrequency)
    return keywords

def findKeywordsFromUrlResponse(response):
    plainText = htmlToPlainTextResponse(response)
    words = filterWordsForKeywords(filterWordsForFrequency(plainTextToWords(plainText)))
    wordsFrequency = calculateWordsCount(words)
    keywords = findKeywords(wordsFrequency)
    return keywords

def findSemanticsKeywords(keywords):
    semanticsKeywords = dict()

    for key, value in keywords.items():
        syns = wordnet.synsets(key)
        semanticsKeywords[key] = syns[0].lemmas()[0].name().replace("_"," ").replace("-"," ").lower().strip()

    return semanticsKeywords

def findSubLinks(url, maxSubLink):
    #html = requests_session.get(url)
    try:
        linkler = session.get(url).html.absolute_links
    except:
        return []
    
    if maxSubLink == -1:
        return list(linkler)
    else:
        return list(linkler)[:maxSubLink]

"""    
def findSubLinks2(url, maxSubLink):
    html = requests_session.get(url)
    soup = BeautifulSoup(html.content, 'lxml')
    links = []
    
    i = 0
    for link in soup.findAll('a', attrs={'href': re.compile("^http://")}):
        if not link.endswith('.pdf', '.jpg', '.png', '.jpeg', '.gif'):
            i = i + 1
            links.append(link.get('href'))
            print("test 1")
            if maxSubLink != -1 and i >= maxSubLink : break
    print("test 2")
    return links
"""

def playground():
   pass

def do_something(response):
    print(response.url)


if __name__ == '__main__':
    app.debug = True

     ##Test Kısmı
    mainUrl = "https://en.wikipedia.org/wiki/Fernando_Muslera"
    otherUrls = "https://en.wikipedia.org/wiki/Soviet_Union https://en.wikipedia.org/wiki/Nazi_Germany".split()
    mainKeywords = findKeywordsFromUrl(mainUrl)
    tree = {}

    #örnek dict
    #(url : alt urller)

    #root = Node("root")

    #Siteden Post atıldığında aşağıdaki işlemler sırası ile gerçekleşecek
    #rs = (grequests.get(u) for u in otherUrls)
    #print(rs)

    """
    for level1 in otherUrls:
        level1Node = Node(level1, parent = root)
        #Her url için benzerlik hesaplaması yapılacak
        #Her urlnin alt linkleri bulunup ağaçta onun altına eklenecek
        
        for level2 in findSubLinks(level1, subLinkCount):
            
            level2Node = Node(level2, parent = level1Node)
            for level3 in findSubLinks(level2, subLinkCount):
                level3Node = Node(level3, parent = level2Node)
    
    for pre, fill, node in RenderTree(root):
        print("%s%s" % (pre, node.name))
    """

    app.run()