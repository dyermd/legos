#!/usr/bin/perl -w

use strict;

{
    my ($file) = @ARGV;

    open(IN, $file) || die "Could not open $file\n";

    while(my $line = <IN>){
	chomp($line);
	my ($epic, $description, $product) = split(/\t/, $line);
	my $systemCall = "python add_epic_to_jira.py -a 'Hardware' -c 'Hardware' -d '$product' -n '$description' -e '$epic' -v '1.0' -x 'HW' -y 'Critical' -u 'mdyer' -p 'F\@m1l13s' -s 'https://jira.butterflynetinc.com'";
	#print "$systemCall\n";
	system($systemCall);
    }

    close(IN);

}

1;
