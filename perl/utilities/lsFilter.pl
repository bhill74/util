my $p = $ARGV[0];
my $total = 0;
my $sub = '';
while ( <STDIN> ) {
	if ( /^total (\d+)$/ ) {
		$total += $1;
	} elsif ( /(\S+) \-\> (\S+\s*)$/ ) {
	    my $f = "$`${p}${sub}/$1";
		my $o = $2;
		if ( $o !~ m|^/| && $o =~ m|^(\S+/)?| ) {
			my $d = `readlink -f ${p}${sub}/$1`;
            chomp $d;		   
		    $o = "$d/$'";
		}
		print "$f -> $o";
	} elsif ( /^((.*):\s*)$/ ) {
	    $sub = "/$2";
	    if ( $p eq '/' ) {
			print "/$1";
		} else {		
		   print "${p}/$1";
	    }
	} elsif ( /(\S+\s*)$/ ) {
	    if ( $p eq '/' ) {
			print "${sub}/$1";
		} else {
			print "$`${p}${sub}/$1";
		}
	}
}
if ($total > 0) {
	print "total $total\n";
}