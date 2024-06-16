#!/usr/bin/python3

#v0.4

import os
import re #regex
import esprima # pip install esprima
import bs4 # pip install beautifulsoup4
from enum import Enum
from collections import namedtuple

# global settings
doCheckSubFolders = True
excludeDirs = ['auto-validation','__MACOSX']
excludeDotDirs = True # directories whose names begin with '.'
projectBaseDir = '' # needed to get relative paths of project-files

# enum JavaScript-checks
class JsChecks(Enum):
    Error = 100; ErrorHtml = 101
    SourceType = 11; StrictMode = 12; InternScript = 13
    GlobalVariables = 21; VarVariables = 22; UndeclaredVariables = 23
    EventLevelHandling = 31; EventAttributeHandling = 32

# custom types
ScopeInfo = namedtuple('ScopeInfo', ['level','type','variables','range','children','parent'])
VariableInfo = namedtuple('VariableInfo', ['name', 'kind', 'type', 'initialValue', 'scopeInfo', 'line', 'column','range'])


## JS files ##
parsedJsFiles = {}
def _parseJsFile(jsFile):
    global parsedJsFiles
    fileName = os.path.relpath(jsFile, projectBaseDir)
    script = None
    if fileName in parsedJsFiles:
        script = parsedJsFiles[fileName]
    else:
        f = open(jsFile, encoding='utf-8')
        fileContent = f.read()
        f.close()
        # info: always parse as module, because .parseScript(...) gives error even if script only has 'import' en no 'export' declaration
        script = esprima.parseModule(fileContent, {'comment': True, 'loc': True, 'range': True, 'tokens': True})
        # fix: check if js-file is 'script' instead of 'module', and modify 'sourceType' from 'module' to 'script'
        scriptType = script.type if hasattr(script, 'type') else ''
        if scriptType == 'Program':
            isModule = False
            for node in script.body:
                if node.type == 'ExportDeclaration' or node.type == 'ExportDefaultDeclaration':
                    isModule = True
                    break
            if not isModule:
                script.sourceType = 'script'
        parsedJsFiles[fileName] = script
    return script
def _checkSourceType(jsFile):
    lex = _parseJsFile(jsFile)
    return [lex.sourceType]
def _checkStrictMode(jsFile):
    lex = _parseJsFile(jsFile)
    if not lex.body:
        return
    firstObject = lex.body[0]
    if firstObject.directive == 'use strict':
        return ['OK']
    return ['NOK']
def _getVariables(node, scopeInfo):
    variables = scopeInfo.variables
    if hasattr(node, 'type'):
        name = None
        kind = None
        type = None
        initialValue = None
        line = None
        column = None
        range = None
        if node.type == "VariableDeclaration":
            # vb 'let name = ...;'
            for declaration in node.declarations:
                name = declaration.id.name
                kind = node.kind if hasattr(node, 'kind') else None
                type = 'declaration'
                if declaration.init: 
                    initialValue = declaration.init.value
                if hasattr(declaration.id, 'loc'): 
                    line = declaration.id.loc.start.line
                    column = declaration.id.loc.start.column
                if hasattr(declaration.id, 'range'): 
                    range = declaration.id.range
                variables.append(VariableInfo(name, kind, type, initialValue, scopeInfo, line, column, range))
        elif node.type == "ExpressionStatement":
            # vb 'name;' # geeft ook runtime-error
            if node.expression.type == "Identifier":
                type = 'undeclared'
                name = node.expression.name
                if hasattr(node.expression, 'loc'): 
                    line = node.expression.loc.start.line
                    column = node.expression.loc.start.column
                if hasattr(node.expression, 'range'): 
                    range = node.expression.range
                variables.append(VariableInfo(name, kind, type, initialValue, scopeInfo, line, column, range))
        elif node.type == "AssignmentExpression":
            # vb 'name = ...;' / 'name. ... = ...;' / 'name[...] = ...;'
            type = 'assignment'
            if node.left.type == "Identifier":
                name = node.left.name
            else:
                ids = []
                def findIdentifiers(nodeProp):
                    localIds = []
                    if hasattr(nodeProp, 'type') and nodeProp.type == 'Identifier':
                        localIds.append(nodeProp.name)
                    else:
                        try:
                            for attr, value in vars(nodeProp).items():
                                localIds += findIdentifiers(value)
                        except:
                            pass # ignore
                    return localIds
                ids += findIdentifiers(node)
                name = ids[0]
            if hasattr(node.left, 'loc'): 
                line = node.left.loc.start.line
                column = node.left.loc.start.column
            if hasattr(node.left, 'range'): 
                range = node.left.range
            variables.append(VariableInfo(name, kind, type, initialValue, scopeInfo, line, column, range))
        elif node.type in ['FunctionDeclaration','FunctionExpression','ArrowFunctionExpression']:
            # vb 'function X(...) {...}' / 'function(...) {...}' / '(...) => {...}' / '(...) => ...'
            for param in node.params:
                type = 'parameter'
                if param.type == 'Identifier':
                    name = param.name
                    if hasattr(param, 'loc'): 
                        line = param.loc.start.line
                        column = param.loc.start.column
                    if hasattr(param, 'range'): 
                        range = param.range
                elif param.type == 'AssignmentExpression':
                    name = param.left.name
                    initialValue = param.right.value if param.right.type == 'Literal' else None
                    if hasattr(param.left, 'loc'): 
                        line = param.left.loc.start.line
                        column = param.left.loc.start.column
                    if hasattr(param.left, 'range'): 
                        range = param.left.range
                variables.append(VariableInfo(name, kind, type, initialValue, scopeInfo, line, column, range))
