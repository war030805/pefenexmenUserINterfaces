#!/usr/bin/python3

#v0.4

import os
import re #regex
import cssutils # pip install cssutils
import bs4 # pip install beautifulsoup4
from enum import Enum
from collections import namedtuple

# global settings
doCheckSubFolders = True
excludeDirs = ['auto-validation','__MACOSX']
excludeDotDirs = True # directories whose names begin with '.'
projectBaseDir = '' # needed to get relative paths of project-files

# enum CSS-checks
class CssChecks(Enum):
    Error = 100; ErrorHtml = 101
    Comments = 0
    ExternStylesHttp = 11; ExternStylesLocal = 12; InternStyles = 13; InlineStyles = 14
    SemiForbiddenProperties = 21; ForbiddenProperties = 22; HiddenTitle = 23
    Grid = 31; Flexbox = 32
    DuplicatesOnSelectorLevel = 91; DuplicatesOnPropertyLevel = 92

# custom types
PropertyInfo = namedtuple('PropertyInfo', ['cssFilename', 'selector', 'property', 'value'])


## CSS files ##
parsedCssFiles = {}
def _parseCssFile(cssFile):
    global parsedCssFiles
    fileName = os.path.relpath(cssFile, projectBaseDir)
    sheet = None
    if fileName in parsedCssFiles:
        sheet = parsedCssFiles[fileName]
    else:
        sheet = cssutils.parseFile(cssFile, validate = False)
        parsedCssFiles[fileName] = sheet
    return sheet

def _flattenCssFile(cssFile):
    cssFlatMap = []
    fileName = os.path.relpath(cssFile, projectBaseDir)
    sheet = _parseCssFile(cssFile)
    for cssStyleRule in sheet.cssRules.rulesOfType(cssutils.css.CSSRule.STYLE_RULE):
        selector = cssStyleRule.selectorText
        declarationBlock = cssStyleRule.style
        for property in declarationBlock.getProperties(all=True):
            cssFlatMap.append(PropertyInfo(fileName, selector, property.name, property.value))
    return cssFlatMap
def _getUniqueIdentifier(propertyInfo, uniqueness):
    uniqueValue = ''
    if 'property' in uniqueness:
        uniqueValue = propertyInfo.property
    if 'value' in uniqueness:
        uniqueValue = uniqueValue+":"+propertyInfo.value if 'property' in uniqueness else propertyInfo.value
    if 'selector' in uniqueness:
        uniqueValue = propertyInfo.selector if len(uniqueValue) == 0 else propertyInfo.selector+'{'+uniqueValue+'}'
    return uniqueValue
def _checkCssDuplicates(cssFiles, uniqueness = ['property'], sortByAmount = True, duplicateMinimum = 1):
    cssFlatMap = []
    for cssFile in cssFiles:
        cssFlatMap += _flattenCssFile(cssFile)
    
    uniqueProperties = {}
    for propertyInfo in cssFlatMap:
        uniqueProperty = _getUniqueIdentifier(propertyInfo, uniqueness)
        if not uniqueProperty in uniqueProperties:
            uniqueProperties[uniqueProperty] = [1, []]
            uniqueProperties[uniqueProperty][1].append(propertyInfo)
        else:
            uniqueProperties[uniqueProperty][0] += 1
            uniqueProperties[uniqueProperty][1].append(propertyInfo)
    
    uniquePropertiesSorted = {key: val for key, val in sorted(uniqueProperties.items(), key=lambda item: item[1] if sortByAmount else item[0], reverse=sortByAmount)}
    #print(uniqueProperties)
    results = []
    for key,val in uniquePropertiesSorted.items():
        if (val[0] >= duplicateMinimum):
            cssFilenames = {}
            for propertyInfo in val[1]:
                cssFilename = propertyInfo.cssFilename
                if not cssFilename in cssFilenames:
                    cssFilenames[cssFilename] = 1
                else:
                    cssFilenames[cssFilename] +=1
            cssFilesInfo = ','.join(f'{key} ({val})' for key,val in cssFilenames.items())
            results.append(f'{val[0]}\t{key}\t[{cssFilesInfo}]')
    return results
def _isWantedProperty(property, condition):
    (propertyName, propertyValue) = property
    (conditionName, conditionValue) = condition
    if not conditionName and not conditionValue:
        return False
    isValid = True
    if conditionName:
        conditionNameRegex = conditionName.replace('*','.*')
        isValid = isValid and re.match(conditionNameRegex, propertyName)
    if conditionValue:
        conditionValueRegex = conditionValue.replace('*','.*')
        isValid = isValid and re.match(conditionValueRegex, propertyValue)
    return isValid
