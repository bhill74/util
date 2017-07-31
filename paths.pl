while ( m|/usr/bin/env (\w+)| || m|/bin/env (\w+)| ) {
  my ( @which ) = `which $1`;
  my $path = $which[0];
  $_ = $`.$path.$';
}
