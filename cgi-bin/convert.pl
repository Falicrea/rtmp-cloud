#!/usr/bin/perl 

use CGI;  # perl -e shell -MCPAN >> install CGI

print "Content-type: text/html\n\n";

my $cgi = CGI->new();
# Retrieve the value of a query parameter named 'path'
my $param_value = $cgi->param('path');
print "The value of the parameter 'path' is: $param_value\n\r";
#system qq(ffmpeg -h);
