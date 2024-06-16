import subprocess
import os

vnuHtmlOutputFilename = 'validatie-01_html-00_w3c.txt'
vnuCssOutputFilename = 'validatie-02_css-00_w3c.txt'
okSuffix = '_OK'

scriptDir = os.path.realpath(os.path.dirname(__file__))
relPath = os.path.relpath(scriptDir, os.getcwd())


def _checkVnuHtml(projectDir):
    vnuHtmlCmdFile = os.path.join(relPath, 'vnu.jar')
    vnuHtml = subprocess.run(['java', '-jar', vnuHtmlCmdFile, '--skip-non-html', '--errors-only', '--stdout', projectDir], capture_output=True)
    result = vnuHtml.stdout.decode()
    return result
    
def _checkVnuCss(projectDir):
    vnuCssCmdFile = os.path.join(relPath, 'vnu.jar')
    vnuHtml = subprocess.run(['java', '-jar', vnuCssCmdFile, '--skip-non-css', '--errors-only', '--stdout', projectDir], capture_output=True)
    result = vnuHtml.stdout.decode()
    return result


def _clearOutputFile(outputFile):
    if os.path.exists(outputFile):
        os.remove(outputFile)
    # OK-variant
    outputPathInfo = os.path.split(outputFile)
    outputFilenameInfo = os.path.splitext(outputPathInfo[1])
    okOutputFile = os.path.join(outputPathInfo[0], outputFilenameInfo[0]+okSuffix+outputFilenameInfo[1])
    if os.path.exists(okOutputFile):
        os.remove(okOutputFile)

def _writeToOutputFile(outputFile, content):
    # write outputtext
    if not content:
        outputPathInfo = os.path.split(outputFile)
        outputFilenameInfo = os.path.splitext(outputPathInfo[1])
        outputFile = os.path.join(outputPathInfo[0], outputFilenameInfo[0]+okSuffix+outputFilenameInfo[1])
    with open(outputFile, 'a', encoding='utf-8') as output:
        output.write(content)


## MODULE (when imported as module) ##
def checkProject(projectDir, outputToFile=True):
    if outputToFile:
        htmlOutputFile = os.path.join(projectDir, vnuHtmlOutputFilename)
        _clearOutputFile(htmlOutputFile)
    htmlResult = _checkVnuHtml(projectDir)
    if outputToFile:
        _writeToOutputFile(htmlOutputFile, htmlResult)

    if outputToFile:
        cssOutputFile = os.path.join(projectDir, vnuCssOutputFilename)
        _clearOutputFile(cssOutputFile)
    cssResult = _checkVnuCss(projectDir)
    if outputToFile:
        _writeToOutputFile(cssOutputFile, cssResult)
    
    return {'html':htmlResult, 'css':cssResult}


## MAIN (executed as standalone script) ##
def main():
    outputDir = os.getcwd()

    projectDir = '.'

    print('== HTML check ==')
    htmlOutputFile = os.path.join(outputDir, vnuHtmlOutputFilename)
    _clearOutputFile(htmlOutputFile)
    htmlResult = _checkVnuHtml(projectDir)
    _writeToOutputFile(htmlOutputFile, htmlResult)

    print('== CSS check ==')
    cssOutputFile = os.path.join(outputDir, vnuCssOutputFilename)
    _clearOutputFile(cssOutputFile)
    cssResult = _checkVnuCss(projectDir)
    _writeToOutputFile(cssOutputFile, cssResult)


if __name__ == "__main__":
    main()
