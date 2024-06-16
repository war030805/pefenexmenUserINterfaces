#!/usr/bin/python3

#v0.4

import os
import re #regex
import bs4 # pip install beautifulsoup4
from enum import Enum
from collections import namedtuple, Counter

# global settings
doCheckSubFolders = True
excludeDirs = ['auto-validation','__MACOSX']
excludeDotDirs = True # directories whose names begin with '.'
projectBaseDir = '' # needed to get relative paths of project-files

# enum HTML-checks
class HtmlChecks(Enum):
    Error = 100
    TagSummary = 0
    BaseStructure = 11; PageTitleAndH1Info = 12
    OutsideBody = 21  #; UpperCaseTagNames = 22
    Main = 31; NestedArticles = 32; ForbiddenTags = 33; SemiForbiddenTags = 34; SemanticTags = 35
    ImageScaling = 41; ImageAltInfo = 42
    FormInputTypes = 51; FormInputNameAttr = 52; FormInputValidation = 53

# custom types
TagInfo = namedtuple('TagInfo', ['htmlFilename', 'name', 'count'])

# constants
sectioningElements = ['body', 'nav', 'aside', 'article', 'section']
headingRegex = re.compile('^h([1-6])$')


## HTML Files ##
parsedHtmlFiles = {} # all lower case (= case insensitive)
#parsedAsXmlFiles = {} # as is (= case sensitive)
def _parseHtmlFile(htmlFile, caseSensitive=False):
    global parsedHtmlFiles
    fileName = os.path.relpath(htmlFile, projectBaseDir)
    document = None
    if not caseSensitive:
        if fileName in parsedHtmlFiles:
            document = parsedHtmlFiles[fileName]
        else:
            with open(htmlFile) as file:
                document = bs4.BeautifulSoup(file.read(), 'html.parser')
                #document = bs4.BeautifulSoup(file.read(), 'html5lib') # requires 'pip install html5lib' # creates valid HTML5, but we wan't the original code + is slow
                parsedHtmlFiles[fileName] = document
    # elif caseSensitive: # TODO: requires original tag names from source
    #     if fileName in parsedAsXmlFiles:
    #         document = parsedAsXmlFiles[fileName]
    #     else:
    #         with open(htmlFile) as file:
    #             document = bs4.BeautifulSoup(file.read(), 'xml') # TODO: requires 'pip install lxml'
    #             parsedAsXmlFiles[fileName] = document
    return document

flatmapHtmlFiles = []
def _flattenHtmlFile(htmlFile):
    global flatmapHtmlFiles
    fileName = os.path.relpath(htmlFile, projectBaseDir)
    tagsFlatmap = []
    found = False
    for tagInfo in flatmapHtmlFiles:
        (flattenFileName, name, count) = tagInfo
        if flattenFileName == fileName:
            tagsFlatmap.append(tagInfo)
            found = True
    if not found:
        document = _parseHtmlFile(htmlFile)
        tags = document.select('*')
        uniqueTagsCounted = sorted(Counter([tag.name for tag in tags]).items(), key=lambda item: item[0])
        for key,val in uniqueTagsCounted:
            tagName = key
            tagCount = val
            tagInfo = TagInfo(fileName, tagName, tagCount)
            flatmapHtmlFiles.append(tagInfo)
            tagsFlatmap.append(tagInfo)
    return tagsFlatmap
def _flattenHtmlFiles(htmlFiles):
    tagsFlatmap = []
    for htmlFile in htmlFiles:
        tagsFlatmap += _flattenHtmlFile(htmlFile)
    return tagsFlatmap
