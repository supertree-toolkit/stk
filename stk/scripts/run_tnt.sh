#!/bin/bash

for i in $(seq $1 $2); do
    tnt mxram 1024, log tnt_log.$i.txt, run Matrix.tnt, echo= , timeout 24:00:00, rseed0, rseed*,hold 1000,xmult= level 10, taxname=, tsave *trees_tnt.$i.tnt, save, tsave / , scores, log / , nelsen *, tsave *strict_consensus.$i.tnt, save /, tsave / ,majority *, tsave *majority_consensus.$i.tnt, save /, tsave / , quit  ;
done;