def _getScopeTree(node, parentScope = None):
    if isinstance(node, list):
        for subnode in node:
            _getScopeTree(subnode, parentScope)
    nodeType = node.type if hasattr(node, 'type') else ''
    scopeInfo = None
    if not parentScope or nodeType == 'Program':
        nodeSourceType = node.sourceType if hasattr(node, 'sourceType') else ''
        if not nodeSourceType == 'module':
            nodeSourceType = 'global'
        scopeInfo = ScopeInfo(0, nodeSourceType, [], None, [], None)
        _getScopeTree(node.body, scopeInfo)
    elif nodeType == 'BlockStatement':
        scopeInfo = ScopeInfo(parentScope.level+1, 'block', [], None, [], parentScope)
        parentScope.children.append(scopeInfo)
        _getScopeTree(node.body, scopeInfo)
    elif nodeType in ['FunctionDeclaration','FunctionExpression','ArrowFunctionExpression']:
        scopeType = 'function'
        if nodeType == 'ArrowFunctionExpression' and not node.body.type == 'BlockStatement':
            scopeType = 'arrowexpression'
        scopeInfo = ScopeInfo(parentScope.level+1, scopeType, [], None, [], parentScope)
        parentScope.children.append(scopeInfo)
        # (arrow-)function wit code-block syntax => function-node and block-statement same scope!
        body = node.body
        if node.body.type == 'BlockStatement':
            body = body.body
        _getScopeTree(body, scopeInfo)
    else:
        try:
            scopeInfo = parentScope
            for attr, value in vars(node).items():
                _getScopeTree(value, scopeInfo)
        except:
            pass # ignore Exceptiovn

    _getVariables(node, scopeInfo)
    return scopeInfo
def _variableInfosToOutputResult(variableInfos):
    uniqueVariables = {}
    for variableInfo in variableInfos:
        if not variableInfo.name in uniqueVariables:
            uniqueVariables[variableInfo.name] = [variableInfo]
        else:
            uniqueVariables[variableInfo.name].append(variableInfo)
    outputResults = []
    for key, val in uniqueVariables.items():
        locations = ', '.join(str(varInfo.line)+':'+str(varInfo.column)+'(depth:'+str(varInfo.scopeInfo.level)+')' for varInfo in val)
        outputResults.append(f'{key:<20}\t\t{locations}')
    return outputResults
