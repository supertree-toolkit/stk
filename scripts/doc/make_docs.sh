#!/bin/bash

# generate Master POD
perl pod2include.pl STK_header.pod > STK.pod

# Generate HTML version
pod2html --title STK --backlink "Back to top" STK.pod --css styles.css > STK.html

# Generate WIKI version
pod2wiki --style mediawiki STK.pod > STK.wiki
