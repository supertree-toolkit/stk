package main;
# Pod Include parser.

=head1 USAGE

    pod2include.pl <filename>

    <fn_switch> = a switch that must preceed the filename for the child
                  parser. use an empty string (e.g. '') if the parser
              doesn't require one.

=head1 POD CONVENTIONS

This formatter creates a .pod file based on the original input file, but with
"include" interpolations.  Any line that reads similar to

    =for include filename.pod

will cause the text in C<filename.pod> to be included at that point. Other
formatters will simply skip the file.

The output of this formatter is POD printed to STDOUT.  This is suitable  for
piping to (for example) pod2html.

=cut

use strict; use warnings;
use IO::File;

for (@ARGV) {
    my $source = $_;
    my $IN = IO::File->new($source,'<') or die ("Can't read $source: $!");
    my $SCRATCH = IO::File->new(">&STDOUT") or die ("Can't clone STDOUT: $!");

    my $p = Parser->new();
    $p->parse_from_filehandle($IN, $SCRATCH);

    $IN->close;
    $SCRATCH->close;
}


#==============================================================================
package Parser;
use base 'Pod::Parser';

sub preprocess_paragraph {
    my ($self, $content) = @_;
    
    my $text;
    
    if ($content =~ /^=for include (.*)/) {
        my $file = $1;
        $file =~ s/^\s+|\s+$//s;
        if ( -f $file ) {
            open my $SOURCE, '<', $file or die ("Can't source $file: $!");
            $text = join('',<$SOURCE>)."\n\n";
            # remove any comment lines
            $text =~ s/\#+.*\n//g;
            # remove the REQUIRES, FEEDBACK and AUTHORS sections
            $text =~ s/=head1 REQUIRES.*(=head1 )/$1/s;
            $text =~ s/=head1 AUTHORS.*//s;
            $text =~ s/=head1 FEEDBACK.*(=head1 )/$1/s;
            
            # becuase of how Pod::Usage works it needs the sections in =head1, so 
            # lets replace them - we need to do the case anyway...
            $text =~ s/head1 OPTIONS/head2 Options/g;
            $text =~ s/head1 SYNOPSIS/head2 Synopsis/g;
            $text =~ s/head1 DESCRIPTION/head2 Description/g;
            $text =~ s/head1 EXAMPLES/head2 Examples/g;
            
            # move headings down a level
            $text =~ s/\=head3/\=head4/g;
            $text =~ s/\=head2/\=head3/g;
            $text =~ s/\=head1/\=head2/g;
            
            close $SOURCE;
        }
        else {
            $text = "I<Can't find file '$file' during include>.\n\n";
        }
    }
    else {
        $text = Pod::Parser::preprocess_paragraph(@_);
    }
    
    return $text;
}
