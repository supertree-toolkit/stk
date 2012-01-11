import string
import sys


class GeneticCode:
    """A container for NCBI translation tables.

    See the ncbi translation tables, which this week are at
    http://www.ncbi.nlm.nih.gov/Taxonomy/Utils/wprintgc.cgi?mode=c

    (If they move, poke around the 'taxonomy browser' area.)

    This week we have

    - **1** standard
    - **2** vertebrate mito
    - **4** Mold, Protozoan
    - **5** invertbrate mito
    - **6** The Ciliate, Dasycladacean and Hexamita Nuclear Code
    - **9** echinoderm and flatworm mito
    - **10**  Euplotid Nuclear Code
    - **11**  Bacterial and Plant Plastid Code
    -  **12** Alternative Yeast Nuclear Code
    -  **13** Ascidian Mitochondrial Code
    -  **14** Alternative Flatworm Mitochondrial Code
    -  **21** Trematode Mitochondrial Code

    If more transl_tables are needed, you should be able to just drop
    them in, with a little tweaking.

    This provides
    
    - **code**  A dictionary.  So you can ask for eg myGC.code['ggg']
    - **codonsForAA**  Another dictionary, where you can ask for eg myGC.codonsForAA['v']
    - **startList**  A list of start codons

    Wikipedia says: The joint nomenclature committee of the
    IUPAC/IUBMB has officially recommended the three-letter symbol Sec
    and the one-letter symbol U for selenocysteine.  The UGA codon is
    made to encode selenocysteine by the presence of a SECIS element
    (SElenoCysteine Insertion Sequence) in the mRNA.
    
    """
    
    def __init__(self, transl_table=1):
        self.transl_table = transl_table
        self.code = {}
        self.codonsForAA = {}
        self.startList = []

        if transl_table == 1: # standard
            AAs    = 'FFLLSSSSYY**CC*WLLLLPPPPHHQQRRRRIIIMTTTTNNKKSSRRVVVVAAAADDEEGGGG'
            Starts = '---M---------------M---------------M----------------------------'
            Base1  = 'TTTTTTTTTTTTTTTTCCCCCCCCCCCCCCCCAAAAAAAAAAAAAAAAGGGGGGGGGGGGGGGG'
            Base2  = 'TTTTCCCCAAAAGGGGTTTTCCCCAAAAGGGGTTTTCCCCAAAAGGGGTTTTCCCCAAAAGGGG'
            Base3  = 'TCAGTCAGTCAGTCAGTCAGTCAGTCAGTCAGTCAGTCAGTCAGTCAGTCAGTCAGTCAGTCAG'

        elif transl_table == 2: # vertebrate mito
            AAs      = 'FFLLSSSSYY**CCWWLLLLPPPPHHQQRRRRIIMMTTTTNNKKSS**VVVVAAAADDEEGGGG'
            Starts   = '--------------------------------MMMM---------------M------------'
            Base1    = 'TTTTTTTTTTTTTTTTCCCCCCCCCCCCCCCCAAAAAAAAAAAAAAAAGGGGGGGGGGGGGGGG'
            Base2    = 'TTTTCCCCAAAAGGGGTTTTCCCCAAAAGGGGTTTTCCCCAAAAGGGGTTTTCCCCAAAAGGGG'
            Base3    = 'TCAGTCAGTCAGTCAGTCAGTCAGTCAGTCAGTCAGTCAGTCAGTCAGTCAGTCAGTCAGTCAG'

        elif transl_table == 4: # Mold, Protozoan,
                                # and Coelenterate Mitochondrial Code and the Mycoplasma/Spiroplasma Code
            AAs    = 'FFLLSSSSYY**CCWWLLLLPPPPHHQQRRRRIIIMTTTTNNKKSSRRVVVVAAAADDEEGGGG'
            Starts = '--MM---------------M------------MMMM---------------M------------'
            Base1  = 'TTTTTTTTTTTTTTTTCCCCCCCCCCCCCCCCAAAAAAAAAAAAAAAAGGGGGGGGGGGGGGGG'
            Base2  = 'TTTTCCCCAAAAGGGGTTTTCCCCAAAAGGGGTTTTCCCCAAAAGGGGTTTTCCCCAAAAGGGG'
            Base3  = 'TCAGTCAGTCAGTCAGTCAGTCAGTCAGTCAGTCAGTCAGTCAGTCAGTCAGTCAGTCAGTCAG'

        elif transl_table == 5: # invertebrate mito
            AAs    = 'FFLLSSSSYY**CCWWLLLLPPPPHHQQRRRRIIMMTTTTNNKKSSSSVVVVAAAADDEEGGGG'
            Starts = '---M----------------------------MMMM---------------M------------'
            Base1  = 'TTTTTTTTTTTTTTTTCCCCCCCCCCCCCCCCAAAAAAAAAAAAAAAAGGGGGGGGGGGGGGGG'
            Base2  = 'TTTTCCCCAAAAGGGGTTTTCCCCAAAAGGGGTTTTCCCCAAAAGGGGTTTTCCCCAAAAGGGG'
            Base3  = 'TCAGTCAGTCAGTCAGTCAGTCAGTCAGTCAGTCAGTCAGTCAGTCAGTCAGTCAGTCAGTCAG'

        elif transl_table == 6: # The Ciliate, Dasycladacean and Hexamita Nuclear Code (transl_table=6)
            AAs    = 'FFLLSSSSYYQQCC*WLLLLPPPPHHQQRRRRIIIMTTTTNNKKSSRRVVVVAAAADDEEGGGG'
            Starts = '-----------------------------------M----------------------------'
            Base1  = 'TTTTTTTTTTTTTTTTCCCCCCCCCCCCCCCCAAAAAAAAAAAAAAAAGGGGGGGGGGGGGGGG'
            Base2  = 'TTTTCCCCAAAAGGGGTTTTCCCCAAAAGGGGTTTTCCCCAAAAGGGGTTTTCCCCAAAAGGGG'
            Base3  = 'TCAGTCAGTCAGTCAGTCAGTCAGTCAGTCAGTCAGTCAGTCAGTCAGTCAGTCAGTCAGTCAG'

        # tables 7 and 8 have been deleted from NCBI.
        
        elif transl_table == 9: # echinoderm and flatworm mito
            AAs    = 'FFLLSSSSYY**CCWWLLLLPPPPHHQQRRRRIIIMTTTTNNNKSSSSVVVVAAAADDEEGGGG'
            Starts = '-----------------------------------M----------------------------'
            Base1  = 'TTTTTTTTTTTTTTTTCCCCCCCCCCCCCCCCAAAAAAAAAAAAAAAAGGGGGGGGGGGGGGGG'
            Base2  = 'TTTTCCCCAAAAGGGGTTTTCCCCAAAAGGGGTTTTCCCCAAAAGGGGTTTTCCCCAAAAGGGG'
            Base3  = 'TCAGTCAGTCAGTCAGTCAGTCAGTCAGTCAGTCAGTCAGTCAGTCAGTCAGTCAGTCAGTCAG'

        elif transl_table == 10: # The Euplotid Nuclear Code (transl_table=10)
            AAs    = 'FFLLSSSSYY**CCCWLLLLPPPPHHQQRRRRIIIMTTTTNNKKSSRRVVVVAAAADDEEGGGG'
            Starts = '-----------------------------------M----------------------------'
            Base1  = 'TTTTTTTTTTTTTTTTCCCCCCCCCCCCCCCCAAAAAAAAAAAAAAAAGGGGGGGGGGGGGGGG'
            Base2  = 'TTTTCCCCAAAAGGGGTTTTCCCCAAAAGGGGTTTTCCCCAAAAGGGGTTTTCCCCAAAAGGGG'
            Base3  = 'TCAGTCAGTCAGTCAGTCAGTCAGTCAGTCAGTCAGTCAGTCAGTCAGTCAGTCAGTCAGTCAG'


        elif transl_table == 11: # The Bacterial and Plant Plastid Code (transl_table=11)
            AAs    = 'FFLLSSSSYY**CC*WLLLLPPPPHHQQRRRRIIIMTTTTNNKKSSRRVVVVAAAADDEEGGGG'
            Starts = '---M---------------M------------MMMM---------------M------------'
            Base1  = 'TTTTTTTTTTTTTTTTCCCCCCCCCCCCCCCCAAAAAAAAAAAAAAAAGGGGGGGGGGGGGGGG'
            Base2  = 'TTTTCCCCAAAAGGGGTTTTCCCCAAAAGGGGTTTTCCCCAAAAGGGGTTTTCCCCAAAAGGGG'
            Base3  = 'TCAGTCAGTCAGTCAGTCAGTCAGTCAGTCAGTCAGTCAGTCAGTCAGTCAGTCAGTCAGTCAG'

        elif transl_table == 12: # The Alternative Yeast Nuclear Code (transl_table=12)
            AAs    = 'FFLLSSSSYY**CC*WLLLSPPPPHHQQRRRRIIIMTTTTNNKKSSRRVVVVAAAADDEEGGGG'
            Starts = '-------------------M---------------M----------------------------'
            Base1  = 'TTTTTTTTTTTTTTTTCCCCCCCCCCCCCCCCAAAAAAAAAAAAAAAAGGGGGGGGGGGGGGGG'
            Base2  = 'TTTTCCCCAAAAGGGGTTTTCCCCAAAAGGGGTTTTCCCCAAAAGGGGTTTTCCCCAAAAGGGG'
            Base3  = 'TCAGTCAGTCAGTCAGTCAGTCAGTCAGTCAGTCAGTCAGTCAGTCAGTCAGTCAGTCAGTCAG'


        elif transl_table == 13: # The Ascidian Mitochondrial Code (transl_table=13)
            AAs    = 'FFLLSSSSYY**CCWWLLLLPPPPHHQQRRRRIIMMTTTTNNKKSSGGVVVVAAAADDEEGGGG'
            Starts = '---M------------------------------MM---------------M------------'
            Base1  = 'TTTTTTTTTTTTTTTTCCCCCCCCCCCCCCCCAAAAAAAAAAAAAAAAGGGGGGGGGGGGGGGG'
            Base2  = 'TTTTCCCCAAAAGGGGTTTTCCCCAAAAGGGGTTTTCCCCAAAAGGGGTTTTCCCCAAAAGGGG'
            Base3  = 'TCAGTCAGTCAGTCAGTCAGTCAGTCAGTCAGTCAGTCAGTCAGTCAGTCAGTCAGTCAGTCAG'

        elif transl_table == 14: # The Alternative Flatworm Mitochondrial Code (transl_table=14)
            AAs    = 'FFLLSSSSYYY*CCWWLLLLPPPPHHQQRRRRIIIMTTTTNNNKSSSSVVVVAAAADDEEGGGG'
            Starts = '-----------------------------------M----------------------------'
            Base1  = 'TTTTTTTTTTTTTTTTCCCCCCCCCCCCCCCCAAAAAAAAAAAAAAAAGGGGGGGGGGGGGGGG'
            Base2  = 'TTTTCCCCAAAAGGGGTTTTCCCCAAAAGGGGTTTTCCCCAAAAGGGGTTTTCCCCAAAAGGGG'
            Base3  = 'TCAGTCAGTCAGTCAGTCAGTCAGTCAGTCAGTCAGTCAGTCAGTCAGTCAGTCAGTCAGTCAG'
            
        elif transl_table == 21: # Trematode Mitochondrial Code (transl_table=21)
            AAs    = 'FFLLSSSSYY**CCWWLLLLPPPPHHQQRRRRIIMMTTTTNNNKSSSSVVVVAAAADDEEGGGG'
            Starts = '-----------------------------------M---------------M------------'
            Base1  = 'TTTTTTTTTTTTTTTTCCCCCCCCCCCCCCCCAAAAAAAAAAAAAAAAGGGGGGGGGGGGGGGG'
            Base2  = 'TTTTCCCCAAAAGGGGTTTTCCCCAAAAGGGGTTTTCCCCAAAAGGGGTTTTCCCCAAAAGGGG'
            Base3  = 'TCAGTCAGTCAGTCAGTCAGTCAGTCAGTCAGTCAGTCAGTCAGTCAGTCAGTCAGTCAGTCAG'



        else:
            print "GeneticCode: I don't know that transl_table.  Get it from NCBI and add it!"
            sys.exit()

        for i in range(64):
            theCodon = string.lower(Base1[i] + Base2[i] + Base3[i])
            theAA = string.lower(AAs[i])
            self.code[theCodon] = theAA
            if self.codonsForAA.has_key(theAA):
                self.codonsForAA[theAA].append(theCodon)
            else:
                self.codonsForAA[theAA] = [theCodon]
            if Starts[i] == 'M':
                self.startList.append(theCodon)

        if 1:
            self.codonsForAA['b'] = self.codonsForAA['n'] + self.codonsForAA['d']
            self.codonsForAA['z'] = self.codonsForAA['q'] + self.codonsForAA['e']

        if 1:
            self.codonsForAA['u'] = ['tga']  # selenocysteine

        if 0:
            k = self.code.keys()
            k.sort()
            for aKey in k:
                print "%20s  %-30s" % (aKey, self.code[aKey])

    def wise2Table(self):
        """Output in a form suitable to replace codon.table in wise2"""

        print "! this is a codon table"
        print "! by p4, for ncbi %i" % self.transl_table
        for first in "tcag":
            for second in "tcag":
                for third in "tcag":
                    lcod = "%s%s%s" % (first,second,third)
                    ret = self.code[lcod]
                    if ret == '*':
                        ret = 'X'
                    print lcod.upper(), ret.upper()
                    
                    
