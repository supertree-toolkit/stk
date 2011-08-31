#/usr/bin/perl -w

use Test::Harness qw(&runtests $verbose);

$verbose=1;

runtests @ARGV;