def _checkProperties(cssFile, properties, styleRuleRequiresAllProperties = False):
    propertiesWanted = []
    for item in properties:
        itemParts = item.split(':')
        if len(itemParts) == 2:
            propertyName = itemParts[0] if itemParts[0] != '' else '*'
            propertyValue = itemParts[1] if itemParts[1] != '' else '*'
            propertiesWanted.append((propertyName, propertyValue))
        elif itemParts[0] != '':
            propertiesWanted.append((itemParts[0], None))
    results = []
    sheet = _parseCssFile(cssFile)
    for cssStyleRule in sheet.cssRules.rulesOfType(cssutils.css.CSSRule.STYLE_RULE):
        selector = cssStyleRule.selectorText
        declarationBlock = cssStyleRule.style
        ruleProperties = declarationBlock.getProperties(all=True)
        foundedProperties = []
        for property in ruleProperties:
            for propertyWanted in propertiesWanted:
                if _isWantedProperty((property.name, property.value), propertyWanted):
                    foundedProperties.append((property.name, property.value))
                    break
        if foundedProperties:
            if not styleRuleRequiresAllProperties:
                results.append(selector+' { '+', '.join(prop[0]+':'+prop[1] for prop in foundedProperties)+' }')
            else:
                hasAllWantedProperties = True
                for propertyWanted in propertiesWanted:
                    isWantedFounded = False
                    for propFounded in foundedProperties:
                        isWantedFounded = isWantedFounded or _isWantedProperty((propFounded[0], propFounded[1]), propertyWanted)
                        if isWantedFounded: break
                    hasAllWantedProperties = hasAllWantedProperties and isWantedFounded
                if hasAllWantedProperties:
                    results.append(selector+' { '+', '.join(prop[0]+':'+prop[1] for prop in foundedProperties)+' }')
    return results
def _checkSemiForbiddenProperties(cssFile):
    forbiddenProperties = ['overflow']
    results = _checkProperties(cssFile, forbiddenProperties)
    return results
def _checkForbiddenProperties(cssFile):
    forbiddenProperties = ['float', ':*!important']
    results = _checkProperties(cssFile, forbiddenProperties)
    return results
def _checkGrid(cssFile):
    # check for selector with css-properties: 'display:grid','display:inline-grid','grid','grid-template-*','grid-area','justify-*','align-*','place-*','*gap'
    gridProperties = ['display:grid','display:inline-grid','grid','grid-template-*','grid-area']
    results = _checkProperties(cssFile, gridProperties)
    outputResults = []
    for result in results:
        outputResults.append(result.replace('{','{\n\t\t').replace(',',',\n\t\t'))
    return outputResults
def _checkFlexbox(cssFile):
    # check for selector with css-properties: 'display:flex','display:inline-flex','flex','flex-*','order','justify-*','align-*','*-gap'
    flexboxProperties = ['display:flex','display:inline-flex','flex','flex-*','order']
    results = _checkProperties(cssFile, flexboxProperties)
    outputResults = []
    for result in results:
        outputResults.append(result.replace('{','{\n\t\t').replace(',',',\n\t\t'))
    return outputResults
def _checkHiddenTitle(cssFile):
    # check for selector with css-properties: 'position:absolute','width:1px','height:1px','left:-10000px','float:hidden'
    hiddenTitleProperties = ['position:absolute','width','height','left','overflow:hidden']
    return _checkProperties(cssFile, hiddenTitleProperties, styleRuleRequiresAllProperties=True)
