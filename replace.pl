use File::Basename;

sub replace {
  my( $src, $tgt ) = @_;
  # Shell
  s/\$\{$src\}/$tgt/g;
  # Perl
  s/\$ENV\{$src\}/$tgt/g;
  # PHP
  s/\$_ENV\[$src\]/$tgt/g;
  # AL
  s/getenv\(\s*\"$src\"\s*\)\s*\+\s*\"/\"$tgt/g;   
  # TCL
  s/\$::env\{$src\}/$tgt/g;
}

replace( "HOME", $ENV{HOME} );
replace( "PWD", dirname($ARGV) );
