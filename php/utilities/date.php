<?php

/****************************************************
 * Includes:
 */

/* ##################################################
 * Class Date
 *
 * Used to process Date strings
 *
 */
class Date { 
  /**************************************************
   *%FUNCTION: dates
   *%DESCRIPTION:
   * Used to create a range of dates for every day
   * between two values.
   *%ARGUMENTS:
   * start -- The starting date.
   * stop -- The stopping date.
   *%RETURNS:
   * The array of dates created.
   */
  function dates( $start, $stop ) {
    $dates = array();
  
    /* Process the start and end time */
    $begin = mktime( 1,0,0,substr($start,5,2),     
		     substr($start,8,2),
		     substr($start,0,4) );
    $end = mktime( 1,0,0,substr($stop,5,2),
		   substr($stop,8,2),
		   substr($stop,0,4) );
    
    if ($end>=$begin) {
      array_push( $dates, date( 'Y-m-d', $begin ) ); // first entry
      
      while ( $begin < $end ) {
	$begin += 86400; // add 24 hours
	array_push( $dates, date( 'Y-m-d', $begin ) );
      }
    }
    return $dates;
  }
}

?>
