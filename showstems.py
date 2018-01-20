#/usr/bin/python3
# stemit_01.py
# 
# Get all the (reasonable) stem words from the HILR 'Short bio' fields
#  of the member pages.
# These will be used to select stems to indicate taxonomic category guesses
#  based on what a member wrote in his/her bio. 
# For finding word stems, use the PorterStemmer algorithm from
#  the nltk package.  Seems to be derived from the Tukey/Dolby 
#  algorithm from 66-67.  
#  

'''
theory:

fn stemmer:
given a string
sanitize
tokenize
stem words
add word to dict list for that stem

'''

from nltk.stem import PorterStemmer
from collections import defaultdict
import sys
import csv
import re
# Sorry, NewTrace is not python3 yet.  This is experimental.
from NewTracep3 import NTRC, ntrace, ntracef


class CStemWords():
    ''' Class that computes and maintains the dictionary of stemmed words. '''


    @ntrace
    def __init__(self, mysStopwordFilename):
        ''' CStemWords init: Initialize the empty stemword dict.  
             Get the stopword list from user-specified file.  

            Store stopwords as a dict because it's faster to lookup.
            Ignore blank lines and comment lines in stopword file.
        '''
        self.dWords = defaultdict(list)
        self.dWordsNocc = defaultdict(int)
        self.dWordStemCrop = {}
        self.dStoplist = dict()
        with open(mysStopwordFilename, "r") as fhIn:
            for sLine in fhIn:
                sWord = sLine.strip()
                if sWord and not sWord.startswith("#"):
                    self.dStoplist[sWord] = len(sWord)
            # Yes, this could be done as a one-liner, but uuuuugly.
            #dStoplist = {w.strip():len(w.strip()) for w in fhIn
            #               if w.strip() and not w.strip().startswith("#")}
            # And slower, too, going thru .strip() four times.
        self.ps = PorterStemmer()
        NTRC.ntrace(3, "proc CStemWords.init dStop|%s|" % (self.dStoplist))


# m s C l e a n S t r i n g 
    @ntrace
    def msCleanString(self, mysInput):
        ''' Remove stoplist words from the input string.  Return string.
            
            Tokenize away most common punctuation, remove stoplist words,
             and turn it back into a string.  Ignore blanks.
        '''
        lTokens0 = re.split(r'( +|,|\.|-|\/)', mysInput)
        lTokens1 = [w.strip(',.!?()(:;\"\'-') for w in lTokens0]
        lTokens2 = [word for word in lTokens1 
                    if word and word[0] not in ',.' ]
        lTokens3 = [word for word in lTokens2 if word not in self.dStoplist]
        sResult = ' '.join(lTokens3)
        return sResult


# m l P r o c e s s S t r i n g 
    @ntrace
    def mlProcessString(self, mysInput):
        ''' Find the stem of each word.  For each stem, keep a list of
             the unique words that translate to that stem.  
        '''
        lStemPairs = [(self.ps.stem(word), word) for word in mysInput.split()]
        for sStem, sWord in lStemPairs:
            if sWord not in self.dWords[sStem]:
                self.dWords[sStem].append(sWord)
            self.dWordsNocc[sWord] += 1
            self.dWordStemCrop[sWord] = (self.dWordsNocc[sWord]
                                    , sWord[:len(sStem)]
                                    , sStem
                                    , sWord[len(sStem):])
        return lStemPairs


# m d G e t W o r d D i c t 
    @ntrace
    def mdGetWordStemCropDict(self):
        ''' Return the dictionary of words with their stems and 
            cropped suffixes. '''
        return self.dWordStemCrop


# f n v P r o c e s s F i l e 
@ntrace
def fnvProcessFile(mysFilename, cStemmer):
    ''' For a file, get all the lines, render them into ASCII-7 for 
         easier handling, extract the member bio from each line, 
         then clean it up a little and add its words to the stem dict.
    '''
    # NB: File must be opened in read-binary mode.  This avoids UTF-8 decoding
    #  problems and makes it easier to sanitize to pure ASCII-7.
    with open(mysFilename, 'rb') as fhIn:
        lLinesRaw = [sLine for sLine in fhIn]
        lLines = [fnsSanitize(sLine) for sLine in lLinesRaw if sLine.strip()]
        ldMembers = csv.DictReader(lLines)
        for dMember in ldMembers:
            NTRC.ntrace(3, "proc member|%s|" % (dMember))
            if debug: print(".", end="")
            sBioRaw = dMember["Short bio"].lower()
            if sBioRaw:
                sBio = cStemmer.msCleanString(sBioRaw)
                lStem = cStemmer.mlProcessString(sBio)


# f n s S a n i t i z e 
@ntrace
def fnsSanitize(mysInput):
    ''' Ensure that the input string becomes pure ASCII-7 for easy handling.  
    
        Map any higher characters into underscores.  This is necessary to
         avoid problems with ISO Latin-1 and Unicode typographic characters
         that are put into the text by word processors, especially on Macs.
    '''
    lString = [chr(cint) if (cint>=32 and cint<=126) else "_"
                for cint in mysInput]
    sResult = "".join(lString)
    return sResult


# f n v D u m p W o r d s 
@ntrace
def fnvDumpWords(mydWords):
    ''' Dump resulting stem-to-word-list dictionary in readable form. '''
    print("\n\n====== FINAL DICT ======")
    for sWord, (nOcc, sRoot, sStem, sCrop) in sorted(mydWords.items()):
        sFlag = "" if sRoot == sStem else "*"
        print("%4d %-25s%-20s%-10s%s" % (nOcc, sWord, sStem, sCrop, sFlag))


# M A I N 
@ntrace
def main(cStemmer):
    ''' MAIN: Process any files on the command line.  Dump results. '''
    for sFile in sys.argv[1:]:
        fnvProcessFile(sFile, cStemmer)
    dFinal = cStemmer.mdGetWordStemCropDict()
    fnvDumpWords(dFinal)


# E N T R Y   P O I N T 
if __name__ == "__main__":
    debug = 0
    cStem = CStemWords("StopWordList.txt")
    sys.exit(main(cStem))


# Edit history:
# 20180113  RBL Original version.
# 20180114  RBL Remove ugly debug printing, add comments.
# 20180116  RBL Put ntracing back in; see if it's safe for p3.
# 20180118  RBL Reformulate for printing all the words and their stems 
#                and suffixes.
#               Change tokenizer to strip punctuation after splitting.  
# 
# 

#END
       