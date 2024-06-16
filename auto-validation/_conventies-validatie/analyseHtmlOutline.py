#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""analyseHtmlOutline.py: Check outline Conventions."""

__author__ = "Kenneth De Keulenaer, Jan Celis, Jeroen Reinenbergh"
__copyright__ = "Copyright 2023, The Autovalidation Project"
__credits__ = ["Kenneth De Keulenaer", "Jan Celis", "Jeroen Reinenbergh"]
__license__ = "GPL"
__version__ = "2.0.0"
__maintainer__ = "Kenneth De Keulenaer"
__email__ = "kenneth.dekeulenaer@kdg.be"
__status__ = "Production"

from importlib.resources import path
import os
import os.path
import re
import bs4
from bs4.element import NavigableString
import argparse


# global settings
doCheckSubFolders = True
excludeDirs = ['auto-validation','__MACOSX']
excludeDotDirs = True # directories whose names begin with '.'
projectBaseDir = '' # needed to get relative paths of project-files

outputFilename = "validatie-01_html-01_kdg-outline.txt"
okSuffix = '_OK'


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

def _deleteDisplayedText(soup):
    new_children = []
    for child in soup.contents:
        if not isinstance(child, NavigableString):
            new_children.append(_deleteDisplayedText(child))
    soup.contents = new_children
    return soup
def _deleteNonOutlineTags(soup, removeSectioningRootTags=False):
    sectioningRootElements = [] # ['figure', 'blockquote', 'details', 'dialog', 'fieldset', 'td']
    for tag in soup:
        if isinstance(tag, bs4.Tag):
            if removeSectioningRootTags and tag.name in sectioningRootElements:
                tag.extract() # remove element (with content)
                continue
            if not (tag.name in sectioningElements or headingRegex.match(tag.name)):
                tag.unwrap()
                _deleteNonOutlineTags(soup)
            else:
                _deleteNonOutlineTags(tag)
def _getOutlineSkeleton(soup):
    soup = _deleteDisplayedText(soup)
    #print(soup.prettify())
    _deleteNonOutlineTags(soup)
    #print(soup.prettify())
    return soup

def _hasPreviousSiblingSectioningElement(tag):
    hasPrevSiblingSectioningElement = False
    for prevSibling in tag.previous_siblings:
        if isinstance(prevSibling, bs4.Tag):
            if prevSibling.name in sectioningElements:
                hasPrevSiblingSectioningElement = True
                break
    return hasPrevSiblingSectioningElement
def _pairwiseSum(tuple1, tuple2):
    return tuple(list1 + list2 for (list1, list2) in zip(tuple1, tuple2))
def _checkOutline(soup, level=0):
    headingCount = 0
    prevSectioningCount = 0
    errors = ([], [], [])
    for tag in soup:
        if isinstance(tag, bs4.Tag):
            headingMatch = headingRegex.match(tag.name)
            if tag.name in sectioningElements:
                _, _, nestedErrors = _checkOutline(tag, level + 1)
                errors = _pairwiseSum(errors, nestedErrors)
            elif headingMatch:
                if _hasPreviousSiblingSectioningElement(tag) and headingCount == 0:
                    prevSectioningCount += 1
                headingCount += 1
                headingLevel = int(headingMatch.group(1))
                if headingLevel != level:
                    errors[1].append(tag.sourceline)
            else:
                if _hasPreviousSiblingSectioningElement(tag) and headingCount == 0:
                    prevSectioningCount += 1
                nestedHeadingCount, nestedPrevSectioningCount, nestedErrors = _checkOutline(tag, level)
                headingCount += nestedHeadingCount
                prevSectioningCount += nestedPrevSectioningCount
                errors = _pairwiseSum(errors, nestedErrors)
    if soup.name in sectioningElements:
        if (headingCount == 0 and level > 0) or prevSectioningCount > 0:
            errors[0].append(soup.sourceline)
        if headingCount > 1:
            errors[2].append(soup.sourceline)
    return headingCount, prevSectioningCount, errors

