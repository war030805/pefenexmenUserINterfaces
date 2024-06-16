try:
    ## MODULE (when loaded as module) ##
    from .analyseHtml import checkProject as _checkHtml, HtmlChecks
    from .analyseCss import checkProject as _checkCss, CssChecks
    from .analyseJs import checkProject as _checkJs, JsChecks
except ImportError:
    ## SCRIPT (when run as script) ##
    from analyseHtml import checkProject as _checkHtml, HtmlChecks
    from analyseCss import checkProject as _checkCss, CssChecks
    from analyseJs import checkProject as _checkJs, JsChecks

import os
import argparse
from enum import Enum

# global settings
excludeDirs = ['auto-validation']
outputFilenameHtml = 'validatie-01_html-01_kdg-algemeen.txt'
outputFilenameHtmlProject = 'validatie-01_html-02_kdg-project.txt'
outputFilenameHtmlInfo = 'validatie-01_html-03_kdg-info.txt'
outputFilenameCss = 'validatie-02_css-01_kdg-algemeen.txt'
outputFilenameCssProject = 'validatie-02_css-02_kdg-project.txt'
outputFilenameCssInfo = 'validatie-02_css-03_kdg-info.txt'
outputFilenameJs = 'validatie-03_js-01_kdg-algemeen.txt'
outputFilenameJsProject = 'validatie-03_js-02_kdg-project.txt'
outputFilenameJsInfo = 'validatie-03_js-03_kdg-info.txt'
okSuffix = '_OK'

checkHtml = True
checkCss = True
checkJavaScript = True
analyseLevel = 1 # = Normal
splitOutputPerCriteria = False

class AnalyseLevel(Enum):
    Normal = 1
    Full = 2

def _analyseProject(projectDir):
    #print(f'{projectDir}')
    results = {}

    # HTML
    if checkHtml:
        try:
            results["html"] = _checkHtml(projectDir)
        except Exception as e:
            results["html"] = {"error":str(e)}
    # CSS
    if checkCss:
        try:
            results["css"] = _checkCss(projectDir)
        except Exception as e:
            results["css"] = {"error":str(e)}
    # JS
    if checkJavaScript:
        try:
            results["js"] = _checkJs(projectDir)
        except Exception as e:
            results["js"] = {"error":str(e)}

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

def _clearOutputFile(outputFile):
    if os.path.exists(outputFile):
        os.remove(outputFile)
    # OK-variant
    outputPathInfo = os.path.split(outputFile)
    outputFilenameInfo = os.path.splitext(outputPathInfo[1])
    okOutputFile = os.path.join(outputPathInfo[0], outputFilenameInfo[0]+okSuffix+outputFilenameInfo[1])
    if os.path.exists(okOutputFile):
        os.remove(okOutputFile)

def _clearOutputFiles(outputDir):
    _clearOutputFile(os.path.join(outputDir, outputFilenameHtml))
    _clearOutputFile(os.path.join(outputDir, outputFilenameHtmlProject))
    _clearOutputFile(os.path.join(outputDir, outputFilenameHtmlInfo))
    _clearOutputFile(os.path.join(outputDir, outputFilenameCss))
    _clearOutputFile(os.path.join(outputDir, outputFilenameCssProject))
    _clearOutputFile(os.path.join(outputDir, outputFilenameCssInfo))
    _clearOutputFile(os.path.join(outputDir, outputFilenameJs))
    _clearOutputFile(os.path.join(outputDir, outputFilenameJsProject))
    _clearOutputFile(os.path.join(outputDir, outputFilenameJsInfo))

def _getCheckTypeResult(results, checkType, projectLevel=False):
    return list(filter(lambda r : (r[0] == None if projectLevel else True) and r[1] == checkType, results)) if results else []

def _formatCheckResult(results, title = None, resultIndent = '\t'):
    output = ''
    isTitleAdded = False
    if results:
        for result in results:
            if result[2]:
                if title and not isTitleAdded:
                    output += f'{title}'+'\n'
                    isTitleAdded = True
                if result[0]:
                    output += f'{result[0]}'+'\n'
                if type(result[2]) is str:
                    output += f'{resultIndent}{result[2]}'+'\n'
                else:
                    for resultLine in result[2]:
                        output += f'{resultIndent}{resultLine}'+'\n'
    return output[:-1]

