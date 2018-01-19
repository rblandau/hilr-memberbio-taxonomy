# hilr-memberbio-taxonomy

Contents: HILR programs to add taxonomy categories to member bio pages for OpenScholar.

## Abstract

The HILR member pages are being migrated from the old iSites "About Faces" app to a new format in OpenScholar.  The search function for the new site will have keyword search, so we wish to add keywords to the member records.  These programs will salt the member records being placed into the new format with keywords (categories from some user taxonomy) derived from the "Short bio" fields of the existing member records.  This is just a starting point, and we recognize that there will be both false positives and false negatives, since the assignment is being done on single words in the bios.

There are two major programs.  They are both Python3 and use the nltk package PorterStemmer function.  This function is a good first step.  (It does not appear to be quite so complex or flexible as the stemming program that I did for Tukey and Dolby at Bell Labs in 1967, but that code is not available anymore. :-)

1.  Read all the bios, remove stop-words, stem all the words in the bios, and report all the words that map to each stem.  

2.  Read all the bios, remove stop-words, collect the list of categories associated with the remaining words, and add those category names to the "Taxonomy names" field of the member records.  

The stop-word list was assembled and enhanced from ones found on the web.  The taxonomy classification list was written by Dick Rubinstein of HILR.  

