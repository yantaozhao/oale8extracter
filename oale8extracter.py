#! /usr/bin/env python3
# -*- coding: UTF-8 -*-

import getopt
import os.path
import re
from bs4 import BeautifulSoup

# https://github.com/mmjang/mdict-query
import sys
sys.path.append('C:/Users/DELL/Desktop/hello/mdict-query/')
from mdict_query import IndexBuilder


def usage():
    scriptname = os.path.basename(__file__)
    hlp = f"""
Extract sentences from OALE8. Text result format: "word[TAB]phonic[TAB]defZh[TAB]en[TAB]zh"

SYNOPSIS:
{scriptname} [-i input.txt] [-o output.txt]

OPTIONS:
-i [input.txt]   : file of word list
-o [output.txt]  : result file. Default in one file, unless `-b` used
-k               : keep the original order in the input file
-b  --break-file : break into files by leading letter
-h  --help       : print this help and exit


SEE ALSO:
- Sigil:
https://sigil-ebook.com/

- Use calibre to build e-book:
https://manual.calibre-ebook.com/faq.html#how-do-i-convert-a-collection-of-html-files-in-a-specific-order
```html
<html>
<head> <title>The title</title> </head>
<body>
    <h1>Table of Contents</h1>
    <p style="text-indent:0pt">
        <a href="file1.html">1st File</a> <br/>
        <a href="file2.html">2nd File</a> <br/> 
        ...
    </p>
</body>
</html>
```
Then, just add this HTML file to the GUI and use the Convert button to create your e-book.
"""
    print(hlp)


idxBuilder = None  # global variable


def extractSentence(w):
    """
    extract content from dictionary file.
    :param w: word
    :return: list of specified contents, or `None` if example sentences not exist.
             If the result is not None, its format is:
               w: word. (MUST exist)
               phon: phonic. (Maybe None)
               defZh: definition in Chinese. (Maybe None).
               sentenceEn: example sentence in english. (MUST exist).
               sentenceZh: translation of above sentence. (MUST exist).
    """
    global idxBuilder
    if w is None or len(w) == 0 or idxBuilder is None:
        return None

    soup = None
    while True:
        w_bak = w
        lookupResult = idxBuilder.mdx_lookup(w)
        if len(lookupResult) == 0:
            return None
        soup = BeautifulSoup(lookupResult[0], 'html5lib')
        # check if this word is derived. if yes, find the original word:
        derivedBlock = soup.find_all('span', class_='derived')
        if (len(derivedBlock) == 1):
            orig = derivedBlock[0].find_all('a', id='drv')
            if (len(orig) > 0):
                # w = orig[0].get_text().replace('\t', ' ').strip()  # found
                pass
        elif (len(derivedBlock) > 1):
            raise RuntimeError("I am dizzy: more than one word found")  # exception
        if (w_bak == w):
            break  # good

    # phonic
    phon = None
    for clasTxt in ('phon-gb', 'phon-usgb'):
        phonLi = soup.find_all('span', class_=clasTxt)
        if len(phonLi) > 0:
            phon = phonLi[0].get_text().strip()
            break
        else:
            phon = None

    # meaning
    meaningGroups = soup.find_all('span', class_='n-g')
    for group in meaningGroups:
        # definition in Chinese:
        defZh = None
        defGroups = []
        defBlocks = group.find_all('span', class_='def-g')
        # find the definitions
        for blk in defBlocks:
            defGroups = blk.find_all('span', class_='d')
            if (len(defGroups)) > 0:
                break
            else:
                defGroups = []
        # get the first definition in Chinese
        if len(defGroups) > 0:
            defZhGroups = defGroups[0].find_all('span', class_='oalecd8e_chn')
            if len(defZhGroups) > 0:
                defZh = defZhGroups[0].get_text().replace('\t', ' ').strip()
        # example sentences:
        sentenceGroups = group.find_all('span', 'x-g')
        for sGroup in sentenceGroups:
            sentenceEn = sGroup.find_all('span', 'x')
            sentenceZh = sGroup.find_all('span', 'oalecd8e_chn')
            if len(sentenceEn) == 0 or len(sentenceZh) == 0:
                continue  # ensure the two sentences exist
            return [w, phon, defZh,
                    sentenceEn[0].get_text().replace('\t', ' ').strip(),
                    sentenceZh[0].get_text().replace('\t', ' ').strip()]
    return None