def _formatMultipleCriteriaResult(results):
    outputText = ""
    # create outputtext
    isFirstCriteriaAdded = False
    for criteria,checks in results.items():
        isCriteriaTitleAdded = False
        isFirstCheckResultAdded = False
        for check,result in checks.items():
            indent = '\t'
            if type(result) is tuple:
                indent = result[1]
                result = result[0]
            resultFormatted = _formatCheckResult(result, f'*** {check} ***', indent)
            if resultFormatted:
                # add criteria-title
                if not isCriteriaTitleAdded:
                    if not isFirstCriteriaAdded:
                        outputText += '=== '+criteria+' ==='+'\n'
                        isFirstCriteriaAdded = True
                    else:
                        outputText += '\n\n'+'=== '+criteria+' ==='+'\n'
                    isCriteriaTitleAdded = True   
                # add resultformatted (title+result)
                if not isFirstCheckResultAdded:
                    outputText += resultFormatted+'\n'
                else:
                    outputText += '\n'+resultFormatted+'\n'
                isFirstCheckResultAdded = True
    return outputText

def _writeResultsToOutputFile(outputFile, content):
    # write outputtext
    if not content:
        outputPathInfo = os.path.split(outputFile)
        outputFilenameInfo = os.path.splitext(outputPathInfo[1])
        outputFile = os.path.join(outputPathInfo[0], outputFilenameInfo[0]+okSuffix+outputFilenameInfo[1])
    with open(outputFile, 'a', encoding='utf-8') as output:
        output.write(content)

def _writeHtmlResultsToOutputDir(outputDir, results):
    criteriaList = []
    # OUTPUTFILE: validatie-html-kdg.txt
    outputFile = os.path.join(outputDir, outputFilenameHtml)
    resultsStructured = {}
    # Algemeen
    criteria = 'HTML_Geldige HTML'
    output = {}
    output['Error'] = _getCheckTypeResult(results, HtmlChecks.Error)
    output['Invalide basis structuur'] = _getCheckTypeResult(results, HtmlChecks.BaseStructure)
    output['Code buiten body'] = _getCheckTypeResult(results, HtmlChecks.OutsideBody)
    resultsStructured[criteria] = output
    # Semantics
    criteria = 'HTML_Semantiek_tags'
    output = {}
    output['Ongeldige tags'] = _getCheckTypeResult(results, HtmlChecks.ForbiddenTags)
    output['Geneste \'article\''] = _getCheckTypeResult(results, HtmlChecks.NestedArticles)
    resultsStructured[criteria] = output
    # Afbeeldingen
    criteria = 'HTML_Afbeeldingen_afmeting'
    output = {}
    output['onjuist_herschalen'] = _getCheckTypeResult(results, HtmlChecks.ImageScaling)
    resultsStructured[criteria] = output
    _writeResultsToOutputFile(outputFile, _formatMultipleCriteriaResult(resultsStructured))

    # OUTPUTFILE: validatie-html-kdg-project.txt
    outputFile = os.path.join(outputDir, outputFilenameHtmlProject)
    resultsStructured = {}
    # Semantics
    criteria = 'HTML_Semantiek_inhoud'
    output = {}
    output['Main'] = _getCheckTypeResult(results, HtmlChecks.Main)
    resultsStructured[criteria] = output
    _writeResultsToOutputFile(outputFile, _formatMultipleCriteriaResult(resultsStructured))

    # OUTPUTFILE: validatie-html-kdg-info.txt
    outputFile = os.path.join(outputDir, outputFilenameHtmlInfo)
    resultsStructured = {}
    # Semantics
    criteria = 'HTML_Semantiek_inhoud'
    output = {}
    output['Semi-verboden_tags'] = _getCheckTypeResult(results, HtmlChecks.SemiForbiddenTags)
    if analyseLevel == AnalyseLevel.Full:
        output['page_title_and_h1'] = _getCheckTypeResult(results, HtmlChecks.PageTitleAndH1Info)
        output['img_alt'] = _getCheckTypeResult(results, HtmlChecks.ImageAltInfo)
        output['specific_semantic_tags'] = _getCheckTypeResult(results, HtmlChecks.SemanticTags, projectLevel=True)
    resultsStructured[criteria] = output
    # Formulieren
    criteria = 'HTML_Form_inhoud'
    output = {}
    if analyseLevel == AnalyseLevel.Full:
        output['input, select, textarea'] = _getCheckTypeResult(results, HtmlChecks.FormInputTypes)
        output['validatie attributen'] = _getCheckTypeResult(results, HtmlChecks.FormInputValidation)
    resultsStructured[criteria] = output
    criteria = 'HTML_Form_tags'
    output = {}
    if analyseLevel == AnalyseLevel.Full:
        output['Ontbrekend name-attribuut'] = _getCheckTypeResult(results, HtmlChecks.FormInputNameAttr)
    resultsStructured[criteria] = output
    # # Summary
    # criteria = 'HTML_Overzicht'
    # output = {}
    # if analyseLevel == AnalyseLevel.Full:
    #     outputResults = _getCheckTypeResult(results, HtmlChecks.FormInputNameAttr, projectLevel=True)
    #     output[None] = (outputResults, '')
    # resultsStructured[criteria] = output
    _writeResultsToOutputFile(outputFile, _formatMultipleCriteriaResult(resultsStructured))

