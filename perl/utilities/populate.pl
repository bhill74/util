$table = $ARGV[0];
@fields = split( ',', $ARGV[1] );

$command = "/depot/mysql-4.0.18/bin/mysql -u cadabra -h birch -D cadabraWeb -e ";

while ( <STDIN> ) {
  s/\s*$//;
  my @values = split( "," );
  $query  = "INSERT INTO `$table` (`".join( "`, `", @fields )."`) VALUES (\"".join( "\", \"", @values )."\");";
  #$query =~ s/'/\\'/g;
  #print "$command '$query'\n";
  `$command '$query'`
}