def _getTagsSummaryOfFile(htmlFile, tags = None, includeOtherTags = False):
    uniqueTags = {}
    for tagInfo in _flattenHtmlFile(htmlFile):
        (fileName, name, count) = tagInfo
        if not name in uniqueTags:
            uniqueTags[name] = count
        else:
            uniqueTags[name] += count
    uniqueTagsSorted = {key: val for key, val in sorted(uniqueTags.items())}
    results = []
    if tags:
        for item in tags:
            if isinstance(item, list):
                results += _getTagsSummaryOfFile(htmlFile, item)
                results.append('')
            else:
                tagName = item
                for key,val in uniqueTagsSorted.items():
                    if tagName == key:
                        count = val
                        results.append(f'{tagName:<10}{count:>5}')
                        uniqueTagsSorted.pop(key)
                        break
        # other tags (not part of tags-param)
        if includeOtherTags:
            results.append('')
            for key,val in uniqueTagsSorted.items():
                tagName = key
                count = val
                results.append(f'{tagName:<10}{count:>5}')
    else:
        for key,val in uniqueTagsSorted.items():
            tagName = key
            count = val
            results.append(f'{tagName:<10}{count:>5}')
    return results
def _getTagsSummaryOfFiles(htmlFiles, tags = None, includeOtherTags = False, showFileNames = False, uniqueTagsDictionary = None):
    projectFiles = []
    for htmlFile in htmlFiles:
        fileName = os.path.relpath(htmlFile, projectBaseDir)
        projectFiles.append(fileName)
    projectFilesSorted = sorted(projectFiles)
    uniqueTagsSorted = {}
    if uniqueTagsDictionary:
        uniqueTagsSorted = uniqueTagsDictionary
    else:
        uniqueTags = {}
        for tagInfo in _flattenHtmlFiles(htmlFiles):
            (fileName, name, count) = tagInfo
            if not name in uniqueTags:
                uniqueTags[name] = [count, {}]
                uniqueTags[name][1][fileName] = count
            else:
                uniqueTags[name][0] += count
                if not fileName in uniqueTags[name]:
                    uniqueTags[name][1][fileName] = count
                else:
                    uniqueTags[name][1][fileName] += count
        uniqueTagsSorted = {key: val for key, val in sorted(uniqueTags.items())}
    def getTagResultInfo(tagName, uniqueTagValue, projectFiles):
        totalCount = uniqueTagValue[0]
        fileCounts = []
        for file in projectFiles:
            fileCounts.append(0)
        for (fileName, count) in uniqueTagValue[1].items():
            fileIndex = projectFiles.index(fileName)
            fileCounts[fileIndex] = count
        fileCountInfo = ', '.join(f'{str(fileCount):>2}' for fileCount in fileCounts)
        return (totalCount, fileCountInfo)
    results = []
    if showFileNames:
        results.append('*** HTML-files ***')
        results.append('\n'.join(fileName for fileName in projectFilesSorted))
        results.append('\n')
        results.append('*** Overzicht tags (per file) ***')
    if tags:
        for item in tags:
            if isinstance(item, list):
                results += _getTagsSummaryOfFiles(htmlFiles, item, uniqueTagsDictionary=uniqueTagsSorted)
                results.append('')
            else:
                tagName = item
                result = None
                for key,val in uniqueTagsSorted.items():
                    if tagName == key:
                        result = getTagResultInfo(key, val, projectFilesSorted)
                        uniqueTagsSorted.pop(key)
                        break
                if result:
                    (totalCount, fileCountInfo) = result
                    results.append(f'{tagName:<10}{totalCount:>5}\t[{fileCountInfo}]')
                else:
                    results.append(f'{tagName:<10}{0:>5}')
    else:
        groupedTags = [['html','head','meta','style','link'],
                ['title','body','main'],
                ['nav','article','section','aside'],
                ['h1','h2','h3','h4','h5','h6'],
                ['header','footer'],
                ['figure','figcaption'],
                ['ul','ol','li','menu'],
                ['dl','dt','dd'],
                ['table','thead','tbody','tfoot','tr','td','th','colgroup','col'],
                ['img'],
                ['blockquote','q','cite'],
                ['address'],
                ['form','fieldset','label','input','textarea','select','button'],
                ['div','span','hr','br'],
                ['b','i','u']]
        results += _getTagsSummaryOfFiles(htmlFiles, groupedTags, includeOtherTags=True, uniqueTagsDictionary=uniqueTagsSorted)
    # other tags (not part of tags-param)
    if includeOtherTags:
        results.append('')
        for key,val in uniqueTagsSorted.items():
            tagName = key
            (totalCount, fileCountInfo) = getTagResultInfo(key, val, projectFilesSorted)
            results.append(f'{tagName:<10}{totalCount:>5}\t[{fileCountInfo}]')    
    return results
