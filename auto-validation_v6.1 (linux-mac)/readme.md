# VERSION: v6.1

# Info
Dit tooltje doet een validatie van alle htm(l), css en js bestanden in de huidige directory en alle subdirectories.

# Validatie uitvoeren
Zorg dat je systeem voldoet aan de nodige vereisten, zie '**Prerequisites**'!

Voer de validatie uit door in de terminal, in de root van je project, volgend commando uit te voeren:
> sh auto-validation.sh

Het resultaat komt in bestanden met de naam 'validatie-*.txt'.

# Prerequisites
Deze tool is ontwikkeld gebruikmakend van Java en Python en dienen vooraf geïnstalleerd te zijn.

## 'Python 3'
Controle:
> python3 --version

Download: https://www.python.org/downloads/
Kies de juiste download voor jouw systeem en volg de installatie instructies.

### Vereiste module(s)
Volgende python modules zijn vereist (zie ook 'auto-validation/requirements.txt'):
* 'beautifulsoup4' (=bs4)
* 'cssutils'
* 'esprima'

De lijst van geïsntalleerde modules kan je raadplegen via:
> python3 -c 'help("modules")'

Module(s) kan je installeren via:
> sudo apt install python3-bs4 python3-cssutils python3-esprima

#### 'pip' package manager
Je kan ook gebruik maken van 'pip' als python package manager.
Indien nog niet geïnstalleerd, kan dit via:
> sudo apt install python3-pip

Module(s) kan je dan installeren via:
> pip3 install bs4 cssutils esprima

Of a.d.h.v. het bestand 'requirements.txt' via (relatief pad naar 'requirements.txt' bestand):
> pip3 install -r auto-validation/requirements.txt

## 'Java 8' (of hoger)
JRE (Java Runtime Environment) is voldoende, dus JDK (Java Development Kit) is niet noodzakelijk. 
Controle:
> java --version

Downloads: https://www.oracle.com/java/technologies/downloads/
Kies de juiste download voor jouw systeem en volg de isntallatie instructies.

Voor Ubuntu kan ook:
> sudo apt install default-jre
