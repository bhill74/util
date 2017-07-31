<?php

/****************************************************
 * Includes:
 */
set_include_path( get_include_path() . PATH_SEPARATOR . "$_ENV[HOME]/public_html/charts" );

include_once 'file.php';
include_once 'arguments.php';
include_once 'html.php';

/****************************************************
 * Chart utilities
 * 
 * Utilities used to process information and prepare
 * the OFC Charts.
 */

class Chart
{
    private static $chart_dimensions = array();

    function process_dimensions( $settings,
				 $width = 100,
				 $height = false ) {

      $width = ( isset( $settings['width'] ) &&
		 $settings['width'] > 0 ) ? $settings['width'] : $width;
      $height = ( isset( $settings['height'] ) &&
		  $settings['height'] > 0 ) ? $settings['height'] : $height;
      $height = ( $height === false ) ? $width : $height;
      $resize = ( isset( $settings['resize'] ) ) ? $settings['resize'] : false;
      
      return array( 'width' => $width,
		    'height' => $height,
		    'resize' => $resize );
    }

    /****************************************************
     *%FUNCTION: head
     *%DESCRIPTION: Used to generate the HTML and Javascript
     * necessary for the header of the page.
     *%ARGUMENTS:
     * url -- The URL of the data source.
     * [name = 'chart'] -- The name of the chart.
     * [dimensions] -- The width, height, padding and resize value.
     *%RETURNS:
     * The resulting HTML and Javascript code.
     */
    function head( $url, $name = 'chart', $dimensions = 100 ) {
      /* Sort out the dimensions of the chart */
      if ( is_array( $dimensions ) ) {
	if ( isset( $dimensions['height'] ) &&
	     !isset( $dimensions['width'] ) ) {
	  $dimensions['width'] = $dimensions['height'];
	} else if ( isset( $dimensions['width'] ) &&
		    !isset( $dimensions['height'] ) ) {
	  $dimensions['height'] = $dimensions['width'];
	} 
	$dimensions['resize'] = ( isset( $dimensions['resize'] ) ) ? $dimensions['resize'] : false;
	$dimensions['padding'] = ( isset( $dimensions['padding'] ) ) ? $dimensions['padding'] : 10;
      } else {
	$dimensions = array( 'width' => $dimensions,
			     'height' => $dimensions,
			     'padding' => 10,
			     'resize' => false );
      }
      
      Chart::$chart_dimensions[$name] = $dimensions;
      $width = $dimensions['width'];
      $height = $dimensions['height'];
      if ( $dimensions['resize'] === true ) {
	$width = '100%';
	$height = '100%';
      }      
      
      /* Run the Javascript necessary */
      $html = HTML::js_load( "charts/js/swfobject.js" );
      $ofc_file = 'charts/open-flash-chart.swf';
      $directory = File::getRelativePath( $ofc_file, '', 'up' );
      $code =  "  swfobject.embedSWF( \"${directory}${ofc_file}\", \"${name}\", \n";
      $code .= "    \"${width}\", \"${height}\", \"9.0.0\", \"expressInstall.swf\", \n";
      $code .= "    {\"data-file\":\"" . urlencode( $url ) . "\"} );\n\n";

      if ( $dimensions['resize'] === true ) {
	//$code .= "  \$(document).ready(function() {\n";
	$code .= "  \$(function() {\n";
	$code .= "    \$(\"#resizeable\").resizable();\n";
	$code .= "  });";	
	
	$html .= HTML::js_jquery_ui();
      }
      
      $html .= HTML::js_code( $code );
      
      /* Return the HTML */
      return $html;
    }
    
    function place( $name = 'chart' ) {
      $dimensions = array( 'resize' => false );
      if ( isset( Chart::$chart_dimensions[$name] ) ) {
	$dimensions = Chart::$chart_dimensions[$name];
      }

      $html = HTML::div( '', array( 'id' => $name ) );
      if ( $dimensions['resize'] === true ) {
	$html = HTML::div( $html,
			   array( 'id' => 'resizeable',
				  'style' => array( "width:$dimensions[width]px",
						    "height:$dimensions[height]px",
						    "padding:$dimensions[padding]px",
						    'border-style:dashed',
						    'border-width:2px' ) ) );
      }
      return $html;
    }
}   

?>