def _checkComments(cssFile):
    requiredCommentedProperties = ['position', 'box-sizing']
    results = []
    sheet = _parseCssFile(cssFile)
    # sheet loop all rules
    isPrevRuleAComment = False
    for rule in sheet.cssRules:
        #check type of rule
        if rule.type == cssutils.css.CSSRule.COMMENT:
            commentRule = rule
            # TODO: check if comment is css-code?
            results.append((None, commentRule.cssText))
            isPrevRuleAComment = True
        elif rule.type == cssutils.css.CSSRule.STYLE_RULE:
            styleRule = rule
            selector = styleRule.selectorText
            styleRuleResults = []
            styleRuleChildren = list(styleRule.style.children())
            isPrevRuleChildAComment = False
            isPrevRuleChildRequired = False
            isPrevRuleChildPartOfGap = False
            for j in range(len(styleRuleChildren)):
                isCurrentRuleChildAComment = False
                isCurrentRuleChildRequired = False
                isCurrentRuleChildPartOfGap = False
                isCurrentRuleChildStartOfGap = False
                styleRuleChild = styleRuleChildren[j]
                if isinstance(styleRuleChild, cssutils.css.csscomment.CSSComment):
                    comment = styleRuleChild
                    styleRuleResults.append(comment.cssText)
                    isCurrentRuleChildAComment = True
                if isinstance(styleRuleChild, cssutils.css.property.Property):
                    property = styleRuleChild
                    if property.name in requiredCommentedProperties:
                        styleRuleResults.append(property.cssText+';')
                        isCurrentRuleChildRequired = True
                    else:
                        isNextRuleChildAComment = False
                        if j < len(styleRuleChildren)-1:
                            isNextRuleChildAComment = isinstance(styleRuleChildren[j+1], cssutils.css.csscomment.CSSComment)
                        if isPrevRuleChildAComment or isNextRuleChildAComment:
                            styleRuleResults.append(property.cssText+';')
                        else:
                            if not isPrevRuleChildPartOfGap:
                                #fill gaps for props that doesn't needed a comment with '...'
                                styleRuleResults.append('...')
                                isCurrentRuleChildStartOfGap = True
                            else:
                                isCurrentRuleChildPartOfGap = True
                isPrevRuleChildAComment = isCurrentRuleChildAComment
                isPrevRuleChildRequired = isCurrentRuleChildRequired
                isPrevRuleChildPartOfGap = isCurrentRuleChildStartOfGap or isCurrentRuleChildPartOfGap
            if styleRuleResults and not (len(styleRuleResults) == 1 and styleRuleResults[0] == '...'):
                results.append((selector, styleRuleResults))
    outputResults = []
    for (selector, content) in results:
        if not selector:
            outputResults.append(''.join(re.sub('\s+',' ',content.replace('\n','').replace('\r',''))))
        else:
            outputResults.append(selector+' { '+'\n\t\t'+'\n\t\t'.join(re.sub('\s+',' ',item.replace('\n','').replace('\r','')) for item in content)+' }')
    return outputResults
def _checkCssFiles(cssFiles):
    if not cssFiles: return []
    ## DO CHECKs
    results = []
    validCssFiles = []
    # individual file checks
    for cssFile in cssFiles:
        fileName = os.path.relpath(cssFile, projectBaseDir)
        hiddenTitleResult = None
        semiForbiddenPropertiesResult = None
        forbiddenPropertiesResult = None
        gridResult = None
        flexboxResult = None
        commentsResult = None
        try:
            hiddenTitleResult = _checkHiddenTitle(cssFile)
            semiForbiddenPropertiesResult = _checkSemiForbiddenProperties(cssFile)
            forbiddenPropertiesResult = _checkForbiddenProperties(cssFile)
            gridResult = _checkGrid(cssFile)
            flexboxResult = _checkFlexbox(cssFile)
            commentsResult = _checkComments(cssFile)
        except Exception as exc:
            results.append([fileName, CssChecks.Error, f'Error while processing file... {type(exc).__name__}: {str(exc)}'])
            continue
        validCssFiles.append(cssFile)
        # algemeen
        results.append([fileName, CssChecks.HiddenTitle, hiddenTitleResult])
        results.append([fileName, CssChecks.SemiForbiddenProperties, semiForbiddenPropertiesResult])
        results.append([fileName, CssChecks.ForbiddenProperties, forbiddenPropertiesResult])
        # grid / flexbox
        results.append([fileName, CssChecks.Grid, gridResult])
        results.append([fileName, CssChecks.Flexbox, flexboxResult])
        # comments
        results.append([fileName, CssChecks.Comments, commentsResult])
    # duplicatie
    results.append([None, CssChecks.DuplicatesOnSelectorLevel, _checkCssDuplicates(validCssFiles, ['selector','property','value'], False, 2)])
    results.append([None, CssChecks.DuplicatesOnPropertyLevel, _checkCssDuplicates(validCssFiles, ['property','value'], True, 5)])
    return results