def formatContent(resultList):
    """
    format content, and return as list
    :param resultList:
    :return:
    """
    word = resultList[0]
    phon = resultList[1]
    defZh = resultList[2]
    sentenceEn = resultList[3]
    sentenceZh = resultList[4]

    # plain text:
    wordEnZhLineTxt = word + '\t' + (('[' + phon + ']') if phon is not None else ' ') + '\t' + (defZh if defZh is not None else ' ') + '\t' + sentenceEn + '\t' + sentenceZh

    # html:
    wordEnZhLineHtml = None
    if phon is None and defZh is None:
        wordEnZhLineHtml = '<table width="100%">\n' + \
                           ' <tr><td>' + re.sub(word, '<i><strong>\g<0></strong></i>', sentenceEn,
                                                flags=re.IGNORECASE) + '</td></tr>\n' + \
                           ' <tr><td>' + sentenceZh + '</td></tr>\n' + \
                           ' <tr><td style="color:darkred; white-space: nowrap">' + word + '</td></tr>\n' + \
                           '</table>' + '\n<hr style="border:none; height:1px; background-color:lightgray;" /><br />'
    else:
        wordEnZhLineHtml = '<table width="100%">\n' + \
                           ' <tr><td colspan="2">' + re.sub(word, '<i><strong>\g<0></strong></i>', sentenceEn,
                                                            flags=re.IGNORECASE) + '</td></tr>\n' + \
                           ' <tr><td colspan="2">' + sentenceZh + '</td></tr>\n' + \
                           ' <tr><td style="color:darkred; white-space: nowrap">' + word + '</td>\n' + \
                           '  <td style="text-align:center; font-size:80%; color:royalblue;"><pre>' + \
                              (('[' + phon + ']') if phon is not None else '') + \
                              ('  ' if (phon is not None and defZh is not None) else '') + \
                              (defZh if defZh is not None else '') + '</pre></td></tr>\n' + \
                           '</table>' + '\n<hr style="border:none; height:1px; background-color:lightgray;" /><br />'

    return [wordEnZhLineTxt,
            wordEnZhLineHtml]


def main():
    fileIn = 'input.txt'
    fileOut = ('output', '.txt')
    keepOriginal = False
    breakFileFlag = False
    # parse command line args
    try:
        opts, args = getopt.getopt(sys.argv[1:], 'hkbi:o:', ['help', 'break-file'])
    except getopt.GetoptError as err:
        print('Error: %s!' % err)
        sys.exit(2)
    for o, a in opts:
        if o == '-i':
            fileIn = a
        elif o == '-o':
            fileOut = os.path.splitext(a)
            if len(fileOut[1]) == 0:
                print('Error: Regular name of output file required! For example: output.txt')
                sys.exit()
        elif o == '-k':
            keepOriginal = True
        elif o in ('-b', '--break-file'):
            breakFileFlag = True
        elif o in ('-h', '--help'):
            usage()
            sys.exit()

    global idxBuilder
    idxBuilder = IndexBuilder('C:/Users/DELL/Desktop/hello/Oxford+Advanced+Learner+English-Chinese+Dictionary+8th+Edition.mdx')

    # read/write files
    with open(fileIn, 'r') as fdIn:
        # words = fdIn.readlines()
        words = [w for w in [line.replace('\t', ' ').strip() for line in fdIn] if len(w) > 0]
        if not keepOriginal:
            words = list(set(words))
            words.sort(key=str.lower)
        failWords = []
        print("Total words: %d." % len(words))

        # output:
        fdOutTxt = None
        fdOutHtml = None
        rememberedLeadingLetter = None
        fileOpenedFlag = False

        for word in words:
            # open right file
            if breakFileFlag:
                if rememberedLeadingLetter != word[0].lower():
                    if fdOutTxt is not None:
                        if not fdOutTxt.closed:
                            fdOutTxt.close()
                    if fdOutHtml is not None:
                        if not fdOutHtml.closed:
                            fdOutHtml.close()
                    rememberedLeadingLetter = word[0].lower()
                    fileOutTxt = fileOut[0] + '_' + rememberedLeadingLetter + fileOut[1]
                    fileOutHtml = fileOut[0] + '_' + rememberedLeadingLetter + '.html'
                    fdOutTxt = open(fileOutTxt, mode='a+', encoding='utf-8')
                    fdOutHtml = open(fileOutHtml, mode='a+', encoding='utf-8')
            elif not fileOpenedFlag:
                fileOutTxt = fileOut[0] + fileOut[1]
                fileOutHtml = fileOut[0] + '.html'
                fdOutTxt = open(fileOutTxt, mode='a+', encoding='utf-8')
                fdOutHtml = open(fileOutHtml, mode='a+', encoding='utf-8')
                fileOpenedFlag = True

            # lookup word
            result = extractSentence(word)
            if result is not None:
                markupResult = formatContent(result)
                if markupResult[0] is not None:
                    fdOutTxt.write(markupResult[0] + '\n')
                if markupResult[1] is not None:
                    fdOutHtml.write(markupResult[1] + '\n')
            else:
                failWords.append(word)
                print('[FAIL] ' + word)

        else:
            if fdOutTxt is not None:
                if not fdOutTxt.closed:
                    fdOutTxt.close()
            if fdOutHtml is not None:
                if not fdOutHtml.closed:
                    fdOutHtml.close()

        if len(failWords) > 0:
            with open(fileOut[0] + fileOut[1] + '.fail', 'a+', encoding='utf-8') as fdFailTxt:
                for word in failWords:
                    fdFailTxt.write(word + '\n')
    # done
    print("result: " + fileOut[0] + fileOut[1] + ' / ' + fileOut[0] + '.html')


if __name__ == '__main__':
    main()
