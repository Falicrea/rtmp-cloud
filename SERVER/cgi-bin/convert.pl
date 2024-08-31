#!/usr/bin/perl -w

use warnings FATAL => 'all';
use strict;
use CGI; # perl -e shell -MCPAN >> install CGI
use File::Basename;

print "Content-type: text/html\n\n";
my $cgi = CGI->new();
# Retrieve the value of a query parameter named 'flv'
my $flv = $cgi->param('flv');
my $filename = basename($flv, '.flv');
if(-e -f -r qq(/mnt$flv)) {
    system qq(ffmpeg -i /mnt$flv -vcodec libx2674 -acodec copy /mnt/mp4s/$filename.mp4);
} else {
    print "file not found"
}