## HTML Files ##
parsedHtmlFiles = {}
def _parseHtmlFile(htmlFile):
    fileName = os.path.relpath(htmlFile, projectBaseDir)
    document = None
    if fileName in parsedHtmlFiles:
        document = parsedHtmlFiles[fileName]
    else:
        with open(htmlFile) as file:
            document = bs4.BeautifulSoup(file.read(), 'html.parser')
            parsedHtmlFiles[fileName] = document
    return document
def _checkExternStylesInHtml(htmlFile, local = True, external = True): # link-elementen (in head-element)
    ignoreInUrls = 'fonts'
    result = []
    document = _parseHtmlFile(htmlFile)
    linkTags = document.head.find_all('link') if document.head else []
    for linkTag in linkTags:
        if linkTag.has_attr('href'):
            if linkTag.has_attr('rel') and not 'stylesheet' in linkTag['rel']:
                continue
            hrefStartsWithHttp = re.match('http', linkTag['href'], re.IGNORECASE)
            if local and not hrefStartsWithHttp:
                result.append(str(linkTag['href']))
            if external and hrefStartsWithHttp:
                if not ignoreInUrls in linkTag['href']:
                    result.append(str(linkTag['href'])) 
        # TODO: get list of 'imports' in css-file
    return result
def _checkInternStylesInHtml(htmlFile): # style-elementen
    result = []
    document = _parseHtmlFile(htmlFile)
    styleTags = document.find_all('style')
    for styleTag in styleTags:
        result.append(str(styleTag.sourceline)+':'+str(styleTag.sourcepos))
    return result
def _checkInlineStylesInHtml(htmlFile): # style-attributen
    result = []
    document = _parseHtmlFile(htmlFile)
    tags = document.find_all(lambda tag : tag.has_attr('style'))
    for tag in tags:
        result.append(f'{str(tag.sourceline)}:{str(tag.sourcepos)} <{tag.name} style="'+tag['style']+'">')
    return result
