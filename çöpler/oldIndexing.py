@app.route('/Indexing', methods = ['POST', 'GET'])
def Indexing():
    if request.method == 'POST':
        mainUrl = request.form['url'] #url string olarak geliyor
        otherUrls = request.form['urls'].split() # diğer urllerde string listesi olarak gelsin

        subLinkSimilarity = dict()
        mainSiteKeywords = findKeywordsFromUrl(mainUrl)
        #recursiveIndexingTest(mainUrl, mainSiteKeywords, mainUrl, otherUrls, 1, 5, subLinkSimilarity)
        #print(subLinkSimilarity)

        #loop.run_until_complete(recursiveIndexing(mainUrl, mainSiteKeywords, mainUrl, otherUrls, 3, 5, subLinkSimilarity))
        #recursiveIndexing(mainUrl, mainSiteKeywords, mainUrl, otherUrls, 3, 3, subLinkSimilarity)
        #print(subLinkSimilarity)

        return render_template('Indexing.html', result = None)
    else:
        return render_template('Indexing.html', result = None)

def recursiveIndexingTest(mainUrl, mainSiteKeywords, parent, otherUrls, level, maxSubLink, dictionary):
    if level > 3: #birinci seviyede ana urllerle karşılaştırıcaz, 2. seviyede ana urlnin altındaki 2. seviye linklerle karşılaştırıcaz 3. de 3. seviyedeki linklerle karşılaştırcaz
        return

    #dictionary[parent] = await preCalculatedSimilarityScores(mainUrl, mainSiteKeywords, otherUrls)
    dictionary[parent] = otherUrls
    
    for url in otherUrls:
        try:
            recursiveIndexingTest(mainUrl, mainSiteKeywords, url, findSubLinksTest(url , maxSubLink), level+1, maxSubLink, dictionary)
            #print("recursive girdi")
            #loop.run_until_complete(await recursiveIndexing(mainUrl, mainSiteKeywords, url, findSubLinks(url , maxSubLink), maximumLevel-1, maxSubLink, dictionary))
        except:
            print("Linkte hata")
            continue

async def findSubLinksTest(url, maxSubLink):
    #html = requests_session.get(url)
    linkler = await asession.get(url).html.absolute_links
    #print(list(linkler)[:maxSubLink])
    return list(linkler)[:maxSubLink]




async def preCalculatedSimilarityScores(mainUrl, mainSiteKeywords, otherUrls):
    otherSitesKeywords = dict()
    
    for url in otherUrls.split():
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
            similarityScores[site] = (mainFrequencyFactor * siteFrequencyFactor) / (mainFrequencyFactor ** 2 + siteFrequencyFactor ** 2 - mainFrequencyFactor * siteFrequencyFactor) * 100

    return similarityScores


def findSubLinks(url, maxSubLink):
    html = requests_session.get(url)
    soup = BeautifulSoup(html.content, 'lxml')
    links = ""
    
    i = 0
    for link in soup.findAll('a', attrs={'href': re.compile("^http://")}):
        i = i + 1
        links = links + ' ' + link.get('href')
        print("test 1")
        if maxSubLink != -1 and i >= maxSubLink : return links
    print("test 2")
    return links



"""
async def recursiveIndexing(mainUrl, mainSiteKeywords, parent, otherUrls, maximumLevel, maxSubLink, dictionary):
    if maximumLevel < 1:
        loop.close()
        return

    print(maximumLevel)
    #dictionary[parent] = await preCalculatedSimilarityScores(mainUrl, mainSiteKeywords, otherUrls)
    dictionary[parent] = otherUrls
    
    for url in otherUrls.split():
        try:
            print("recursive girdi")
            loop.run_until_complete(await recursiveIndexing(mainUrl, mainSiteKeywords, url, findSubLinks(url , maxSubLink), maximumLevel-1, maxSubLink, dictionary))
        except:
            continue
"""

def calculateSimilarityScores(mainUrl, otherUrls):
    mainSiteKeywords = findKeywordsFromUrl(mainUrl)
    otherSitesKeywords = dict()
    
    for url in otherUrls.split():
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
            similarityScores[site] = (mainFrequencyFactor * siteFrequencyFactor) / (mainFrequencyFactor ** 2 + siteFrequencyFactor ** 2 - mainFrequencyFactor * siteFrequencyFactor) * 100

    return similarityScores

    
"""
tree = {}

level1Dict = {}
for level1Url in otherUrls: #1. seviyedeki urlleri requestleyip alt linklerini alıp dicte ekleyeceğiz
    level1Dict[level1Url] = None #1. seviye linkler köke ekleniyor girilen url dizisinden elde ediliyorlar
        
#ilk seviyede 1. seviye tüm linkleri aynı anda requestliyoruz
tree[mainUrl] = level1Dict

rs = (grequests.get(key) for key, value in level1Dict.items())
i = 0
for response in grequests.map(rs):
tree[tree.keys()[i]] = findSubLinks2(response, 2)
i = i + 1
""""