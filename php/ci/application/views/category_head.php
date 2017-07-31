<?php

require_once( "category.php" );
require_once( "finance_gui.php" );

class CategoryGUI extends FinanceGUI {  
  /*****************************************
   *%FUNCTION: js_categoriesList()
   *%DESCRIPTION:
   * Used to produce the JS code for the menu 
   * of options that will be used for category
   * selection.
   *%ARGUMENTS:
   * [name = 'categories'] - The name of the array
   * to produce code for.
   * [tree = false] - The current level of the
   * category tree.
   *%RETURNS:
   * The code to produce the JS array.
   */
  public static function js_categoriesList( $name = 'categories', $tree = false ) {    
    $code = '';
    $Category = Category::get();   

    if ( $tree === false ) {      
      $tree = $Category->tree();
      $code .= "var ${name} = new Array();\n";
    }   
    
    foreach( array_keys( $tree ) as $category ) {      
      $prefix = "${name}['${category}']";
      $code .= "${prefix} = new Array();\n";
      $info = $Category->info( $category );
      $id = $info['category_id'];
      $code .= "${prefix}[${id}] = '${category}';\n";
      $code .= CategoryGUI::js_categoriesList( $prefix, $tree[$category] );
    }
    
    return $code;
  }

  public static function head( $settings = array() ) {
    $html  = FinanceGUI::head( $settings );
    $html .= HTML::js_load( "js/jsColor/jscolor.js" );
    $html .= FinanceGUI::menu_head( $settings );   
    $name = 'categories';
    $code = CategoryGUI::js_categoriesList( $name );
    $code .= "jsselectmenu.add( 'category', ${name} );\n";
    $html .= HTML::js_code( $code );
    return $html;
  }   
  
  /*****************************************
   *%FUNCTION: category()
   *%DESCRIPTION:
   * Used to produce the HTML code for creating
   * a product select object.
   *%ARGUMENTS:
   * name -- The name of the field.
   * value -- The value to consider as the default.
   *%RETURNS:
   * The HTML code.
   */  
  public static function category( $name, $value = '', $settings = array() ) {
    $settings['class'] = "category";
    return FinanceGUI::menu( $name, $value, $settings );
  }
  
  public static function category2( $name, $value = '', $settings = array() ) {
    /* Display the path but only if provided */
    $render  = "entry = item.label;\n";
    $render .= "if ( item.option != undefined ) {\n";
    $render .= "   entry = item.option;\n";
    $render .= "}\n";
    $render .= "if ( item.path != undefined ) {\n";
    $render .= "   entry = entry + \"<br><i><font size=-2>\" + item.path + \"</font></i>\";\n";
    $render .= "}";
    
    $source = "query.php?type=categories";
    
    $settings['minLength'] = 3;
    $settings['render'] = $render;

    return UISelect::select( $name, $source, $value, $settings );
  }
}

<?php if ( $edit !== false ) open_form( "category" ); ?>

<table border=0 cellpadding=0 cellspacing=0>
<tr>
<?php

$buttonWidth = 15;
$cellWidth = 150;
$directions = array( 'T' => 'Up', 
                     'B' => 'Down', 
                     'L' => 'Left', 
                     'R' => 'Right' );

  /*****************************************
   *%FUNCTION: shiftButton()
   *%DESCRIPTION:
   * Used to create a link that will shift a category in a given direction
   *%ARGUMENTS:
   * url -- The url to with (minus the direction parameter).
   * direction -- The direction to account for. 
   *%RETURNS:
   * The HTML code for the option. 
   */
function shiftButton( $url, $direction ) {
    $string = CategoryGUI::$directions[$direction];
    $image = HTML::image( 'images/buttons/' . strtolower( $string ) . '.png',
			  array( 'alt' => "[${string}]",
				 'width' => CategoryGUI::$buttonWidth,
				 'align' => 'right' ) );
    return HTML::wrap( 'a', $image, array( 'href' => "${url}&direction=" . strtolower( $string ) ) );
  }

  /*****************************************
   *%FUNCTION: shiftButtons()
   *%DESCRIPTION:
   * Used to create a series of links that 
   * will shift the category in the given directions.
   *%ARGUMENTS:
   * url -- The url to with (minus the direction parameter).
   * directions -- The directions to account for. 
   *%RETURNS:
   * The HTML code for the options. 
   */
