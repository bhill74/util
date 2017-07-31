/*****************************************************************************
 *  FILE:  exchange.js - The Any+Time(TM) JavaScript Library (source)
 *
 * 
 ****************************************************************************/
var rateCache = new Array();
rateCache['CAD'] = 1;

function updateRate( table, select ) {
  return '';
  var entry = document.getElementById( table + '.exchange' );  
  var code = select.options[select.selectedIndex].value;

  if ( rateCache[code] === undefined ) {
    var url = "get_rate.php?from="+code+"&to=CAD"; 
    var id = '#'+table+'.download';
    var download = document.getElementById( table+'.download' );
    alert( url + " " + download.id );
    $('#'+download.id).load( url, function( response, status, xhr ) {
			       alert( "B" );
			       alert( status );
			     } );   
    alert( 'DOWN ' + download.innerHTML );
    rateCache[code] = download.innerHTML;
  }
  entry.value = rateCache[code];
}
