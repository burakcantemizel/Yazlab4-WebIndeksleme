from flask import Flask, render_template, request
from bs4 import BeautifulSoup
import requests
import re
import collections
import stopwords
import nltk
import math
import lxml
import cchardet
#import asyncio
from requests_html import HTMLSession,AsyncHTMLSession
from anytree import Node, RenderTree

requests_session = requests.Session()
#asession = AsyncHTMLSession()

session = HTMLSession()

app = Flask(__name__)



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
        similarityScores = preCalculatedSimilarityScores(mainUrl, mainKeywords, otherUrls)
        return render_template('CalculateSimilarity.html', result = similarityScores)
    else:
        return render_template('CalculateSimilarity.html', result = None)

@app.route('/Indexing', methods = ['POST', 'GET'])
def Indexing():
    if request.method == 'POST':
        mainUrl = request.form['url'] #url string olarak geliyor
        otherUrls = request.form['urls'].split() # diğer urllerde string listesi olarak gelsin
        mainSiteKeywords = findKeywordsFromUrl(mainUrl)
        subLinkSimilarity = dict()
        recursiveIndexing(mainUrl, mainSiteKeywords, mainUrl, otherUrls, 3, 5, subLinkSimilarity)
        print(subLinkSimilarity)

        return render_template('Indexing.html', result = None)
    else:
        return render_template('Indexing.html', result = None)

def recursiveIndexing(mainUrl, mainSiteKeywords, parent, otherUrls, maximumLevel, maxSubLink, dictionary):
    if maximumLevel < 1:
        return

    print(maximumLevel)
    dictionary[parent] = preCalculatedSimilarityScores(mainUrl, mainSiteKeywords, otherUrls)
    #dictionary[parent] = otherUrls


    
    for url in otherUrls:
        try:
            recursiveIndexing(mainUrl, mainSiteKeywords, url, findSubLinks(url , maxSubLink), maximumLevel-1, maxSubLink, dictionary)
        except:
            continue


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
                print(keyword)
                mainFrequencySqSum = mainFrequencySqSum + count ** 2
                siteFrequencySqSum = siteFrequencySqSum + keywords[keyword] ** 2
           
        mainFrequencyFactor = math.sqrt(mainFrequencySqSum)
        siteFrequencyFactor = math.sqrt(siteFrequencySqSum)

        if mainFrequencyFactor == 0 or siteFrequencyFactor == 0:
            similarityScores[site] = 0
        else:
            similarityScores[site] = ((mainFrequencyFactor * siteFrequencyFactor) / (mainFrequencyFactor ** 2 + siteFrequencyFactor ** 2 - mainFrequencyFactor * siteFrequencyFactor)) * 100

    return similarityScores


def htmlToPlainText(url):
    html = requests_session.get(url).text #Complexity !!! Requestsi test et
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