def _checkBaseStructure(htmlFile):
    outputResult = []
    document = _parseHtmlFile(htmlFile)
    if not document.html:
        outputResult.append('[Base structure] missing html-element')
    elif not document.html.head:
        outputResult.append('[Base structure] missing head-element')
    elif not document.html.body:
        outputResult.append('[Base structure] missing body-element')
    else:
        # lang
        if not document.html.has_attr('lang'):
            outputResult.append(['Lang missing'])
        #else:
        #    outputResult.append('[Lang] '+document.html['lang'])
        # charset
        hasCharset = False
        for tag in document.html.head:
            if isinstance(tag, bs4.Tag):
                if tag.name == 'meta' and tag.has_attr('charset'):
                    hasCharset = True
                    if not re.match('utf-', tag['charset'], re.IGNORECASE):
                        outputResult.append('[Charset] '+tag['charset'])
        if not hasCharset:
            outputResult.append('[Charset missing]')
    return outputResult
def _checkCodeOutsideBody(htmlFile):
    validTags = ['head','body']
    outputResult = []
    document = _parseHtmlFile(htmlFile)
    for tag in document.html if document.html else []:
        if isinstance(tag, bs4.Tag) and not tag.name in validTags:
            outputResult.append('[Outside body] '+str(tag.sourceline)+': '+str(tag))
    return outputResult
def _checkPageTitleAndH1Info(htmlFile):
    outputResult = []
    document = _parseHtmlFile(htmlFile)
    # title
    for tag in document.html.head if document.html and document.html.head else []:
        if isinstance(tag, bs4.Tag) and tag.name == 'title':
            outputResult.append(str(tag))
            #outputResult.append(str(tag.sourceline)+': '+str(tag))
            break
    # h1
    tagH1 = document.html.body.find('h1') if document.html and document.html.body else None
    if tagH1:
        outputResult.append(str(tagH1))
    return outputResult
def _checkSemanticTagsInfoOfFile(htmlFile):
    outputResults = _getTagsSummaryOfFile(htmlFile, ['nav','article','aside','figure','blockquote','q','cite','address'])
    return outputResults
def _checkSemanticTagsInfoOfFiles(htmlFiles):
    outputResults = _getTagsSummaryOfFiles(htmlFiles, ['nav','article','aside','figure','blockquote','q','cite','address'])
    return outputResults
def _checkMain(htmlFile):
    outputResult = []
    document = _parseHtmlFile(htmlFile)
    tags = document.find_all('main')
    if not tags:
        outputResult.append('[MISSING main]')
    elif len(tags) > 1:
        results = {}
        for tag in tags:
            if tag.name in results:
                results[tag.name].append(str(tag.sourceline))#+':'+str(tag.sourcepos))
            else:
                results[tag.name] = [str(tag.sourceline)]#+':'+str(tag.sourcepos)]
        for key,val in results.items():
            outputResult.append('[MULTIPLE main] <'+key+'>: '+'; '.join(val))
    return outputResult
def _checkNestedArticles(htmlFile):
    results = {}
    document = _parseHtmlFile(htmlFile)
    tags = document.select('article article')
    for tag in tags:
        if tag.name in results:
            results[tag.name].append(str(tag.sourceline))#+':'+str(tag.sourcepos))
        else:
            results[tag.name] = [str(tag.sourceline)]#+':'+str(tag.sourcepos)]
    outputResults = []
    for key,val in results.items():
        outputResults.append('[NESTED articles] <'+key+'>: '+'; '.join(val))
    return outputResults
