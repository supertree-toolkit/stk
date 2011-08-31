#!/usr/bin/perl -w

sub standard_tests {

  $exec = shift;

  # check we get the usage message when using help
  my $output =`perl $exec.pl -h`;
  like($output,  qr/$exec.pl \[options\]/,'Got help message ok');

  # and with long options
  my $output2 =`perl $exec.pl --help`;
  ok($output eq $output2,'Got help message ok with long option');

  # check man options
  $output =`perl $exec.pl -m`;
  # authors is the last to be printed - also means someone will have to alter the test to 
  # remove my name (and if I change my email!)
  like($output,  qr/Jon Hill \(jon.hill\@imperial.ac.uk\)/,'Got man message ok');
  $output2 =`perl $exec.pl --man`;
  ok($output eq $output2,'Got man message ok with long option');

  # finally we should get the help with no options
  $output =`perl $exec.pl`;
  like($output,  qr/$exec.pl \[options\]/,'Correct behaviour with no options specified');
}

1;