def _checkGlobalDeclaredVariables(jsFile):
    lex = _parseJsFile(jsFile)
    scopeTree = _getScopeTree(lex)
    # global declared variables
    globalDeclaredVariables = list(filter(lambda v: v.type == 'declaration', scopeTree.variables))
    def findVarDeclaredVariablesOutsideFunctions(scopeInfo):
        varVariables = []
        if not scopeInfo == 'function':
            varVariables = list(filter(lambda v: v.type == 'declaration' and v.kind == 'var', scopeInfo.variables))
            # search child scopes
            for childScopeInfo in scopeInfo.children:
                varVariables += findVarDeclaredVariablesOutsideFunctions(childScopeInfo)
        return varVariables
    for childScopeInfo in scopeTree.children:
        if not childScopeInfo.type == 'function':
            globalDeclaredVariables += findVarDeclaredVariablesOutsideFunctions(childScopeInfo)
    return _variableInfosToOutputResult(globalDeclaredVariables)
def _checkAllVarDeclaredVariables(jsFile):
    lex = _parseJsFile(jsFile)
    scopeTree = _getScopeTree(lex)
    # all 'var' declared variables
    def findVarDeclaredVariables(scopeInfo):
        varVariables = list(filter(lambda v: v.type == 'declaration' and v.kind == 'var', scopeInfo.variables))
        # search child scopes
        for childScopeInfo in scopeInfo.children:
            varVariables += findVarDeclaredVariables(childScopeInfo)
        return varVariables
    allVarDeclaredVariables = findVarDeclaredVariables(scopeTree)
    return _variableInfosToOutputResult(allVarDeclaredVariables)
def _findUndeclaredVariables(scopeInfo, checkChildScopes = True, ignoreVariableNames = [], topParentScopeInfo = None):
    undeclaredVariables = []
    topScopeInfo = topParentScopeInfo if topParentScopeInfo else scopeInfo
    def isVariableDeclaredInScope(name, scopeInfo):
        declarationFound = False
        for scopeVariableIfo in scopeInfo.variables:
            if  scopeVariableIfo.name == name and scopeVariableIfo.type in ['declaration','parameter']:
                declarationFound = True
                break
        return declarationFound
    def isVariableDeclaredInScopeTree(name, scopeInfo):
        declarationFound = False
        parentScope = None
        while not declarationFound:
            declarationFound = isVariableDeclaredInScope(name, parentScope if parentScope else scopeInfo )
            if declarationFound:
                break
            elif scopeInfo.parent and not scopeInfo == topScopeInfo and not parentScope == topScopeInfo:
                parentScope = parentScope.parent if parentScope else scopeInfo.parent
            else:
                break
        return declarationFound
    for variableInfo in scopeInfo.variables:
        if (variableInfo.type == 'undeclared' or variableInfo.type == 'assignment'):
            variableName = variableInfo.name
            if not isVariableDeclaredInScopeTree(variableName, scopeInfo):
                if not (variableName in ignoreVariableNames):
                    undeclaredVariables.append(variableInfo)
    # search child scopes
    if checkChildScopes:
        for childScopeInfo in scopeInfo.children:
            undeclaredVariables += _findUndeclaredVariables(childScopeInfo, ignoreVariableNames=ignoreVariableNames, topParentScopeInfo=topScopeInfo)
    return undeclaredVariables
def _checkGlobalUndeclaredVariables(jsFile):
    lex = _parseJsFile(jsFile)
    scopeTree = _getScopeTree(lex)
    # undeclared variables
    undeclaredVariables = _findUndeclaredVariables(scopeTree, checkChildScopes=True, ignoreVariableNames=['window','document'])
    return _variableInfosToOutputResult(undeclaredVariables)
def _checkEventLevelHandling(jsFile):
    lex = _parseJsFile(jsFile)
    if not lex.tokens:
        return
    #possibleEventMembers = list(filter(lambda token: token.name.startsWith('on') and token.type == 'Identifier', lex.tokens))
    possibleEventMembers = []
    for index, token in enumerate(lex.tokens):
        if token.type == 'Identifier' and token.value.startswith('on'):
            if index > 0:
                prevToken = lex.tokens[index-1]
                if prevToken.type == 'Punctuator' and prevToken.value == '.':
                    possibleEventMembers.append(token)
    outputResults = []
    for token in possibleEventMembers:
        outputResults.append(f'{token.value:<15}\t{token.loc.start.line}:{token.loc.start.column}')
    return outputResults
