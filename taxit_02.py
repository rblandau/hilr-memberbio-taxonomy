#/usr/bin/python3
# taxit_02.py
# 
#                               RBLandau 20180114
#                               revised 20180118
#
# Add taxonomic categories to HILR member records, based on bio words.
# 
# For finding word stems, use the PorterStemmer algorithm from
#  the nltk package.  Seems to be derived from the Tukey/Dolby 
#  algorithm from 66-67.  
#  

'''
theory:

foreach member:
given a bio string
sanitize, tokenize
stem words
if word is in mapping dict, add categories for that word to member list

'''

from nltk.stem import PorterStemmer
from collections import defaultdict
import sys
import csv
import re
import copy
# Sorry, NewTrace is not python3 yet.
from NewTracep3 import NTRC, ntrace, ntracef


# c l a s s   C T a x i f y 
class CTaxify():
    ''' Class that makes list of taxonomic categories to add to member bio. '''


    @ntrace
    def __init__(self, mysStopwordFilename="StopWordList.txt", 
                        mysTaxonomyFilename="TaxonomyList.txt"):
        ''' CTaxify init: Get the stopword list from user-specified file.  
             Get the taxonomy list from user-specified file.

            Store stopwords as a dict because it's faster to lookup.
            Store taxonomies in dict.
            Ignore blank lines and comment lines in both files.
            Taxonomy list file format is now
            <taxonomyname> \s <listofwords>
        '''
        self.ps = PorterStemmer()

        # Get stop-word list.  
        self.dStoplist = dict()
        with open(mysStopwordFilename, "r") as fhIn:
            for sLine in fhIn:
                sWord = sLine.strip()
                if sWord and not sWord.startswith("#"):
                    self.dStoplist[sWord] = len(sWord)
            # Yes, this could be done as a one-liner, but uuuuugly.
            #self.dStoplist = {w.strip():len(w.strip()) for w in fhIn
            #               if w.strip() and not w.strip().startswith("#")}
            # And slower, too, going thru .strip() four times.
        NTRC.ntrace(3, "proc stopword list|%s|" % (list(self.dStoplist.keys())))

        # Get taxonomy category list.
        #  A word stem can map to one or more categories.
        self.dStem2Tax = defaultdict(list)
        with open(mysTaxonomyFilename, "r") as fhIn:
            for sLineRaw in fhIn:
                sLine = sLineRaw.strip()
                if sLine and not sLine.startswith("#"):
                    lWordsAll = re.split(r'\s+', sLine)
                    NTRC.ntrace(5, "proc lWords|{}|".format(lWordsAll))
                    (sTaxName, lWords) = (lWordsAll[0].replace("%20"," ")
                                        , lWordsAll[1:]
                                        )
                    lStems = [self.ps.stem(sWord.lower()) for sWord in lWords]
                    for sStem in lStems:
                        self.dStem2Tax[sStem].append(sTaxName)
                        self.dStem2Tax[sStem] = list(set(self.dStem2Tax[sStem]))
        NTRC.ntrace(3, "proc stem2tax dict|%s|" % (self.dStem2Tax))


# m s C l e a n S t r i n g 
    @ntrace
    def msCleanString(self, mysInput):
        ''' Remove stoplist words from the input string.  Return string.
            
            Tokenize away most common punctuation, remove stoplist words,
             and turn it back into a string.  Ignore blanks.
        '''
        lTokens1 = re.split(r' *[,.();:/\"]*[ .,]+[(\"\']*', mysInput)
        lTokens2 = [word for word in lTokens1 
                    if word and word[0] not in ',.' ]
        NTRC.ntrace(4, "proc lTokens2|{}|".format(lTokens2))
        lTokens3 = [word for word in lTokens2 if word not in self.dStoplist]
        sResult = ' '.join(lTokens3)
        return sResult


