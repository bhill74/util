<?php

/****************************************************
 * Includes:
 */
set_include_path( get_include_path() . PATH_SEPARATOR . "$_ENV[HOME]/public_html/charts" );

include_once( "html.php" );

/* ##################################################
 * Class UISelect
 *
 * Used to construct an autocomplete dropdown.
 *
 */
class UISelect {    
  /*************************************************
   *%FUNCTION: select
   *%DESCRIPTION:
   * Used to create a FORM SELECT element.
   *%ARGUMENTS:
   * name -- The name of the select.
   * info -- The array of values to use for options.
   * [value] -- The selected value
   * [order] -- The order of the options.
   * [settings] -- The settings to be included in the HTML element.
   *%RETURNS:
   * The generated HTML.
   */ 
  public static function select( $name, $source,
				 $value = '',
				 $settings = array() ) {
    $idSuffix = "_id";
    $idName = "${name}${idSuffix}";       
    $html = HTML::js_jquery_ui();

    /* If provided then include a label */
    if ( isset( $settings['label'] ) ) {
      $html .= HTML::wrap( 'label', $settings['label'], array( 'for' => $name ) );
    }
    
    /* Define an entry for the results, and if altered it will
     * clear the ID entry.
     */
    $html .= HTML::entry( $name, array( 'id' => $name,
					'onkeydown' => "$('#${idName}').val('');" ) );
    /* Define a hidden entry for the corresponding ID (if one
     * exists
     */
    //$html .= HTML::hidden( $idName, $value, array( 'id' => $idName ) );
    $html .= HTML::entry( $idName, array( 'id' => $idName, 'value' => $value ) );

    /* Wrap them both up into a DIV tag.
    $html = HTML::div( $html, array( 'class' => 'ui-widget' ) );    
    
    /* Get the minimum number of keystrokes that should be used */
    $minLength = ( isset( $settings['minLength'] ) ) ? $settings['minLength'] : 2;  
    $source .= "&minLength=${minLength}";
    
    /* Get the code for rendering the item in the dropdown.
     * If not provided, use the default that includes 'label', 'icon' and 'description' 
     * Assume arguments are 'ul' and 'item'.
     */
    $render =  "if ( item.icon != undefined ) {\n";
    $render .= "   entry = entry + \"<img width=25 src=\\\"images/\" + item.icon + \"\\\">\";\n";
    $render .= "}\n";
    $render .= "entry = entry + item.label;\n";
    $render .= "if ( item.desc != undefined ) {\n";
    $render .= "   entry = entry + \"<br><i><font size=-2>\" + item.desc + \"</font></i>\";\n";
    $render .= "}";
    $render = ( isset( $settings['render'] ) ) ? $settings['render'] : $render;

    /* Get the code for processing the selected item from
     * the dropdown. If not provided use the default that sets
     * the corresponding ID
     * Assume arguments are 'event' and 'ui'
     */
    //$select =  "var id = this.name + \"${idSuffix}\";\n";   
    $select = "$( \"#${idName}\" ).val( ui.item.id );";
    $select = ( isset( $settings['select'] ) ) ? $settings['select'] : $select;
    $selectExtra = ( isset( $settings['selectExtra'] ) ) ? $settings['selectExtra'] : '';
    
    /* Define the code that should be attached for the autocomplete
     * widget
     */
    $code = "$(function() {\n";
    $code .= "  $( \"#${name}\" ).autocomplete({\n";
    $code .= "     source: \"${source}\",\n";
    $code .= "     minLength: ${minLength},\n";
    $code .= "     select: function( event, ui ) {\n";
    $indent = "        ";
    $code .= $indent . preg_replace( '/\n/', "\n${indent}", $select ) . "\n";
    if ( $selectExtra != "" ) {
      $code .= $indent . preg_replace( '/\n/', "\n${indent}", $selectExtra ) . "\n";
    }
    $code .= "     }\n";
    $code .= "  }).data( \"autocomplete\" )._renderItem = function( ul, item ) {\n";
    $code .= "     var entry = '';\n";
    $indent = "     ";
    $code .= $indent . preg_replace( '/\n/', "\n${indent}", $render ) . "\n";
    $code .= "     return $( \"<li></li>\" )\n";
    $code .= "            .data( \"item.autocomplete\", item )\n";
    $code .= "            .append( \"<a>\" + entry + \"</a>\" )\n";
    $code .= "            .appendTo( ul );";
    $code .= "  };\n";
    $code .= "});\n";
    $html .= HTML::js_code( $code );
    return $html;    
  }
}

?>