def _checkJsFiles(jsFiles):
    if not jsFiles: return []
    ## DO CHECKs
    results = []
    for jsFile in jsFiles:
        fileName = os.path.relpath(jsFile, projectBaseDir)
        sourceTypeResults = None
        strictModeResults = None
        globalDeclaredVariablesResults = None
        varDeclaredVariablesResults = None
        globalUndeclaredVariablesResults = None
        eventLevelHandlingResults = None
        try:
            sourceTypeResults = _checkSourceType(jsFile)
            strictModeResults = _checkStrictMode(jsFile)
            globalDeclaredVariablesResults = _checkGlobalDeclaredVariables(jsFile)
            varDeclaredVariablesResults = _checkAllVarDeclaredVariables(jsFile)
            globalUndeclaredVariablesResults = _checkGlobalUndeclaredVariables(jsFile)
            eventLevelHandlingResults = _checkEventLevelHandling(jsFile)
        except Exception as exc:
            results.append([fileName, JsChecks.Error, f'Error while processing file... {type(exc).__name__}: {str(exc)}'])
            continue
        # info
        results.append([fileName, JsChecks.SourceType, sourceTypeResults])
        results.append([fileName, JsChecks.StrictMode, strictModeResults])
        # variables
        results.append([fileName, JsChecks.GlobalVariables, globalDeclaredVariablesResults])
        results.append([fileName, JsChecks.VarVariables, varDeclaredVariablesResults])
        results.append([fileName, JsChecks.UndeclaredVariables, globalUndeclaredVariablesResults])
        # events
        results.append([fileName, JsChecks.EventLevelHandling, eventLevelHandlingResults])
    return results


## HTML Files ##
parsedHtmlFiles = {}
def _parseHtmlFile(htmlFile):
    global parsedHtmlFiles
    fileName = os.path.relpath(htmlFile, projectBaseDir)
    document = None
    if fileName in parsedHtmlFiles:
        document = parsedHtmlFiles[fileName]
    else:
        with open(htmlFile) as file:
            document = bs4.BeautifulSoup(file.read(), 'html.parser')
            parsedHtmlFiles[fileName] = document
    return document
def _checkInternJavaScript(htmlFile):
    outputResult = []
    document = _parseHtmlFile(htmlFile)
    tags = document.find_all('script')
    results = {}
    for tag in tags:
        if re.search('\w', tag.text):
            if tag.name in results:
                results[tag.name].append(str(tag.sourceline))#+':'+str(tag.sourcepos))
            else:
                results[tag.name] = [str(tag.sourceline)]#+':'+str(tag.sourcepos)]
    for key,val in results.items():
        outputResult.append('<'+key+'>: '+'; '.join(val))
    return outputResult
def _checkEventAttributeHandling(htmlFile): # = DOM Events Level 0
    outputResult = []
    document = _parseHtmlFile(htmlFile)
    def getEventAttributes(tag):
        return [k+'="'+v+'"' for k,v in tag.attrs.items() if k.startswith('on')]
    def hasEventAttribute(tag):
        return True if getEventAttributes(tag) else False
    tags = document.find_all(lambda tag : hasEventAttribute(tag))
    for tag in tags:
        outputResult.append(str(tag.sourceline)+': <'+str(tag.name)+' '+' '.join(getEventAttributes(tag))+'>')
    return outputResult