function shiftButtons( $url, $directions ) {
    $buttons = array();
    foreach ( preg_split( '//', $directions ) as $direction ) {
      if ( $direction == '' ) {
	continue;
      }
      array_push( $buttons, shiftButton( $url, $direction ) );
    }
    return implode( '<br/>', $buttons );
  }  

  private function add( $category ) {   
      return HTML::entry( Finance::toFieldName( $category, 'names' ) );
  }

  public static function color( $name, $value = '', $settings = array() ) {   
    $settings['value'] = $value;
    $settings['class'] = 'color';
    if ( !isset( $settings['size'] ) ) {
      $settings['size'] = 6;
    }
    return HTML::entry( $name, $settings );   
  }

  private function nickname( $category, $nickname = '' ) {   
    return HTML::entry( Finance::toFieldName( $category, 'nickname' ),
			array( 'size' => 3,
			       'value' => $nickname ) );  
    return $html;
  } 

function cell( $category, $info, $directions, $url ) {
    $html = "<table cellpadding=0 cellspacing=0 width=" . $cellWidth . ">\n";
    $html .= "<tr><td width=" . ( $cellWidth - $buttonWidth ) . ">\n";
    $html .= "<font size=+2><b>$category</b></font><br>\n";
    $html .='<font size=-2><i>[' . $info['left'] . ', ' . $info['right'] . ' - ' . $info['depth'] . ']</i></font>';
    $html .= "</td><td valign=top align=right rowspan=3 width=" . $buttonWidth . ">&nbsp;";
    if ( $url !== false ) {
      $html .= CategoryGUI::shiftButtons( $url, $directions );
    }
    $html .= "</td></tr>\n";

    if ( $url !== false ) {
      $html .= "<td>Color: ";
      $html .= color( $category, $info );	  
      $html .= "</td></tr>\n<td>Nickname: ";
      $html .= nickname( $category, $info );	 
      $html .= "</td></tr>\n";
    }
    
    $html .= "</table>\n";
    return $html;
  }

 /*****************************************
  *%FUNCTION: makeRow()
  *%DESCRIPTION:
  * Used to create a recursive construction
  * of a row representing a hierarchy of categories.
  *%ARGUMENTS:
  * tree -- The tree to build for.
  * url -- The url for editing these categories.
  * count -- The referenced counter to populate with the
  * the total number of rows in the tree.
  * level -- The current level being processed in the
  * tree, by default is 1.
  *%RETURNS:
  * The HTML code for the options.
  */
public function makeRow( $tree, $url = false, &$count = 0, $level = 1 ) {
    $html = '';
    $categories = array_keys( $tree );
    $category_first = $categories[0];
    $category_last = end( $categories );
    $category_num = sizeof( $categories );
    
    foreach ( $categories as $category ) {
        $items = $tree[$category];
        
        $info = Category::get()->info( $category );
        
        /* Determine which directions this category can move */
        $directions = '';
      if ( $category_num > 1 ) {
          if ( $category != $category_first ) {
              $directions .= 'L';
              $directions .= 'B';
          }
          if ( $category != $category_last ) {
              $directions .= 'R';
          }
      }
      /* Only sub level categories can move up */
      if ( $level != 1 ) {
          $directions .= 'T';
      }
      
      /* Determine the content of the cell */
      $moveUrl = "${url}?name=${category}";
      
      /* If there are more items below this one */
      $sub_count = 1;
      $sub_html = '';
      if ( sizeof( $items ) > 0 ) {
          $sub_count = 0;
          $sub_html = CategoryGUI::makeRow( $items, $url, $sub_count, $level + 1 );
          if ( $url !== false ) {
              $sub_html .= "<td>New: " . add( $category ) . "</td></tr>\n<tr>";
              $sub_count += 1;
          }
          $count += $sub_count;
      } else {
          $count += 1;
      }
      
      $html .= "<td valign=middle width=" . $cellWidth . " bgcolor=\"#$info[color]\" rowspan=${sub_count}>";
      $html .= cell( $category, $info, $directions, $moveUrl );
      $html .= "</td>";
      
      if ( $sub_html != '' ) {
          $html .= $sub_html;
      } else {
          $html .= "</tr>\n<tr>";
      }
    }
    
    return $html;
  }

makeRow($tree, $url)

?>

</table>
<?php if ( $edit !== false ) close_form(); ?>

?>
