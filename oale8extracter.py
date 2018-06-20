#! /usr/bin/env python3
# -*- coding: UTF-8 -*-

import getopt
import os.path
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
-i        : file of word list
-o        : result file
-h  --help: print this help and exit
"""
    print(hlp)


idxBuilder = None

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
        return [sentenceEn[0].get_text().replace('\t', ' ').strip(), sentenceZh[0].get_text().replace('\t', ' ').strip()]
    return None


def main():
    fileIn = 'input.txt'
    fileOut = 'output.txt'
    # parse command line args
    try:
        opts, args = getopt.getopt(sys.argv[1:], 'hi:o:', ['help'])
    except getopt.GetoptError as err:
        print('Error: %s!' % err)
        sys.exit(2)
    for o, a in opts:
        if o == '-i':
            fileIn = a
        elif o == '-o':
            fileOut = a
        elif o in ('-h', '--help'):
            usage()
            sys.exit()

    global idxBuilder
    idxBuilder = IndexBuilder('C:/Users/DELL/Desktop/hello/Oxford+Advanced+Learner+English-Chinese+Dictionary+8th+Edition.mdx')
    # r/w files
    with open(fileIn, 'r') as fdIn, open(fileOut, 'w+', encoding='utf-8') as fdOut:
        # words = fdIn.readlines()
        words = [w for w in [line.replace('\t', ' ').strip() for line in fdIn] if len(w) > 0]
        failWords = []

        for word in words:
            result = extractSentence(word)
            if result is not None:
                wordEnZhLine = word
                for res in result:
                    wordEnZhLine += '\t' + res
                wordEnZhLine += '\n'
                fdOut.write(wordEnZhLine)
            else:
                failWords.append(word)
                print('[FAIL] ' + word)

        if len(failWords) > 0:
            with open(fileOut + '.fail', 'w+', encoding='utf-8') as fdFail:
                for word in failWords:
                    fdFail.write(word + '\n')
    print("result: " + fileOut)


if __name__ == '__main__':
    main()
