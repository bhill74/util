package process;

#**************************************************
# Used to process the parent command (calling)
#%ARGUMENTS
# None
#%RETURNS
# Nothing, but the environment will be changed.
#**************************************************
# No process has been logged and this is a top level function
my $parent=(caller(1))[3];
if ( ! defined $ENV{_process} && $parent == 'main::BEGIN') {
  my $args=join( " ", @ARGV );
  my $fpath=$0;
  my ( $dir, $base ) = ( $fpath =~ m|^(.*)/([^/]+)$| );
  ( $dir ) = `pushd $dir >/dev/null 2>&1;pwd`;
  chomp $dir;
  `$ENV{HOME}/util/process/process_cmd -P $$ -c ${base} -p \"$dir\" -a "$args" 2>/dev/null`;
  $ENV{_process}=done;
}

1;