# m l S t r i n g 2 T a x o n s 
    @ntrace
    def mlString2Taxons(self, mysInput):
        ''' Find the categories for this bio.  Return a list of unique names.
        
            Just for cleanliness, sort the list of taxonomy category names.
        '''
        lStems = [self.ps.stem(word) for word in mysInput.split()]
        NTRC.ntrace(4, "proc lStems|{}|".format(lStems))
        lTaxons = []
        for sStem in lStems:
            if sStem in self.dStem2Tax:
                lTaxons.extend(self.dStem2Tax[sStem])
                NTRC.ntrace(5, "proc taxonmatch from|{}| to|{}|"
                    .format(sStem, self.dStem2Tax[sStem]))
        return sorted([item for item in set(lTaxons) if item])


# f n v P r o c e s s F i l e 
#@ntrace
def fnvProcessFile(mysFilename, cTaxer):
    ''' For a file, get all the lines, render them into ASCII-7 for 
         easier handling, get the member dict for each member. 
         Process each member to get taxonomy categories, then output
         the enhanced member list.
    '''
    # NB: File must be opened in read-binary mode.  This avoids UTF-8 decoding
    #  problems and makes it easier to sanitize to pure ASCII-7.
    with open(mysFilename, 'rb') as fhIn:
        lLinesRaw = [sLine.strip() for sLine in fhIn]
    # Save the order of columns for output.
    lColumns = lLinesRaw[0].decode('utf-8').strip().split(",")
    lLines = [fnsSanitize(sLine) for sLine in lLinesRaw if sLine.strip()]
    ldMembers = csv.DictReader(lLines)
    ldMembersPlusTax = []
    # Get new info for all members.
    for dMember in ldMembers:
#        NTRC.ntrace(3, "proc member|%s|" % (dMember))
        if debug: print(".", end="")
        dMemberPlusTax = fndProcessMember(dMember, cTaxer)
        ldMembersPlusTax.append(dMemberPlusTax)
    nResult = fnnWriteMembers(ldMembersPlusTax, lColumns)
    return nResult


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


# f n d P r o c e s s M e m b e r 
@ntrace
def fndProcessMember(mydMember, cTaxer):
    ''' Try to add taxonomic categories to member dict.
        Return the member dict with enhancement, if any were generated.  
        
        Taxonomic categories will be added to the "Taxonomy terms" field of
         the member record, as a string with multiple entries separated by 
         vertical bar.
    '''
    sBioRaw = mydMember["Short bio"].lower()
    lTaxons = []
    if sBioRaw:
        sBio = cTaxer.msCleanString(sBioRaw)
        lTaxons = cTaxer.mlString2Taxons(sBio)
    sTaxons = "|".join(lTaxons)
    NTRC.ntrace(4, "proc sTaxons|{}|".format(sTaxons))
    dMemberPlusTax = copy.deepcopy(mydMember)
    dMemberPlusTax["Taxonomy terms"] = sTaxons
    return dMemberPlusTax


# f n n W r i t e M e m b e r s 
@ntrace
def fnnWriteMembers(myldMembers, mylColumns):
    ''' Write CSV output of all members to stdout.
        Return count of member records written.
        
        Manually write header line first, then write members thru CSV pkg.
    '''
    sColumnList = ",".join(mylColumns)
    nOut = 0
    fhWriter = csv.DictWriter(sys.stdout, mylColumns)
    fhWriter.writeheader()
    for dMember in myldMembers:
        fhWriter.writerow(dMember)
        nOut += 1
    return nOut


# M A I N 
@ntrace
def main(cTaxer):
    ''' MAIN: Process any files on the command line.  Dump results. '''
    for sFile in sys.argv[1:]:
        fnvProcessFile(sFile, cTaxer)
    return


# E N T R Y   P O I N T 
if __name__ == "__main__":
    debug = 0
    cTax = CTaxify("StopWordList.txt", "TaxonomyList.txt")
    sys.exit(main(cTax))


# Edit history:
# 20180114  RBL Original version.
# 20180115  RBL Remove ugly debug printing, add comments.
# 20180118  RBL Invert the structure of the TaxonomyList file to 
#                match the spreadsheet received.  The best I could 
#                do extracting it from the spreadsheet is
#                <categoryname> <tab> <blankseparatedlistofwords>
# 

#END
       