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
Extract sentences from OALE8. Result format: "word[TAB]defZh[TAB]en[TAB]zh"

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
               defZh: definition in Chinese. (Maybe None).
               sentenceEn: example sentence in english. (Must exist).
               sentenceZh: translation of above sentence. (Must exist).
    """
    global idxBuilder
    if w is None or len(w) == 0 or idxBuilder is None:
        return None

    lookupResult = idxBuilder.mdx_lookup(w)
    if len(lookupResult) == 0:
        return None

    soup = BeautifulSoup(lookupResult[0], 'html5lib')
    meaningGroups = soup.find_all('span', class_='n-g')
    for group in meaningGroups:
        # definition in Chinese:
        defZh = None
        defGroups = group.find_all('span', class_='def-g')
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
            return [defZh,
                    sentenceEn[0].get_text().replace('\t', ' ').strip(),
                    sentenceZh[0].get_text().replace('\t', ' ').strip()]
    return None


def formatContent(word, resultList):
    defZh = resultList[0]
    sentenceEn = resultList[1]
    sentenceZh = resultList[2]

    # plain text:
    wordEnZhLineTxt = None
    if defZh is None:
        wordEnZhLineTxt = word + '\t' + ' ' + '\t' + sentenceEn + '\t' + sentenceZh
    else:
        wordEnZhLineTxt = word + '\t' + defZh + '\t' + sentenceEn + '\t' + sentenceZh

    # html:
    wordEnZhLineHtml = None
    if defZh is None:
        wordEnZhLineHtml = '<table width="100%">\n' + \
                           ' <tr><td style="color:crimson; white-space: nowrap">' + word + '</td></tr>\n' + \
                           ' <tr><td>' + re.sub(word, '<strong>\g<0></strong>', sentenceEn,
                                                flags=re.IGNORECASE) + '</td></tr>\n' + \
                           ' <tr><td>' + sentenceZh + '</td></tr>\n' + \
                           '</table>' + '\n<hr style="border:none; height:1px; background-color:lightgray;" /><br />'
    else:
        wordEnZhLineHtml = '<table width="100%">\n' + \
                           ' <tr><td style="color:crimson; white-space: nowrap">' + word + '</td>\n' + \
                           '  <td style="text-align:center; font-size:70%; color:royalblue;">' + defZh + '</td></tr>\n' + \
                           ' <tr><td colspan="2">' + re.sub(word, '<strong>\g<0></strong>', sentenceEn,
                                                            flags=re.IGNORECASE) + '</td></tr>\n' + \
                           ' <tr><td colspan="2">' + sentenceZh + '</td></tr>\n' + \
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
        onceOpenedFlag = False

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
                    fdOutTxt = open(fileOutTxt, mode='w+', encoding='utf-8')
                    fdOutHtml = open(fileOutHtml, mode='w+', encoding='utf-8')
            elif not onceOpenedFlag:
                fileOutTxt = fileOut[0] + fileOut[1]
                fileOutHtml = fileOut[0] + '.html'
                fdOutTxt = open(fileOutTxt, mode='w+', encoding='utf-8')
                fdOutHtml = open(fileOutHtml, mode='w+', encoding='utf-8')
                onceOpenedFlag = True

            # lookup word
            result = extractSentence(word)
            if result is not None:
                markupResult = formatContent(word, result)
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
            with open(fileOut[0] + fileOut[1] + '.fail', 'w+', encoding='utf-8') as fdFailTxt:
                for word in failWords:
                    fdFailTxt.write(word + '\n')
    # done
    print("result: " + fileOut[0] + fileOut[1] + ' / ' + fileOut[0] + '.html')


if __name__ == '__main__':
    main()
