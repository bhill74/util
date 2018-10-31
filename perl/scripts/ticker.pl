# Ticker Watcher 

use LWP::Simple;

%tickers = ( "aty", "ATI Technologies",
	     "thqi", "THQ Inc.",
	     "nvda", "NVIDIA Corp.",
	     "hs", "CHS Electronics",
	     "creaf", "Creative Technology Ltd.",
	     "gtw", "Gateway Inc.",
	     "nmgc", "NeoMagic",
	     "bbar", "Balance Bar Co.",
	     "vcr", "Seonsory Science",
	     "tdfx", "3DFX",
	     "mty", "Marlton Technologies",
	     "yfa", "Yogen Fruz",
	     "mrvc", "MRV Communications",
	     "cpu", "Comp USA",
	     "osis", "OSI Systems",
	     "bnd", "Boundless Corp.",
	     "amd", "Advanced Micro Devices",
	     "qcom", "Qualcomm Inc.",
	     "cien", "Ciena",
	     "scsc", "Scansource",
	     "afci", "Advanced Fibre Comm." );

%otherSite = ( "aty", "ca",
	       "yfa", "ca" );

$site = "http://biz.yahoo.com";

foreach $ticker ( sort keys %tickers ) {
  $path = "/n";
  $path .= "/" . $otherSite{$ticker} if ( $otherSite{$ticker} );

  $url = sprintf( "%s%s/%s/%s.html", $site, $path, (split( '', $ticker ))[0], $ticker );
  
  $_ = get( $url );
  
  s/\s+/ /g;
  
  @dates = ();

  foreach $line ( split( /(<\/?ul>(<li>)?|<li>)/ ) ) {
    $date = $1 if ( $line =~ m|<small><b>([^>]+)</b></small>|i );
    if ( $date ) {
      #print "$date - $line\n";
    }

    $time = $1 if ( $line =~ /(\d+:\d+ [ap]m)$/i );
    
    if ( $date && 
	 ( ( $line =~ /Quarterly\s+Report\s+\(SEC\s+form/i && $line =~ /EDGAR Online/i ) ||
	   ( $line =~ /Quarter\s+Fiscal/i && $line =~ /PR Newswire/i ) ||
	   ( $line =~ /Quarter\s+Results/i && $line =~ /PR Newswire/i ) ||
	   ( $line =~ /Q\d+\s+Results/i && $line =~ /Reuters Securities/i ) ) ) {
      push( @dates, sprintf( "%s - %s", $date, $time ) );
    }
  }

  printf( "\n%-30s(%s)\n   %s\n", $tickers{$ticker}, $ticker, join( "\n   ", @dates ) );
}






