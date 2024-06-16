#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""conventions-validator.py: Check conventions."""

__author__ = "Kenneth De Keulenaer, Jan Celis, Jeroen Reinenbergh"
__copyright__ = "Copyright 2023, The Autovalidation Project"
__credits__ = ["Kenneth De Keulenaer", "Jan Celis", "Jeroen Reinenbergh"]
__license__ = "GPL"
__version__ = "2.0.0"
__maintainer__ = "Kenneth De Keulenaer"
__email__ = "kenneth.dekeulenaer@kdg.be"
__status__ = "Production"


import os

# OUTLINE: do outline-check on project
from analyseHtmlOutline import checkProject as _checkProject

# ANALYSE: do analyse-check on project
from analyse import analyse as _analyseProject
from analyse import AnalyseLevel


## MAIN (executed as standalone script) ##
def main():
    #scriptDir = path.realpath(os.path.dirname(__file__))
    #projectDir = scriptDir
    projectDir = os.getcwd()

    print('== Conventions check ==')
    # OUTLINE: do outline-check on project
    _checkProject(projectDir)
    # ANALYSE: do analyse-check on project
    _analyseProject(projectDir, level = AnalyseLevel.Normal)


if __name__ == "__main__":
    main()