def _checkHtmlFiles(htmlFiles):
    if not htmlFiles: return []
    # DO CHECKs
    results = []
    for htmlFile in htmlFiles:
        fileName = os.path.relpath(htmlFile, projectBaseDir)
        internJavaScriptResults = None
        eventAttributeHandlingResults = None
        try:
            internJavaScriptResults = _checkInternJavaScript(htmlFile)
            eventAttributeHandlingResults = _checkEventAttributeHandling(htmlFile)
        except Exception as exc:
            results.append([fileName, JsChecks.ErrorHtml, f'Error while processing file... {type(exc).__name__}: {str(exc)}'])
            continue
        # intern scripts
        results.append([fileName, JsChecks.InternScript, internJavaScriptResults])
        # events
        results.append([fileName, JsChecks.EventAttributeHandling, eventAttributeHandlingResults])
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
    global parsedJsFiles, parsedHtmlFiles
    parsedJsFiles = {}
    parsedHtmlFiles = {}
    # check project
    global projectBaseDir
    projectBaseDir = projectDir
    results = []
    htmlFiles = _getAllFiles(projectDir, '.html', recursive=doCheckSubFolders, ignoreDotDirs=excludeDotDirs)
    results += _checkHtmlFiles(htmlFiles)
    jsFiles = _getAllFiles(projectDir, '.js', recursive=doCheckSubFolders, ignoreDotDirs=excludeDotDirs)
    results += _checkJsFiles(jsFiles)
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
    # INFO
    outputFilename = outputFilenamePrefix+'algemeen.txt'
    outputSubTitle = '*** script type ***'
    outputResults = filter(lambda r : r[1] == JsChecks.SourceType, results) if results else []
    _writeResultsToOutputFile(os.path.join(outputDir, outputFilename), outputResults, outputSubTitle)
    outputSubTitle = '*** strict-mode ***'
    outputResults = filter(lambda r : r[1] == JsChecks.StrictMode, results) if results else []
    _writeResultsToOutputFile(os.path.join(outputDir, outputFilename), outputResults, outputSubTitle)
    # FILES
    outputFilename = outputFilenamePrefix+'JS-01_bestand.txt'
    outputSubTitle = '*** Error HTML ***'
    outputResults = filter(lambda r : r[1] == JsChecks.ErrorHtml, results) if results else []
    _writeResultsToOutputFile(os.path.join(outputDir, outputFilename), outputResults, outputSubTitle)
    outputSubTitle = '*** Intern: <script>...</script> ***'
    outputResults = filter(lambda r : r[1] == JsChecks.InternScript, results) if results else []
    _writeResultsToOutputFile(os.path.join(outputDir, outputFilename), outputResults, outputSubTitle)
    # VARIABLES
    outputFilename = outputFilenamePrefix+'JS-02_geldige JavaScript.txt'
    outputSubTitle = '*** Error ***'
    outputResults = filter(lambda r : r[1] == JsChecks.Error, results) if results else []
    _writeResultsToOutputFile(os.path.join(outputDir, outputFilename), outputResults, outputSubTitle)
    outputSubTitle = '*** All "var" declared variables ***'
    outputResults = filter(lambda r : r[1] == JsChecks.VarVariables, results) if results else []
    _writeResultsToOutputFile(os.path.join(outputDir, outputFilename), outputResults, outputSubTitle)
    outputSubTitle = '*** Global declared variables ***'
    outputResults = filter(lambda r : r[1] == JsChecks.GlobalVariables, results) if results else []
    _writeResultsToOutputFile(os.path.join(outputDir, outputFilename), outputResults, outputSubTitle)
    outputSubTitle = '*** Undeclared/leaked variables ***'
    outputResults = filter(lambda r : r[1] == JsChecks.UndeclaredVariables, results) if results else []
    _writeResultsToOutputFile(os.path.join(outputDir, outputFilename), outputResults, outputSubTitle)
    # EVENTS
    outputFilename = outputFilenamePrefix+'JS-04_DOM Events.txt'
    outputSubTitle = '*** Html-attribute event-handling: on...="..." ***'
    outputResults = filter(lambda r : r[1] == JsChecks.EventAttributeHandling, results) if results else []
    _writeResultsToOutputFile(os.path.join(outputDir, outputFilename), outputResults, outputSubTitle)
    outputSubTitle = '*** DOM Events Level 0: <element>.on... = ... ***'
    outputResults = filter(lambda r : r[1] == JsChecks.EventLevelHandling, results) if results else []
    _writeResultsToOutputFile(os.path.join(outputDir, outputFilename), outputResults, outputSubTitle)

def main():
    scriptDir = os.path.realpath(os.path.dirname(__file__))

    outputDir = scriptDir
    outputFilenamePrefix = 'analyse-js_'

    projectDir = scriptDir
    if (os.path.basename(projectDir) == 'auto-validation'):
        projectDir = os.path.realpath(os.path.dirname(projectDir)) # go one-direction up

    _clearOutputFiles(outputDir, outputFilenamePrefix)
    results = checkProject(projectDir)
    _writeResultsToOutputDir(results, outputDir, outputFilenamePrefix)

if __name__ == "__main__":
    main()