def getHtmlOutlineSkeleton(filePath):
    soup = _parseHtmlFile(filePath)
    htmlOutlineSkeleton = _getOutlineSkeleton(soup)
    return htmlOutlineSkeleton

def checkOutline(filePath):
    soup = _parseHtmlFile(filePath)
    soupOfOutlineSkeleton = _getOutlineSkeleton(soup)
    _, _, errors = _checkOutline(soupOfOutlineSkeleton)
    return errors


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


def _checkProject(projectDir):
    # reset project-cached-data
    global parsedHtmlFiles
    parsedHtmlFiles = {}
    # check project
    global projectBaseDir
    projectBaseDir = projectDir
    results = []
    for file in _getAllFiles(projectDir, '.html', recursive=doCheckSubFolders, ignoreDotDirs=excludeDotDirs):
        fileName = os.path.relpath(file, projectBaseDir)
        try:
            outlineErrors = checkOutline(file)
            if outlineErrors:
                results.append([fileName, outlineErrors])
        except TypeError as err:
            results.append([fileName, 'Is propably empty...'])
        except BaseException as err:
            results.append([fileName, f'Error while processing file... {type(err).__name__}: {str(err)}'])
    return results


def _clearOutputFile(outputFile):
    if os.path.exists(outputFile):
        os.remove(outputFile)
    # OK-variant
    outputPathInfo = os.path.split(outputFile)
    outputFilenameInfo = os.path.splitext(outputPathInfo[1])
    okOutputFile = os.path.join(outputPathInfo[0], outputFilenameInfo[0]+okSuffix+outputFilenameInfo[1])
    if os.path.exists(okOutputFile):
        os.remove(okOutputFile)

def _formatErrorOutput(errorLines, errorType):
    if errorLines:
        return f'\t{errorType}: {"; ".join(sorted([str(errorLine) for errorLine in errorLines]))}\n'
    else:
        return ''
def _formatOutlineErrors(outlineErrors):
    if type(outlineErrors) is str:
        return '\t'+outlineErrors
    output = ''
    (outline_untitled, outline_levelConflict, outline_multipleHeadings) = outlineErrors
    output += _formatErrorOutput(outline_untitled, '[Outline] Untitled')
    output += _formatErrorOutput(outline_levelConflict, '[Outline] Level conflict')
    output += _formatErrorOutput(outline_multipleHeadings, '[Outline] Multiple headings')
    return output
def _formatOutlineResult(results):
    outputText = ''
    for result in results:
        fileName = result[0]
        errors = result[1]
        if errors[0] or errors[1] or errors[2]:
            output = _formatOutlineErrors(errors)
            outputText += fileName + '\n' + output + '\n'
    return outputText[:-1]
def _writeResultsToOutputFile(outputFile, content):
    # write outputtext
    if not content:
        outputPathInfo = os.path.split(outputFile)
        outputFilenameInfo = os.path.splitext(outputPathInfo[1])
        outputFile = os.path.join(outputPathInfo[0], outputFilenameInfo[0]+okSuffix+outputFilenameInfo[1])
    with open(outputFile, 'a', encoding='utf-8') as output:
        output.write(content)


def checkProject(projectDir, outputToFile=True):
    outputDir = projectDir
    outputFile = os.path.join(outputDir, outputFilename)

    if outputToFile:_clearOutputFile(outputFile)
    results = _checkProject(projectDir)
    if outputToFile:_writeResultsToOutputFile(outputFile, _formatOutlineResult(results))    
    return results


## MAIN (executed as standalone script) ##
def main():
    scriptDir = os.path.realpath(os.path.dirname(__file__))

    outputDir = scriptDir
    outputFile = os.path.join(outputDir, outputFilename)
    
    projectDir = scriptDir
    if (os.path.basename(projectDir) == 'auto-validation'):
        projectDir = os.path.realpath(os.path.dirname(projectDir)) # go one-direction up

    _clearOutputFile(outputFile)
    results = _checkProject(projectDir)
    _writeResultsToOutputFile(outputFile, results)

if __name__ == "__main__":
    main()