def _writeCssResultsToOutputDir(outputDir, results):
    # OUTPUTFILE: validatie-css-kdg.txt
    outputFile = os.path.join(outputDir, outputFilenameCss)
    resultsStructured = {}
    # Algemeen
    criteria = 'CSS_Geldige CSS'
    output = {}
    output['Error'] = _getCheckTypeResult(results, CssChecks.Error)
    output['Verboden properties/eigenschappen'] = _getCheckTypeResult(results, CssChecks.ForbiddenProperties)
    resultsStructured[criteria] = output
    # Libraries
    criteria = 'CSS_Libraries CSS'
    output = {}
    output['CSS Links'] = _getCheckTypeResult(results, CssChecks.ExternStylesHttp)
    resultsStructured[criteria] = output
    # Files
    criteria = 'CSS_Bestanden CSS'
    output = {}
    output['Error HTML'] = _getCheckTypeResult(results, CssChecks.ErrorHtml)
    output['Intern styles: <style>...</style>'] = _getCheckTypeResult(results, CssChecks.InternStyles)
    output['Inline styles: style="..."'] = _getCheckTypeResult(results, CssChecks.InlineStyles)
    resultsStructured[criteria] = output
    _writeResultsToOutputFile(outputFile, _formatMultipleCriteriaResult(resultsStructured))

    # OUTPUTFILE: validatie-css-kdg-project.txt
    outputFile = os.path.join(outputDir, outputFilenameCssProject)
    resultsStructured = {}
    # Hidden titles
    criteria = 'CSS_Verborgen titels'
    output = {}
    if analyseLevel == AnalyseLevel.Full:
        output['Verborgen titels'] = _getCheckTypeResult(results, CssChecks.HiddenTitle)
    resultsStructured[criteria] = output
    _writeResultsToOutputFile(outputFile, _formatMultipleCriteriaResult(resultsStructured))

    # OUTPUTFILE: validatie-css-kdg-info.txt
    outputFile = os.path.join(outputDir, outputFilenameCssInfo)
    resultsStructured = {}
    # Algemeen
    criteria = 'CSS_Geldige CSS'
    output = {}
    if analyseLevel == AnalyseLevel.Full:
        output['Semi-verboden properties/eigenschappen'] = _getCheckTypeResult(results, CssChecks.SemiForbiddenProperties)
    resultsStructured[criteria] = output
    # Files
    criteria = 'CSS_Bestanden CSS'
    output = {}
    if analyseLevel == AnalyseLevel.Full:
        output['CSS Links'] = _getCheckTypeResult(results, CssChecks.ExternStylesLocal)
    resultsStructured[criteria] = output
    # Lay-out
    criteria = 'CSS_Lay-out'
    output = {}
    if analyseLevel == AnalyseLevel.Full:
        output['Flexbox'] = _getCheckTypeResult(results, CssChecks.Flexbox)
    resultsStructured[criteria] = output
    # Lay-out Grid
    criteria = 'CSS_Lay-out_Grid'
    output = {}
    if analyseLevel == AnalyseLevel.Full:
        output['Grid'] = _getCheckTypeResult(results, CssChecks.Grid)
    resultsStructured[criteria] = output
    # Duplicatie
    criteria = 'CSS_Duplicatie'
    output = {}
    outputResults = _getCheckTypeResult(results, CssChecks.DuplicatesOnSelectorLevel)
    output['selector/property/value combinatie'] = (outputResults, '')
    outputResults = _getCheckTypeResult(results, CssChecks.DuplicatesOnPropertyLevel)
    output['property/value combinatie'] = (outputResults, '')
    resultsStructured[criteria] = output
    # Comments
    # criteria = 'CSS_Commentaar'
    # output = {}
    # if AnalyseLevel.Full:
    #     output['Comments'] = _getCheckTypeResult(results, CssChecks.Comments)
    # resultsStructured[criteria] = output
    _writeResultsToOutputFile(outputFile, _formatMultipleCriteriaResult(resultsStructured))

