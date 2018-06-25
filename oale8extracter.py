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
Extract sentences from OALE8. Result format: "word[TAB]en[TAB]zh"

SYNOPSIS:
{scriptname} [-i input.txt] [-o output.txt]

OPTIONS:
-i [input.txt]   : file of word list
-o [output.txt]  : result file. Default in one file, except `-b` used.
-b  --break-file : break into files by leading letter
-h  --help       : print this help and exit
"""
    print(hlp)


idxBuilder = None  # global variable


def extractSentence(w):
    global idxBuilder
    if w is None or len(w) == 0 or idxBuilder is None:
        return None

    lookupResult = idxBuilder.mdx_lookup(w)
    if len(lookupResult) == 0:
        return None

    soup = BeautifulSoup(lookupResult[0], 'html5lib')
    sentenceGroups = soup.find_all('span', 'x-g')  # group of example sentences
    for group in sentenceGroups:
        sentenceEn = group.find_all('span', 'x')
        sentenceZh = group.find_all('span', 'oalecd8e_chn')
        if len(sentenceEn) == 0 or len(sentenceZh) == 0:
            continue
        return [sentenceEn[0].get_text().replace('\t', ' ').strip(),
                sentenceZh[0].get_text().replace('\t', ' ').strip()]
    return None


def main():
    fileIn = 'input.txt'
    fileOut = ('output', '.txt')
    breakFileFlag = False
    # parse command line args
    try:
        opts, args = getopt.getopt(sys.argv[1:], 'hbi:o:', ['help', 'break-file'])
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
        words = list(set(words))
        words.sort(key=str.lower)
        failWords = []
        print("Total words: %d." % len(words))

        # output:
        fileOutTxt = None
        fdOutTxt = None
        fileOutHtml = None
        fdOutHtml = None
        rememberedLeadingLetter = None
        alreadyOpenedFlag = False

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
            elif not alreadyOpenedFlag:
                fileOutTxt = fileOut[0] + fileOut[1]
                fileOutHtml = fileOut[0] + '.html'
                fdOutTxt = open(fileOutTxt, mode='w+', encoding='utf-8')
                fdOutHtml = open(fileOutHtml, mode='w+', encoding='utf-8')
                alreadyOpenedFlag = True

            # lookup word
            result = extractSentence(word)
            if result is not None:
                wordEnZhLineTxt = word
                wordEnZhLineHtml = '<p> ' + '<span style="color:#c00000"><strong>' + word + '</strong></span>'
                for res in result:
                    wordEnZhLineTxt += '\t' + res
                    wordEnZhLineHtml += '<br/>' + re.sub(word, '<strong>\g<0></strong>', res, flags=re.IGNORECASE)
                wordEnZhLineTxt += '\n'
                wordEnZhLineHtml += '<br/> </p>\n'
                fdOutTxt.write(wordEnZhLineTxt)
                fdOutHtml.write(wordEnZhLineHtml)
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