def _checkSemiForbiddenTags(htmlFile):
    forbiddenTags = ['div','span','br']
    results = {}
    document = _parseHtmlFile(htmlFile)
    tags = document.find_all(forbiddenTags)
    for tag in tags:
        # if tag.name == 'br' and tag.parent and tag.parent.name == 'p':
        #     continue
        if tag.name in results:
            results[tag.name].append(str(tag.sourceline))#+':'+str(tag.sourcepos))
        else:
            results[tag.name] = [str(tag.sourceline)]#+':'+str(tag.sourcepos)]
    outputResults = []
    for key,val in results.items():
        outputResults.append('[Semi-verboden tag] <'+key+'>: '+'; '.join(val))
    return outputResults
def _checkForbiddenTags(htmlFile):
    forbiddenTags = ['b','i','u','hr']
    results = {}
    document = _parseHtmlFile(htmlFile)
    tags = document.find_all(forbiddenTags)
    for tag in tags:
        # if tag.name == 'br' and tag.parent and tag.parent.name == 'p':
        #     continue
        if tag.name in results:
            results[tag.name].append(str(tag.sourceline))#+':'+str(tag.sourcepos))
        else:
            results[tag.name] = [str(tag.sourceline)]#+':'+str(tag.sourcepos)]
    outputResults = []
    for key,val in results.items():
        outputResults.append('[Verboden tag] <'+key+'>: '+'; '.join(val))
    return outputResults
def _checkUpperCaseTags(htmlFile):
    # TODO: requires original tag-names with possible uppercase characters
    results = {}
    document = _parseHtmlFile(htmlFile, caseSensitive=True)
    tags = document.find_all(re.compile('[A-Z]'))
    for tag in tags:
        if tag.name in results:
            results[tag.name].append(str(tag.sourceline)+':'+str(tag.sourcepos))
        else:
            results[tag.name] = [str(tag.sourceline)+':'+str(tag.sourcepos)]
    outputResults = []
    for key,val in results.items():
        outputResults.append('[UPPER] <'+key+'>: '+'; '.join(val))
    return outputResults
def _checkImageScaling(htmlFile):
    results = {}
    document = _parseHtmlFile(htmlFile)
    def loopTags(tags):
        for tag in tags:
            # if tag.name == 'br' and tag.parent and tag.parent.name == 'p':
            #     continue
            if tag.name in results:
                if not str(tag.sourceline) in results[tag.name]:
                    results[tag.name].append(str(tag.sourceline))#+':'+str(tag.sourcepos))
            else:
                results[tag.name] = [str(tag.sourceline)]#+':'+str(tag.sourcepos)]
    loopTags(document.find_all('img', width=True))
    loopTags(document.find_all('img', height=True))
    outputResults = []
    for key,val in results.items():
        outputResults.append('[Image scaling] <'+key+'>: '+'; '.join(val))
    return outputResults
def _checkImageAltInfo(htmlFile):
    outputResult = []
    document = _parseHtmlFile(htmlFile)
    tags = document.find_all('img')
    for tag in tags:
        #outputResult.append(str(tag))
        outputResult.append(str(tag.sourceline)+': '+str(tag))
    return outputResult
def _checkFormInputTypes(htmlFile):
    formInputTags = ['input','select','textarea']
    results = {}
    document = _parseHtmlFile(htmlFile)
    tags = document.find_all(formInputTags)
    for tag in tags:
        inputType = None
        if tag.name == 'input':
            inputType = None
            if not tag.has_attr('type'):
                inputType = 'input_text'
            else:
                inputType = 'input_'+tag['type']
        else:
            inputType = tag.name
        
        if inputType and inputType in results:
            results[inputType] += 1
        else:
            results[inputType] = 1
    outputResults = []
    for key,val in results.items():
        outputResults.append(str(val)+'\t'+key)
    return outputResults
def _checkFormInputValidations(htmlFile):
    formInputTags = ['input','select','textarea']
    valAttributes = ['required','minlength','maxlength','min','max','step','pattern']
    results = {}
    document = _parseHtmlFile(htmlFile)
    tags = document.find_all(formInputTags)
    for tag in tags:
        for valAttr in valAttributes:
            if tag.has_attr(valAttr):
                if valAttr in results:
                    results[valAttr] += 1
                else:
                    results[valAttr] = 1
    outputResults = []
    for key,val in results.items():
        outputResults.append(str(val)+'\t'+key)
    return outputResults