def _checkHtmlFiles(htmlFiles):
    if not htmlFiles: return []
    ## DO CHECKs
    results = []
    for htmlFile in htmlFiles:
        fileName = os.path.relpath(htmlFile, projectBaseDir)
        externStylesHttpResult = None
        externStylesLocalResult = None
        internStylesResult = None
        inlineStylesResult = None
        try:
            externStylesHttpResult = _checkExternStylesInHtml(htmlFile, local=False, external=True)
            externStylesLocalResult = _checkExternStylesInHtml(htmlFile, local=True, external=False)
            internStylesResult = _checkInternStylesInHtml(htmlFile)
            inlineStylesResult = _checkInlineStylesInHtml(htmlFile)
        except Exception as exc:
            results.append([fileName, CssChecks.ErrorHtml, f'Error while processing file... {type(exc).__name__}: {str(exc)}'])
            continue
        results.append([fileName, CssChecks.ExternStylesHttp, externStylesHttpResult])
        results.append([fileName, CssChecks.ExternStylesLocal, externStylesLocalResult])
        results.append([fileName, CssChecks.InternStyles, internStylesResult])
        results.append([fileName, CssChecks.InlineStyles, inlineStylesResult])
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
    global parsedCssFiles, parsedHtmlFiles
    parsedCssFiles = {}
    parsedHtmlFiles = {}
    # check project
    global projectBaseDir
    projectBaseDir = projectDir
    results = []
    htmlFiles = _getAllFiles(projectDir, '.html', recursive=doCheckSubFolders, ignoreDotDirs=excludeDotDirs)
    results += _checkHtmlFiles(htmlFiles)
    cssFiles = _getAllFiles(projectDir, '.css', recursive=doCheckSubFolders, ignoreDotDirs=excludeDotDirs)
    results += _checkCssFiles(cssFiles)
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
    # ALGEMEEN
    outputFilename = outputFilenamePrefix+'CSS-02_geldige CSS.txt'
    outputSubTitle = '*** Error ***'
    outputResults = filter(lambda r : r[1] == CssChecks.Error, results) if results else []
    _writeResultsToOutputFile(os.path.join(outputDir, outputFilename), outputResults, outputSubTitle)
    outputSubTitle = '*** Verboden properties/eigenschappen ***'
    outputResults = filter(lambda r : r[1] == CssChecks.ForbiddenProperties, results) if results else []
    _writeResultsToOutputFile(os.path.join(outputDir, outputFilename), outputResults, outputSubTitle)
    outputSubTitle = '*** Semi-verboden properties/eigenschappen ***'
    outputResults = filter(lambda r : r[1] == CssChecks.SemiForbiddenProperties, results) if results else []
    _writeResultsToOutputFile(os.path.join(outputDir, outputFilename), outputResults, outputSubTitle)
    outputFilename = outputFilenamePrefix+'M2.1-05_verborgen titels.txt'
    outputSubTitle = '*** Verborgen titels ***'
    outputResults = filter(lambda r : r[1] == CssChecks.HiddenTitle, results) if results else []
    _writeResultsToOutputFile(os.path.join(outputDir, outputFilename), outputResults, outputSubTitle)
    # COMMENTS
    outputFilename = outputFilenamePrefix+'CSS-06_commentaar.txt'
    outputSubTitle = '*** Comments ***'
    outputResults = filter(lambda r : r[1] == CssChecks.Comments, results) if results else []
    _writeResultsToOutputFile(os.path.join(outputDir, outputFilename), outputResults, outputSubTitle)
    # GRID
    outputFilename = outputFilenamePrefix+'M2.1-02_gebruik Grid.txt'
    outputSubTitle = '*** Grid ***'
    outputResults = filter(lambda r : r[1] == CssChecks.Grid, results) if results else []
    _writeResultsToOutputFile(os.path.join(outputDir, outputFilename), outputResults, outputSubTitle)
    outputSubTitle = '*** Flexbox ***'
    outputResults = filter(lambda r : r[1] == CssChecks.Flexbox, results) if results else []
    _writeResultsToOutputFile(os.path.join(outputDir, outputFilename), outputResults, outputSubTitle)
    # FILES
    outputFilename = outputFilenamePrefix+'CSS-01_CSS_naam_inhoud.txt'
    outputSubTitle = '*** CSS Links ***'
    outputResults = filter(lambda r : r[1] == CssChecks.ExternStylesLocal, results) if results else []
    _writeResultsToOutputFile(os.path.join(outputDir, outputFilename), outputResults, outputSubTitle)
    outputFilename = outputFilenamePrefix+'CSS-03_geen libraries.txt'
    outputSubTitle = '*** CSS Links ***'
    outputResults = filter(lambda r : r[1] == CssChecks.ExternStylesHttp, results) if results else []
    _writeResultsToOutputFile(os.path.join(outputDir, outputFilename), outputResults, outputSubTitle)
    outputFilename = outputFilenamePrefix+'CSS-04_geen CSS in HTML.txt'
    outputSubTitle = '*** Error HTML ***'
    outputResults = filter(lambda r : r[1] == CssChecks.ErrorHtml, results) if results else []
    _writeResultsToOutputFile(os.path.join(outputDir, outputFilename), outputResults, outputSubTitle)
    outputSubTitle = '*** Intern styles: <style>...</style> ***'
    outputResults = filter(lambda r : r[1] == CssChecks.InternStyles, results) if results else []
    _writeResultsToOutputFile(os.path.join(outputDir, outputFilename), outputResults, outputSubTitle)
    outputSubTitle = '*** Inline styles: style="..." ***'
    outputResults = filter(lambda r : r[1] == CssChecks.InlineStyles, results) if results else []
    _writeResultsToOutputFile(os.path.join(outputDir, outputFilename), outputResults, outputSubTitle)
    # DUPLICATIE
    outputFilename = outputFilenamePrefix+'CSS-05_duplicate opmaak.txt'
    outputSubTitle = '*** selector/property/value combinatie ***'
    outputResults = filter(lambda r : r[1] == CssChecks.DuplicatesOnSelectorLevel, results) if results else []
    _writeResultsToOutputFile(os.path.join(outputDir, outputFilename), outputResults, outputSubTitle, resultIndent='')
    outputSubTitle = '*** property/value combinatie ***'
    outputResults = filter(lambda r : r[1] == CssChecks.DuplicatesOnPropertyLevel, results) if results else []
    _writeResultsToOutputFile(os.path.join(outputDir, outputFilename), outputResults, outputSubTitle, resultIndent='')

def main():
    scriptDir = os.path.realpath(os.path.dirname(__file__))

    outputDir = scriptDir
    outputFilenamePrefix = 'analyse-css_'

    projectDir = scriptDir
    if (os.path.basename(projectDir) == 'auto-validation'):
        projectDir = os.path.realpath(os.path.dirname(projectDir)) # go one-direction up
    
    _clearOutputFiles(outputDir, outputFilenamePrefix)
    results = checkProject(projectDir)
    _writeResultsToOutputDir(results, outputDir, outputFilenamePrefix)

if __name__ == "__main__":
    main()