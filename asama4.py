import grequests
from bs4 import BeautifulSoup
import re

def recursiveIndexingTest(mainUrl, mainSiteKeywords, parent, otherUrls, level, maxSubLink, dictionary):


    #dictionary[parent] = await preCalculatedSimilarityScores(mainUrl, mainSiteKeywords, otherUrls)
    altAgac = dict()
    for url in otherUrls:
        altAgac.update({url : None})

    dictionary[parent] = altAgac
    
    if level > 3: #birinci seviyede ana urllerle karşılaştırıcaz, 2. seviyede ana urlnin altındaki 2. seviye linklerle karşılaştırıcaz 3. de 3. seviyedeki linklerle karşılaştırcaz
        return

    rs = (grequests.get(url) for url in otherUrls)
    i = 0
    for response in grequests.map(rs):
        try:
            i = i + 1
            recursiveIndexingTest(mainUrl, mainSiteKeywords, response.url, findSubLinks2(response , maxSubLink), level+1, maxSubLink, dictionary)
            #print("recursive girdi")
            #loop.run_until_complete(await recursiveIndexing(mainUrl, mainSiteKeywords, url, findSubLinks(url , maxSubLink), maximumLevel-1, maxSubLink, dictionary))
        except:
            print("hata")
            i = i + 1
            recursiveIndexingTest(mainUrl, mainSiteKeywords, response.url, [], level+1, maxSubLink, dictionary)
            continue
            


def createUrlTree():
    tree = {}

    level1Dict = {}
    for level1Url in otherUrls: #1. seviyedeki urlleri requestleyip alt linklerini alıp dicte ekleyeceğiz
        level1Dict[level1Url] = None #1. seviye linkler köke ekleniyor girilen url dizisinden elde ediliyorlar
        
    #ilk seviyede 1. seviye tüm linkleri aynı anda requestliyoruz
    rs = (grequests.get(key) for key, value in level1Dict.items())
    #gelen response listesini geziyoruz
    for response in grequests.map(rs):
        for key in tree.items():
            print(key)
            key = findSubLinks2(response, 1) # burdan alt url listesi geliyor dicte çevircez
            
    
    tree[mainUrl] = level1Dict

    print(tree)
    #tree[mainUrl] = -1 dal altındaki urller eklenecek

def findSubLinks2(response, maxSubLink):
    soup = BeautifulSoup(response.content, 'lxml')
    links = {}
    
    i = 0
    for link in soup.findAll('a', attrs={'href': re.compile("^http://")}):
            i = i + 1
            links[link.get('href')] = None
            if maxSubLink != -1 and i >= maxSubLink : break
    return links

def findSubLinks3(response, maxSubLink):
    #html = requests_session.get(url)
    try:
        linkler = response.html.absolute_links
    except:
        return []
    
    if maxSubLink == -1:
        return list(linkler)
    else:
        return list(linkler)[:maxSubLink]

mainUrl = "http://kocaeli.edu.tr/"
otherUrls = "http://burakcantemizel.com/ https://www.google.com/".split()
urlListesi = dict()
recursiveIndexingTest(mainUrl, None, mainUrl, otherUrls, 1, 5, urlListesi)
print(urlListesi)