def _checkFormInputNameAttr(htmlFile):
    formInputTags = ['input','select','textarea']
    outputResults = []
    document = _parseHtmlFile(htmlFile)
    tags = document.find_all(formInputTags)
    for tag in tags:
        if tag.name == 'input' and tag.has_attr('type') and (tag['type'] == 'submit' or tag['type'] == 'reset'):
            continue
        if not tag.has_attr('name') or not tag['name']:
            outputResults.append(str(tag.sourceline)+': '+str(tag))
    return outputResults
def _checkHtmlFiles(htmlFiles):
    if not htmlFiles: return []
    ## DO CHECKs
    results = []
    validHtmlFiles = []
    # checks on individual file
    for htmlFile in htmlFiles:
        fileName = os.path.relpath(htmlFile, projectBaseDir)
        # algemeen
        baseStructureResults = None
        pageTitleAndH1Results = None
        codeOutsideBodyResults = None
        #semanticTagsOfFileResults = None
        #upperCaseTagsResults = None
        mainResults = None
        nestedArticlesResults = None
        forbiddenTagsResults = None
        semiForbiddenTagsResults = None
        imageScalingResults = None
        imageAltInfoResults = None
        formInputTypesResults = None
        formInputNameAttrResults = None
        formInputValidationsResults = None
        try:
            baseStructureResults = _checkBaseStructure(htmlFile)
            if not baseStructureResults:
                pageTitleAndH1Results = _checkPageTitleAndH1Info(htmlFile)
                codeOutsideBodyResults = _checkCodeOutsideBody(htmlFile)
                #semanticTagsOfFileResults = _checkSemanticTagsInfoOfFile(htmlFile)
                #upperCaseTagsResults = _checkUpperCaseTags(htmlFile)
                mainResults = _checkMain(htmlFile)
                nestedArticlesResults = _checkNestedArticles(htmlFile)
                forbiddenTagsResults = _checkForbiddenTags(htmlFile)
                semiForbiddenTagsResults = _checkSemiForbiddenTags(htmlFile)
                imageScalingResults = _checkImageScaling(htmlFile)
                imageAltInfoResults = _checkImageAltInfo(htmlFile)
                formInputTypesResults = _checkFormInputTypes(htmlFile)
                formInputNameAttrResults = _checkFormInputNameAttr(htmlFile)
                formInputValidationsResults = _checkFormInputValidations(htmlFile)
        except Exception as exc:
            results.append([fileName, HtmlChecks.Error, f'Error while processing file... {type(exc).__name__}: {str(exc)}'])
            continue
        validHtmlFiles.append(htmlFile)
        results.append([fileName, HtmlChecks.BaseStructure, baseStructureResults])
        if not baseStructureResults:
            results.append([fileName, HtmlChecks.PageTitleAndH1Info, pageTitleAndH1Results])
            results.append([fileName, HtmlChecks.OutsideBody, codeOutsideBodyResults])
            #results.append([fileName, HtmlChecks.SemanticTags, semanticTagsOfFileResults])
            #results.append([fileName, HtmlChecks.UpperCaseTagNames, upperCaseTagsResults])
            results.append([fileName, HtmlChecks.Main, mainResults])
            results.append([fileName, HtmlChecks.NestedArticles, nestedArticlesResults])
            results.append([fileName, HtmlChecks.ForbiddenTags, forbiddenTagsResults])
            results.append([fileName, HtmlChecks.SemiForbiddenTags, semiForbiddenTagsResults])
            # afbeeldingen
            results.append([fileName, HtmlChecks.ImageScaling, imageScalingResults])
            results.append([fileName, HtmlChecks.ImageAltInfo, imageAltInfoResults])
            # forms
            results.append([fileName, HtmlChecks.FormInputTypes, formInputTypesResults])
            results.append([fileName, HtmlChecks.FormInputNameAttr, formInputNameAttrResults])
            results.append([fileName, HtmlChecks.FormInputValidation, formInputValidationsResults])
    # summary
    results.append([None, HtmlChecks.TagSummary, _getTagsSummaryOfFiles(validHtmlFiles, showFileNames=True)])
    results.append([None, HtmlChecks.SemanticTags, _checkSemanticTagsInfoOfFiles(validHtmlFiles)])
    return results