def _writeJsResultsToOutputDir(outputDir, results):
    # OUTPUTFILE: validatie-js-kdg.txt
    outputFile = os.path.join(outputDir, outputFilenameJs)
    resultsStructured = {}
    # Algemeen
    criteria = 'JS_Geldige JS'
    output = {}
    output['Error'] = _getCheckTypeResult(results, JsChecks.Error)
    resultsStructured[criteria] = output
    # Files
    criteria = 'JS_Bestanden JS'
    output = {}
    output['Error HTML'] = _getCheckTypeResult(results, JsChecks.ErrorHtml)
    output['Intern: <script>...</script>'] = _getCheckTypeResult(results, JsChecks.InternScript)
    resultsStructured[criteria] = output
    # Variables
    criteria = 'JS_Variabelen'
    output = {}
    output['All "var" declared variables'] = _getCheckTypeResult(results, JsChecks.VarVariables)
    resultsStructured[criteria] = output
    # Events
    criteria = 'JS_Events'
    output = {}
    output['Html-attribute event-handling: on...="..."'] = _getCheckTypeResult(results, JsChecks.EventAttributeHandling)
    output['DOM Events Level 0: <element>.on... = ...'] = _getCheckTypeResult(results, JsChecks.EventLevelHandling)
    resultsStructured[criteria] = output
    _writeResultsToOutputFile(outputFile, _formatMultipleCriteriaResult(resultsStructured))

    # OUTPUTFILE: validatie-js-kdg-info.txt
    outputFile = os.path.join(outputDir, outputFilenameJsInfo)
    resultsStructured = {}
    # INFO
    criteria = 'JS_Algemeen'
    output = {}
    if analyseLevel == AnalyseLevel.Full:
        output['script type'] = _getCheckTypeResult(results, JsChecks.SourceType)
        output['strict-mode'] = _getCheckTypeResult(results, JsChecks.StrictMode)
    resultsStructured[criteria] = output
    criteria = 'JS_Variabelen'
    output = {}
    output['Global declared variables'] = _getCheckTypeResult(results, JsChecks.GlobalVariables)
    if analyseLevel == AnalyseLevel.Full:
        output['Undeclared/leaked variables'] = _getCheckTypeResult(results, JsChecks.UndeclaredVariables)
    resultsStructured[criteria] = output
    _writeResultsToOutputFile(outputFile, _formatMultipleCriteriaResult(resultsStructured))


def _writeResultsToOutputDir(outputDir, results):
    _writeHtmlResultsToOutputDir(outputDir, results["html"])
    _writeCssResultsToOutputDir(outputDir, results["css"])
    _writeJsResultsToOutputDir(outputDir, results["js"])


## MODULE (whem imported as module) ##
def analyse(projectDir, html=True, css=True, js=True, level = AnalyseLevel.Normal, outputToFile=True):
    global singleProjectDirName, doBulkProjectsCheck
    global checkHtml, checkCss, checkJavaScript
    global analyseLevel
    singleProjectDirName = None
    doBulkProjectsCheck = False
    checkHtml = html
    checkCss = css
    checkJavaScript = js
    analyseLevel = level

    if outputToFile: _clearOutputFiles(projectDir)
    results = _analyseProject(projectDir)
    if outputToFile: _writeResultsToOutputDir(projectDir, results)
    return results


## MAIN (executed as standalone script) ##
def main():
    # script execution arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('--project', help='Check single project', action='store')
    parser.add_argument('--bulk', help='Check subdirectories as seperate projects', action='store')
    parser.add_argument('--html', help='Do HTML-check', action='store_true')
    parser.add_argument('--css', help='Do CSS-check', action='store_true')
    parser.add_argument('--js', help='Do JS-check', action='store_true')
    parser.add_argument('--extended', help='Execute ALL checks, this includes informational checks!', action='store_true')
    args = parser.parse_args()
    
    global singleProjectDirName, doBulkProjectsCheck
    global checkHtml, checkCss, checkJavaScript
    global analyseLevel
    singleProjectDirName = args.project if args.project else None
    doBulkProjectsCheck = True if args.bulk else False
    checkHtml = True if args.html else False
    checkCss = True if args.css else False
    checkJavaScript = True if args.js else False
    doExtendedCheck = True if args.extended else False
    
    # run main
    scriptDir = os.getcwd() # os.path.realpath(os.path.dirname(__file__))
    projectsBaseDir = scriptDir
    analyseLevel = AnalyseLevel.Full if doExtendedCheck else AnalyseLevel.Normal
    if doBulkProjectsCheck:
        for entry in os.listdir(projectsBaseDir):
            fullPath = os.path.join(projectsBaseDir, entry)
            if os.path.isdir(fullPath):
                if entry.startswith('.'):
                    continue
                _clearOutputFiles(fullPath)
                results = _analyseProject(fullPath)
                _writeResultsToOutputDir(fullPath, results)
    else:
        fullPath = projectsBaseDir if not singleProjectDirName else os.path.join(projectsBaseDir, singleProjectDirName)
        if os.path.isdir(fullPath):
            _clearOutputFiles(fullPath)
            results = _analyseProject(fullPath)
            _writeResultsToOutputDir(fullPath, results)

if __name__ == "__main__":
    main()
