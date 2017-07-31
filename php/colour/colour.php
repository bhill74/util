<?php

class Colour {

  /****************************************************
   *%FUNCTION: hex2rgb
   *%DESCRIPTION: Used to convert a HEX (Hexidecimal) 
   * colour string to RGB (Reg/Green/Blue) array.
   *%ARGUMENTS:
   * hex -- The HEX string to convert.
   *%RETURNS:
   * The RGB equivalent.
   */
  function hex2rgb( $hex ) {
    $hex = preg_replace("/[^0-9A-Fa-f]/", '', $hex ); // Gets a proper hex string.
    $rgb = array();
    if (strlen($hex) == 6) { //If a proper hex code, convert using bitwise operation. No overhead... faster
      $colour = hexdec($hex);
      $rgb['r'] = 0xFF & ($colour >> 0x10);
      $rgb['g'] = 0xFF & ($colour >> 0x8);
      $rgb['b'] = 0xFF & $colour;
    } elseif (strlen($hex) == 3) { //if shorthand notation, need some string manipulations
      $rgb['r'] = hexdec(str_repeat(substr($hex, 0, 1), 2));
      $rgb['g'] = hexdec(str_repeat(substr($hex, 1, 1), 2));
      $rgb['b'] = hexdec(str_repeat(substr($hex, 2, 1), 2));
    } else {
      return false; //Invalid hex color code
    }
    return $rgb;
  }
  
  /****************************************************
   *%FUNCTION: hex_shift
   *%DESCRIPTION: Used to adjust a HEX (Hexadecimal)
   * array to darken (-negative) or lighten (+positive)
   * the colour by a percentage.
   *%ARGUMENTS:
   * hex -- The colour array to shift.
   * shift -- The percentage to shift by.
   *%RETURNS:
   * The adjusted HEX value.
   */ 
  function hex_shift( $hex, $shift = 0 ) {
    if ( $shift == 0 ) {
      return $hex;
    }
    $rgb = Colour::hex2rgb( $hex );
    $rgb = Colour::rgb_shift( $rgb, $shift );
    return Colour::rgb2hex( $rgb );
  }

  /****************************************************
   *%FUNCTION: rgb2hex
   *%DESCRIPTION: Used to convert a RGB (Red/Green/Blue)
   * array to a HEX (Hexidecimal) colour string
   *%ARGUMENTS:
   * rgb -- The RGB value to convert.
   *%RETURNS:
   * The HEX equivalent.
   */  
  function rgb2hex( $rgb ) {
    $hex = '';
    foreach ( array( 'r', 'g', 'b' ) as $component ) {
      $value = ( isset( $rgb[$component] ) ) ? $rgb[$component] : 0;
      $value = ( $value >= 0 ) ? $value : 0;
      $value = ( $value <= 255 ) ? $value : 0;
      $hex .= dechex( $value );
    }
    return $hex;
  }

  /****************************************************
   *%FUNCTION: rgb_shift
   *%DESCRIPTION: Used to adjust a RGB (Red/Green/Blue)
   * array to darken (-negative) or lighten (+positive)
   * the colour by a percentage.
   *%ARGUMENTS:
   * rgb -- The colour array to shift.
   * shift -- The percentage to shift by.
   *%RETURNS:
   * The adjusted RGB value.
   */ 
  function rgb_shift( $rgb, $shift = 0 ) {
    if ( $shift != 0 ) {
      foreach ( array_keys( $rgb ) as $component ) {
	$value = $rgb[$component];
	$value = intval( (1+$shift/100)*$value );
	$value = ( $value < 0 ) ? 0 : $value;
	$value = ( $value > 255 ) ? 255 : $value;
	$rgb[$component] = $value;
      }
    }
    return $rgb;   
  }
}

?>