def _getAllFiles(dir, ext, filenamePrefix = None, recursive = True, ignoreDotDirs = True):
    files = []
    for entry in os.listdir(dir):
        fullPath = os.path.join(dir, entry)
        if os.path.isdir(fullPath):
            if ignoreDotDirs and entry.startswith('.'):
                continue
            if not entry in excludeDirs and recursive:
                files += _getAllFiles(fullPath, ext, filenamePrefix, recursive, ignoreDotDirs)
        elif fullPath.endswith('.'+ext if ext[0] != '.' else ext):
            if not filenamePrefix or entry.startswith(filenamePrefix):
                files.append(fullPath)
    return files


## MODULE (whem imported as module) ##
def checkProject(projectDir):
    # reset project-cached-data
    global parsedHtmlFiles, flatmapHtmlFiles
    parsedHtmlFiles = {}
    flatmapHtmlFiles = []
    # check project
    global projectBaseDir
    projectBaseDir = projectDir
    results = []
    htmlFiles = _getAllFiles(projectDir, '.html', recursive=doCheckSubFolders, ignoreDotDirs=excludeDotDirs)
    results += _checkHtmlFiles(htmlFiles)
    return results


## MAIN (executed as standalone script) ##
def _clearOutputFiles(outputDir, outputFilenamePrefix):
    resultFiles = _getAllFiles(outputDir, '.txt', filenamePrefix = outputFilenamePrefix)
    for resultFile in resultFiles:
        os.remove(resultFile)

def _writeResultsToOutputFile(outputFile, results, title, resultIndent = '\t', addExtraLineFeed = True):
    with open(outputFile, 'a', encoding='utf-8') as output:
        if title:
            output.write(title+'\n')
        if results:
            for result in results:
                if result[2]:
                    if result[0]:
                        output.write(f'{result[0]}'+'\n')
                    for resultLine in result[2]:
                        output.write(f'{resultIndent}{resultLine}'+'\n')
        if addExtraLineFeed:
            output.write('\n')
