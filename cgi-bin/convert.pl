#!/usr/bin/perl -w

use warnings FATAL => 'all';
use strict;
use CGI; # perl -e shell -MCPAN >> install CGI


print "Content-type: text/html\n\n";

my $cgi = CGI->new();
# Retrieve the value of a query parameter named 'path'
my $flv = $cgi->param('flv');
#print "The value of the parameter 'path' is: $param_value\n\r";

system qq(ffmpeg -h);
print( "echo The flv filename is: $flv" );