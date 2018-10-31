$time = $ARGV[0];

$rate = 5;

print "Brian's Consultation Service\n";
print "****************************\n\n";

if ( $time =~ /(\d+)m$/ ) {
	$time = $1/60;
}
elsif ( $time =~ /(\d+)/ ) {
	$time = $1;
}

printf( "%.02f x \$%s/hr = \$%0.2f\n", $time, $rate, $time*$rate );