def _writeResultsToOutputDir(results, outputDir, outputFilenamePrefix=''):
    # SUMMARY
    outputFilename = outputFilenamePrefix+'overzicht.txt'
    outputSubTitle = None
    outputResults = filter(lambda r : r[0] == None and r[1] == HtmlChecks.TagSummary, results) if results else []
    _writeResultsToOutputFile(os.path.join(outputDir, outputFilename), outputResults, outputSubTitle, resultIndent='')
    # SYNTAX
    outputFilename = outputFilenamePrefix+'HTML-01_geldige HTML.txt'
    outputSubTitle = '*** Error ***'
    outputResults = filter(lambda r : r[1] == HtmlChecks.Error, results) if results else []
    _writeResultsToOutputFile(os.path.join(outputDir, outputFilename), outputResults, outputSubTitle)
    outputSubTitle = '*** Invalide base structure ***'
    outputResults = filter(lambda r : r[1] == HtmlChecks.BaseStructure, results) if results else []
    _writeResultsToOutputFile(os.path.join(outputDir, outputFilename), outputResults, outputSubTitle)
    outputSubTitle = '*** code_buiten_body ***'
    outputResults = filter(lambda r : r[1] == HtmlChecks.OutsideBody, results) if results else []
    _writeResultsToOutputFile(os.path.join(outputDir, outputFilename), outputResults, outputSubTitle)
    outputSubTitle = '*** verboden_tags ***'
    outputResults = filter(lambda r : r[1] == HtmlChecks.ForbiddenTags, results) if results else []
    _writeResultsToOutputFile(os.path.join(outputDir, outputFilename), outputResults, outputSubTitle)
    # SEMANTICS
    outputFilename = outputFilenamePrefix+'HTML-02_semantiek.txt'
    outputSubTitle = '*** Main ***'
    outputResults = filter(lambda r : r[1] == HtmlChecks.Main, results) if results else []
    _writeResultsToOutputFile(os.path.join(outputDir, outputFilename), outputResults, outputSubTitle)
    outputSubTitle = '*** Geneste \'article\' ***'
    outputResults = filter(lambda r : r[1] == HtmlChecks.NestedArticles, results) if results else []
    _writeResultsToOutputFile(os.path.join(outputDir, outputFilename), outputResults, outputSubTitle)
    outputSubTitle = '*** Semi-verboden_tags ***'
    outputResults = filter(lambda r : r[1] == HtmlChecks.SemiForbiddenTags, results) if results else []
    _writeResultsToOutputFile(os.path.join(outputDir, outputFilename), outputResults, outputSubTitle)
    outputSubTitle = '===== INHOUD ====='
    _writeResultsToOutputFile(os.path.join(outputDir, outputFilename), None, outputSubTitle, addExtraLineFeed=False)
    outputSubTitle = '*** specific_semantic_tags ***'
    outputResults = filter(lambda r : r[0] == None and r[1] == HtmlChecks.SemanticTags, results) if results else []
    _writeResultsToOutputFile(os.path.join(outputDir, outputFilename), outputResults, outputSubTitle)
    outputSubTitle = '*** page_title_and_h1 ***'
    outputResults = filter(lambda r : r[1] == HtmlChecks.PageTitleAndH1Info, results) if results else []
    _writeResultsToOutputFile(os.path.join(outputDir, outputFilename), outputResults, outputSubTitle)
    outputSubTitle = '*** img_alt ***'
    outputResults = filter(lambda r : r[1] == HtmlChecks.ImageAltInfo, results) if results else []
    _writeResultsToOutputFile(os.path.join(outputDir, outputFilename), outputResults, outputSubTitle)
    # IMGs
    outputFilename = outputFilenamePrefix+'M1.1-03_geschaalde afbeeldingen.txt'
    outputSubTitle = '*** onjuist_herschalen ***'
    outputResults = filter(lambda r : r[1] == HtmlChecks.ImageScaling, results) if results else []
    _writeResultsToOutputFile(os.path.join(outputDir, outputFilename), outputResults, outputSubTitle)
    # FORMs
    outputFilename = outputFilenamePrefix+'M3.1-02_variatie input elementen.txt'
    outputSubTitle = '*** input, select, textarea ***'
    outputResults = filter(lambda r : r[1] == HtmlChecks.FormInputTypes, results) if results else []
    _writeResultsToOutputFile(os.path.join(outputDir, outputFilename), outputResults, outputSubTitle)
    outputSubTitle = '*** Ontrbrekend name-attribuut ***'
    outputResults = filter(lambda r : r[1] == HtmlChecks.FormInputNameAttr, results) if results else []
    _writeResultsToOutputFile(os.path.join(outputDir, outputFilename), outputResults, outputSubTitle)
    outputFilename = outputFilenamePrefix+'M3.1-03_validatie attributenf.txt'
    outputSubTitle = '*** validatie attributen ***'
    outputResults = filter(lambda r : r[1] == HtmlChecks.FormInputValidation, results) if results else []
    _writeResultsToOutputFile(os.path.join(outputDir, outputFilename), outputResults, outputSubTitle)

def main():
    scriptDir = os.path.realpath(os.path.dirname(__file__))

    outputDir = scriptDir
    outputFilenamePrefix = 'analyse-html_'

    projectDir = scriptDir
    if (os.path.basename(projectDir) == 'auto-validation'):
        projectDir = os.path.realpath(os.path.dirname(projectDir)) # go one-direction up

    _clearOutputFiles(outputDir, outputFilenamePrefix)
    results = checkProject(projectDir)
    _writeResultsToOutputDir(results, outputDir, outputFilenamePrefix)

if __name__ == "__main__":
    main()