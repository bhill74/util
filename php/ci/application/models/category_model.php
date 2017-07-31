<?php

/************************************************************
 * Class Category_model
 * 
 * This is the class used to query and manipulate information
 * corresonding to categories of products. A cateogory is
 * defined by a name but is also stored within a tree structure
 * to identify relationships between other categories (parents
 * and children).
 *
 * This class manages the category information and the 
 * relationships between them.
 */
class Category_model extends CI_Model {  
    /* The name of the top category */
    public static $top = '_top';

    /********************************************************** 
     * MySQL Table and Fields
     **********************************************************/
    
    /* The name of the categories table */
    public static $table = 'categories';
    
    /**********************************************************
     *%FUNCTION: create()
     *%DESCRIPTION:
     * Used to create the MySQL table with the desired fields.
     * The existing table is DROPed and the new one is created
     * with the ID field given the attributes of PRIMARY and 
     * UNIQUE.
     *%ARGUMENTS: 
     * None.
     *%RETURNS: 
     * TRUE if the table was created and FALSE otherwise.
     */
    public function create() {
        $fields = array( $this->define_field( 'color', 'VARCHAR(6)', 'The colour that should be used to represent this field' ),
                         $this->define_field( 'nickname', 'VARCHAR(50)', 'The short/legible name of the category' ),
                         $this->define_field( 'left',  'INT(5)', 'The index of all items before this item' ),
                         $this->define_field( 'right', 'INT(5)', 'The index of all items after this item' ),
                         $this->define_field( 'depth', 'INT(11)', 'The level of this particular item' ),
                         $this->define_field( 'move',  'INT(1)',  'The flag indicating this item is to be moved' ) );
        return Finance::create( $fields );
    }
    
    /*****************************************
     *%FUNCTION: reset()
     *%DESCRIPTION:
     * Used to reset the category table.
     *%ARGUMENTS:
     * None
     *%RETURNS:
     * The result of the reset query.
     */
    public function reset() {        
        $table = user_table( Category_model::$table );
        $top = Category_model::$top;
        
        $query = $this->insert( $table,
                                array( $this->idField(), 'name', 'left', 'right', 'depth' ),
                                array( 1, $top, 0, 1, 1 ) );
        if ( !$this->query( $query ) ) {
            return true;
        }
        
        return $this->add( $this->unknownName(), $top );
    }
    
    public function basic() {
        // Groceries costs
        $this->add( 'Groceries' );
        // Dairy
        $this->add( 'Dairy', 'Groceries' );
        $this->add( 'Cheese', 'Dairy' );
        $this->add( 'Cheddar', 'Cheese' );
        $this->add( 'Old Cheddar', 'Cheddar' );
        $this->add( 'Medium Cheddar', 'Cheddar' );
        $this->add( 'Mild Cheddar', 'Cheddar' );
        $this->add( 'Mozarella', 'Cheese' );
        $this->add( 'Skim', 'Mozarella' );
        $this->add( 'Regular', 'Mozarella' );
        $this->add( 'Swiss', 'Cheese' );
        $this->add( 'Milk', 'Dairy' );
        $this->add( 'Skim', 'Milk' );
        $this->add( '1%', 'Milk' );
        $this->add( '2%', 'Milk' );
        $this->add( 'Homo', 'Milk' );
        $this->add( 'Coconut', 'Milk' );
        $this->add( 'Yogurt', 'Dairy' );
        $this->add( 'Plain', 'Yogurt' );
        $this->add( 'Flavoured', 'Yogurt' );
        // Goat
        $this->add( 'Goat', 'Groceries' );    
        // Sheep
        $this->add( 'Sheep', 'Groceries' );
        // Meat
        $this->add( 'Meat', 'Groceries' );
        $this->add( 'Beef', 'Meat' );
        $this->add( 'Ground Beef', 'Beef' );
        $this->add( 'Flank Beef Steak', 'Beef' );
        $this->add( 'Sirloin Beef Steak', 'Beef' );
        $this->add( 'Stewing Beef', 'Beef' );
        $this->add( 'Pork', 'Meat' );
        $this->add( 'Ground Pork', 'Pork' );
        $this->add( 'Pork Chops', 'Pork' );
        $this->add( 'Strip Bacon', 'Pork' );
        $this->add( 'Back Bacon', 'Pork' );
        $this->add( 'Lamb', 'Meat' );
        $this->add( 'Chicken', 'Meat' );
        // Grains
        $this->add( 'Grains', 'Groceries' );
        // Produce
        $this->add( 'Produce', 'Groceries' );
        $this->add( 'Vegetables', 'Produce' );
        $this->add( 'Fruit', 'Produce' );
        $this->add( 'Apples', 'Fruit' );
        $this->add( 'Bananas', 'Fruit' );
        $this->add( 'Strawberries', 'Fruit' );
        $this->add( 'Peaches', 'Fruit' );
        $this->add( 'Tomatoes', 'Fruit' );
        $this->add( 'Blackberries', 'Fruit' );
        // Prepared
        $this->add( 'Prepared', 'Groceries' );
        $this->add( 'Dessert', 'Prepared' );
        $this->add( 'Chocolate', 'Dessert' );
        $this->add( 'Bar', 'Chocolate' );
        
        // Home costs.
        $this->add( 'Home' );   
        
        // Restaurant costs.
        $this->add( 'Restaurant' );
        
        // Service costs.
        $this->add( 'Services' );
    }
    
    /********************************************************** 
     * MySQL Data Management
     * 
     * The following commands are used to manage and
     * maniuplate entries in the MySQL table(s).
     **********************************************************/
    public function info($category) 
    {
        $table = userTable(Category_model::$table);
        $this->db->select( '*' );
        $this->db->from( $table );
        $this->db->where( where( $category, 'category' ) );
        $query = $this->db->get();
        if ($query->num_rows() != 1) {
            warn( "Too many records in Category_model::info()\n" );
        }      
        foreach ($query->records() as $row) {
            return $row;
        }
        return false;
    }  
    
    /*****************************************
     *%FUNCTION: delete()
     *%DESCRIPTION:
     * Used to remove a branch from the tree.
     *%ARGUMENTS:
     * category -- The name of the cateogory to 
     * remove.
     *%RETURNS:
     * The information about the given category
   * OR false if none could be found. 
   */
    public function delete( $category ) {
        $info = $this->info($category);
        if ($info === false) {
            return;
        }
        $table = userTable(Category_model::$table);
        // Remove the given category.
        $this->db->where( "left BETWEEN $info[left] and $info[right]" );
        $this->db->delete( $table );
        // Adjust the index values for 'left'.
        $delta = "ROUND(($info[right]- $info[left] + 1))";
        $this->db->where( 'left', "left - ${delta}" );
        $this->db->update( $table, "left > $info[right]" );
        // Adjust the index values for 'right'.
        $this->db->where( 'right', "right - ${delta}" );
        $this->db->update( $table, "right > $info[right]" );
    } 
    
    /********************************************************** 
     * MySQL Category Tree Management
     * 
     * The following commands are used to manage and
     * maniuplate the tree (Net Set Graph) relationships.
     **********************************************************/
    
    /*****************************************
     *%FUNCTION: byValue()
     *%DESCRIPTION:
     * Used to retrieve the name and ID of the
     * category that has a match for a particular
     * field and value.
     *%ARGUMENTS:
     * field -- The field name
     * value -- The value to match for.
     * search for.
     * [fields] -- The fields to retrieve, '*' is
     *%RETURNS:
     * The corresponding category name or FALSE if the 
     * search was unsuccessful.
     */
    public function byValue( $field, $value ) {
        $table = userTable(Category_model::$table);
        $query = $this->db->get_where( $field, $value );
        $row = $query->row();
        return $row['name'];
    }
    
    /*****************************************
     *%FUNCTION: add()
     *%DESCRIPTION:
     * Used to add a new cateogory to the table and create
     * a relationship between it and the parent.
     *%ARGUMENTS:
     * category -- The name of the cateogory to add.
     * parent -- The name of the existing parent, if none 
     * provided then the top place will be used.
     *%RETURNS:
     * Nothing
     */
    public function add( $category, $parent = '' ) {
        $table = user_table(Category_model::$table);
        if ( $parent == '' ) {
            $parent = Category_model::$top;
        }
        
        $pinfo = $this->info( $parent );
        if ( $pinfo === false ) {
            $this->add( $parent );
            $this->add( $category, $parent );
            return;
        }
        
        // Increase the 'right' index.
        $this->db->where( "right >= $pinfo[right]" );
        $this->db->update( $table, array( 'right' => 'right + 2' ) );
        // Increase the 'left' index.
        $this->db->where( "left >= $pinfo[left]" );
        $this->db->update( $table, array( 'left' => 'left + 2' ) );
        // Insert the new category.
        $this->insert( $table, array( 'name' => $category,
                                      'color' => randomString(6),
                                      'left' => $pinfo['right'],
                                      'right' => $pinfo['right'] + 1,
                                      'depth' => $pinfo['depth'] + 1 ) );
    }
    
    /*****************************************
     *%FUNCTION: color()
     *%DESCRIPTION:
     * Used to set or retrive the color used for
     * the given category.
     *%ARGUMENTS:
     * category -- The name of the cateogory.
     * [color] -- The color code to use.
     *%RETURNS:
     * The colour associated with this category.
     */
    public function color( $category, $color = '' ) {
        $table = userTable(Category_model::$table);
        if ( $color != '' ) {
            $this->db->where( 'name', $category );
            $query = $this->db->update( $table, array( 'color' => $color ) );
            if ( $query->num_rows() === 0 ) {
                return $this->color( $category );
            }
        } else {
            $this->db->select( 'color' );
            $this->db->where( 'name', $category );
            $query = $this->db->get( $table );
            if ( $query->num_rows() > 0 ) {
                $row = $query->row();
                $color = $row['color'];
            }
        }
        return $color;
    }
    
    /*****************************************
     *%FUNCTION: nickname()
     *%DESCRIPTION:
     * Used to set or retrive the nickname used for
     * the given category.
     *%ARGUMENTS:
     * category -- The name of the cateogory.
     * [color] -- The color code to use.
     *%RETURNS:
     * The nickname associated with this category.
     */
    public function nickname( $category, $nickname = '' ) {
        $table = userTable(Category_model::$table);
        if ( $nickname != '' ) {
            $this->db->where( 'name', $category );
            $query = $this->db->update( $table, array( 'nickname' => $nickname ) );
            if ( $query->num_rows() == 0 ) {
                return $this->nickname( $category );
            }
        } else {
            $this->db->select( 'nickname' );
            $this->db->where( 'name', $category );
            $query = $this->db->get( $table );
            if ( $query->num_rows() > 0 ) {
                $row = $query->row();
                $nickname = $row['nickname'];
            }
        }
        return $nickname;
    }
    
    /*****************************************
     *%FUNCTION: moveLeft()
     *%DESCRIPTION:
     * Used to shift a branch LEFT within the tree.
     *%ARGUMENTS:
     * category -- The name of the cateogory to 
     * shift.
     *%RETURNS:
     * TRUE if the shift was successful, FALSE
     * otherwise.
     */
    public function moveLeft( $category ) {
        $table = userTable(Category_model::$table);
        $start = $this->info( $category );
        
        $other_category = $this->byValue( 'right', $start['left'] - 1 );
        if ( $other_category === false || $other_category == '' ) {
            return false;
        }
        
        $stop = $this->info( $other_category ); 
        if ( $stop['depth'] != $start['depth'] ) {
            return false;
        }
        
        $diff = array( 'left' => $start['left'] - $stop['left'], 
                       'right' => $start['right'] - $stop['right'] );
        
        // Reset the 'move' flag.
        $this->db->where( 'move <> 0' );
        $this->db->update( $table, array( 'move' => 0 ) );
        // Update the 'right' index.
        $this->db->where( "left BETWEEN $stop[left] AND $stop[right]" );
        $this->db->update( $table, array( 'right' => "right + $diff[right]",
                                          'left' => "left + $diff[right]",
                                          'move' => 1 ) );
        // Update the 'left' index.
        $this->db->where( "left BETWEEN $start[left] AND $start[right]" );
        $this->db->where( 'move', 0 );
        $this->db->update( $table, array( 'right' => "right - $diff[left]",
                                          'left' => "left - $diff[left]" ) );
        // Reset the 'move' flag.
        $this->db->where( 'move <> 0' );
        $this->db->update( $table, array( 'move' => 0 ) );
        return true; 
    }
    
    /*****************************************
     *%FUNCTION: moveRight()
     *%DESCRIPTION:
     * Used to shift a branch RIGHT within the tree.
     *%ARGUMENTS:
     * category -- The name of the cateogory to 
     * shift.
     *%RETURNS:
     * TRUE if the shift was successful, FALSE
     * otherwise.
     */
    public function moveRight( $category ) {
        $table = userTable(Category_model::$table);
        $start = $this->info( $category );
        
        $other_category = $this->byValue( 'left', $start['right'] + 1 );
        if ( $other_category === false || $other_category == '' ) {
            return false;
        }
        
        $stop = $this->info( $other_category ); 
        if ( $stop['depth'] != $start['depth'] ) {
            return false;
        }
        
        $diff = array( 'left' => $stop['left'] - $start['left'], 
                       'right' => $stop['right'] - $start['right'] );
        
        // Reset the 'move' flag.
        $this->db->where( 'move <> 0' );
        $this->db->update( $table, array( 'move' => 0 ) );
        // Shift 'right'/'left' DOWN for everything to right.
        $this->db->where( "left BETWEEEN $stop[left] AND $stop[right]" );
        $this->db->update( $table, array( 'right' => "right - $diff[left]",
                                          'left', "left - $diff[left]",
                                          'move' => 1 ) );
        // Shfit 'right'/'left' UP for category.
        $this->db->where( "left BETWEEN $start[left] AND $stop[right]" );
        $this->db->where( 'move', 0 );
        $this->db->update( $table, array( 'right' => "right + $diff[right]",
                                          'left', "left + $diff[right]" ) );
        // Reset the move flag.
        $this->db->where( 'move <> 0' );
        $this->db->update( $table, array( 'move' => 0 ) );
        
        return true; 
    }
    
    /*****************************************
     *%FUNCTION: moveUp()
     *%DESCRIPTION:
     * Used to shift a branch UP within the tree.
     *%ARGUMENTS:
     * category -- The name of the cateogory to 
     * shift.
     *%RETURNS:
     * Nothing.
     */
    public function moveUp( $category ) {
        $table = userTable(Category_model::$table);
        
        /* Move RIGHT as much as possible */
        do {
            if ( !$moved = $this->moveRight( $category ) ) {
                break;
            }
        } while ( true === $moved );
        
        $start = $this->info( $category );
        
        /* Move UP */
        $other_category = $this->byValue( 'right', $start['right'] + 1 );
        if ( $other_category === false || $other_category == '' ) {
            return;
        }
        
        $stop = $this->info( $other_category ); 
        $width = $start['right'] - $start['left'] + 1;
        
        // Move the category up.
        $this->db->where( "left BETWEEN $start[left] AND $start[right]" );
        $this->db->update( $table, array( 'right' => 'right + 1',
                                                    'left' => 'left + 1',
                                                    'depth' => 'depth - 1' ) );
        // Move the other categories over.
        $this->db->where( 'category_id', $start[category_id] );
        $this->db->update( $table, array( 'right' => "right - ${width}" ) );
        
        return true; 
    }
    
    /*****************************************
     *%FUNCTION: moveDown()
     *%DESCRIPTION:
     * Used to shift a branch DOWN within the tree.
     *%ARGUMENTS:
     * category -- The name of the cateogory to 
     * shift.
     *%RETURNS:
     * TRUE if the shift was successful, FALSE
     * otherwise.
     */
    public function moveDown( $category ) {
        $table = userTable(Category_model::$table);
        $start = $this->info( $category );
        
        /* Move DOWN */
        $other_category = $this->byValue( 'right', $start['left'] - 1 );
        if ( $other_category === false || $other_category == '' ) {
            return;
        }
        
        $stop = $this->info( $other_category ); 
        $width = $start['right'] - $start['left'] + 1;
        
        // Move the category down.
        $this->db->where( "left BETWEEN $start[left] AND $start[right]" );
        $this->db->update( $table, array( 'right' => 'right - 1',
                                          'left' => 'left - 1',
                                          'depth' => 'depth - 1' ) );
        // Update the right.
        $this->db->where( 'category_id', $stop['category_id'] );
        $this->db->update( $table, array( 'right' => "right + ${width}" ) );
        
        return true; 
  }
    
    /*****************************************
     *%FUNCTION: move()
     *%DESCRIPTION:
     * Used to shift a branch within the tree.
     *%ARGUMENTS:
     * direction -- The direction to move the
     * category.
     * category -- The name of the cateogory to 
     * shift.
     *%RETURNS:
     * TRUE if the move was successful, FALSE otherwise.
     */
    public function move( $direction, $category, $parent = '' ) {
        $parent = ( $parent == '' ) ? Category_model::$top : $parent;
        
        switch ( $direction ) {
        case "up":
            return $this->moveUp( $category );
            break;
        case "down":
            return $this->moveDown( $category );
            break;
        case "left":
            return $this->moveLeft( $category );
            break;
        case "right":
            return $this->moveRight( $category );
            break;
        case "over":
            break;
        default:
            break;
        }
        
        return false;
    } 
    
    /*****************************************
     *%FUNCTION: process()
     *%DESCRIPTION:
     * Used to process a cateogory based on the
     * arguments provided to the script.
     *%ARGUMENTS:
     * settings -- The collection of arguments
     * provided to the page.
     *%RETURNS:
     * Nothing.
     */
    public function process( &$settings ) {
        Finance::processKeys( $settings );
        $settings['parent'] = '';
        $settings['direction'] = '';
        $settings = Arguments::process( $settings );
        
        foreach ( array_keys( $settings ) as $key ) {
            $category = $key;
            $extra = array();
            Finance::fromFieldName( $category, $extra );
            if ( sizeof( $extra ) == 0 ) {
                continue;
            }
            
            if ( $extra[0] == 'names' ) {
                $names = explode( ',', $settings[$key] );
                foreach( $names as $name ) {
                    $name = trim( $name );
                    if ( $name != '' ) {
                        $this->add( $name, $category );
                    }
                }
            } else if ( $extra[0] == 'color' ) {
                if ( $settings[$key] != $this->color( $category ) ) {
                    $this->color( $category, $settings[$key] );
                }
            } else if ( $extra[0] == 'nickname' ) {
                if ( $settings[$key] != $this->nickname( $category ) ) {
                    $this->nickname( $category, $settings[$key] );
                }
            }
        }
        
        if ( !isset( $settings['name'] ) || $settings['name'] == '' ) {
            return;
        }
        
        if ( isset( $settings['direction'] ) && $settings['direction'] != '' ) {
            $this->move( $settings['direction'], $settings['name'] );
        } else if ( isset( $settings['parent'] ) && $settings['parent'] != '' ) {
            $this->add( $settings['name'], $settings['parent'] );
        } else if ( isset( $settings['delete'] ) && $settings['delete'] === true ) {
            $this->delete( $settings['name'] );
        }
    }
    
    /**********************************************************
     *%FUNCTION: filter()
     *%DESCRIPTION: 
     * Used to filter the results that correspond to the 
     * given input using string matching.
     *%ARGUMENTS: 
     * input -- The input string to compare with.
     * values -- The set of values to compare against.
     * settings -- Additional settings to be passed in.
     *%RETURNS: 
     * The set of values that correspond to the given input.
     */
    public function filter( $input, &$categories = false, &$settings = array() ) {
        $results = array();  
        
        $inputs = preg_split( '|[\s]+|', trim( $input ) );
        foreach ( $inputs as $input ) {
            if ( Category_model::isParentPattern( $input, $category ) ) {
                $results = array_merge( $results, 
                                        $this->categoriesDOWN( $category, false, true ) );
            } else if ( Category_model::isChildPattern( $input, $category ) ) {
                $results = array_merge( $results, 
                                        $this->categoriesUp( $category, false, true ) );
            } else {	
                $results = array_merge( $results, 
                                        $this->categoriesMATCH( $input, $categories, true ) );
            }
        }
        
        return $results;
    }
    
    public function categoriesDOWN( $category, $include = false, $useId = true ) {
        $results = array();
        $children = $this->children( $category, 'all' );
        $useKey = false;
        foreach( $this->filterOrder( $children, $useId, $useKey ) as $key ) {
            $name = ( $useKey ) ? $children[$key] : $key;
            $item = array( 'label' => $name,
                           'type' => 'children',		   
                           'path' => $this->path( $name, $category ) );
            if ( $useId ) {
                $item['id'] = $key;
            }
            array_push( $results, $item );
        }
        return $results;
    }
    
    public function categoriesUP( $category, $include = false, $useId = true ) {
        $results = array();
        $parents = $this->parents( $category );     
        $useKey = false;
        foreach ( $this->filterOrder( $parents, $useId, $useKey ) as $key ) {
            $name = ( $useKey ) ? $parents[$key] : $key;
            $item = array( 'label' => $name,
                           'type' => 'parent',	     
                           'path' => $this->path( $name, false ) );
            if ( $useId ) {
                $item['id'] = $key;
            }
            array_push( $results, $item );
        }
        return $results;
    } 
    
    public function categoriesMATCH( $input, &$categories = false, $useId = true ) {
        $extra = ( array( 'path' => array( $this, "pathItem" ) ) );
        $categories = ( $categories === false ) ? $this->categories() : $categories;
        return Finance::filterMatchValues( $input, $categories, $useId, $extra );
    }
    
    public function pathItem( $item ) {
        return $this->path( $item['label'], $item['label'] );
    }
    
    private function path( $category, $highlight = false, &$parents = false ) {
        $parents = ( is_array( $parents ) ) ? $parents : $this->parents( $category );
        if ( sizeof( $parents ) == 0 ) {
            return "the top";
        }    
        
        $result = '';
        foreach ( $parents as $parent ) {
            $name = ( is_array( $parent ) ) ? $parent['name'] : $parent;
            if ( is_string( $highlight ) && $highlight == $name ) {
                $name = Finance::highlight( $name );
            }	
            if ( $result != '' ) {
                $result = '->' . $result;
            }
            $result = $name . $result;
        }
        
        return $result;
    } 
    
    public function isParentPattern( $input, &$category ) {
        if ( preg_match( '|^(.*)/$|', $input, $match ) ) {
            $category = $match[1];
            return true;
        }
        return false;
    }
    
    public function isChildPattern( $input, &$category ) {
        if ( preg_match( '|^/(.*)$|', $input, $match ) ) {
            $category = $match[1];
            return true;
        }
        return false;
    }
    
    public function derive( $field, &$settings = array() ) {
        switch ($field) {
        case 'category_name':
            $sql = sprintf( 'IF( %1$s IS NOT NULL, %1$s, %2$s )',
                            $this->derive( 'name', $settings ),
                            Category_model::unknownName() );
            break;
        default:
            $sql = Finance::derive( $field, $settings );
            break;
        }
        return $sql;
    }
    
    /*****************************************
     *%FUNCTION: parents()
     *%DESCRIPTION:
     * Used to retrieve the full list of parent
     * category names ordered by closest to farthest.
     *%ARGUMENTS:
     * category -- The name of the cateogory to search
     * for parents.
     * [ids] -- Whether (true) or not (false) to include
     * the ID values. By default is false.
     *%RETURNS:
     * The array of collected parents.
     */
    public function parents( $category ) {
        return $this->up( $category, false );
    }
    
    public function up( $category, $include = false ) {
        $table = userTable(Category_model::$table);
    
        $this->db->select( 'parent.name AS name' );
        $this->db->select( 'parent.category_id AS id' );
        $this->db->from( "${table} as child, ${table} as parent" );
        $this->db->where( 'child.depth > parent.depth' );
        $equal = ( $include ) ? '=' : '';
        $this->db->where( "parent.left <${equal} child.left" );
        $this->db->where( "parent.right >${equal} child.right" );
        if ($category != Category_model::$top) {
            $this->db->where( "child.name = '${category}'" );
        }
        $this->db->order_by( 'parent.left DESC' );
        $query = $this->db->get();
        
        $parents = array();
        foreach ($query->result() as $row) {
            $parents[$row['id']] = $row['name'];
        }
        return $parents;
    }
    
    /*****************************************
     *%FUNCTION: children()
     *%DESCRIPTION:
     * Used to retrieve the full list of children
     * category names ordered by closest to farthest.
     *%ARGUMENTS:
     * category -- The name of the cateogory to search
     * for parents.
     * [levels] -- The number of levels to search for,
     * by default 1 is used. 'all' can be used to search
     * without limits.
     * [ids] -- Whether (true) or not (false) to include
     * the ID values. By default is false.
     *%RETURNS:
     * The array of collected children.
     */
    public function children( $category, $levels = 1 ) {
        return $this->down( $category, $levels, false );
    }
    
    public function down( $category, $levels = 1, $include = false ) {
        $table = userTable(Category_model::$table);
        
        $this->db->select( 'child.name AS name' );
        $this->db->select( 'child.category_id AS id' );
        $this->db->from( "${table} as child, ${table} as parent" );
        if ( $levels == 'all' ) {
            $this->db->where( 'child.depth > parent.depth' );
        } else {
            $this->db->where( "( child.depth - parent.depth ) BETWEEN 0 and ${levels}" );
        }
        $equal = ( $include ) ? '=' : '';
        $this->db->where( "child.left >${equal} parent.left" );
        $this->db->where( "child.right <${equal} parent.right" );
        if ($category != Category_model::$top) {
            $this->db->where( "parent.name = '${category}'" );
        }
        $this->db->order_by( "child.left ASC" );
        $query = $this->db->get();
        
        $children = array();
        foreach ($query->result() as $row) {
            $children[$row->id] = $row->name;
        }
        
        return $children;
    }
  
    /*****************************************
     *%FUNCTION: tree()
     *%DESCRIPTION:
     * Used to retrieve the full hierarchy based
     * on the given reference point.
     *%ARGUMENTS:
     * [category] -- The name of the cateogory to start
     * with.
     *%RETURNS:
     * The array representing the hierarchy.
     */
    public function tree( $category = '' ) {
        if ( $category == '' ) {
            $category = Category_model::$top;
        }
        $result = array();
        foreach ( $this->children( $category, 1 ) as $child ) {
            $sub_result = $this->tree( $child );
            $result[$child] = $sub_result;
        }
        return $result;
    }
    
    public function all() 
    {
        $table = userTable(Category_model::$table);
        $query = $this->db->get($table);
        $all = array();
        foreach ($query->result() as $row) {
            $all[$row->category_id] = $row;
        }
        return $all;
    }
    
    /**********************************************************
     *%FUNCTION: nameAndId()
     *%DESCRIPTION: 
     * Used to produce the query that will return a listing
     * of 'id' and 'name' values.
     *%ARGUMENTS: 
     * settings -- The settings to alter the way the table is
     * constructed.
     *%RETURNS: 
     * The resulting SQL code for a query.
     */
    public function nameAndId( $fields = '*', &$settings = array() ) {
        $nickname = ( isset( $settings['nickname'] ) && $settings['nickname'] === true );  
        
        $table = $this->table();    
        
        $columns = $this->columns( false, $fields );
        $columns['id'] = $this->idField();
        $columns['name'] = ( $nickname ) ? $this->derive( 'display_name' ) : true;
        
        $sql = "SELECT ";
        $sql .= $this->selectColumns( $columns );
        $sql .= " FROM " . $this->quoteTable( $table );
        return $sql;
    }
    
    /**********************************************************
     *%FUNCTION: variants()
     *%DESCRIPTION: 
     * Used to produce the query that will return a full set of
     * 'id' and 'name' values including all variants.
     *%ARGUMENTS: 
     * None.
     *%RETURNS: 
     * The resulting SQL code for a query.
     */
    public function variants( $fields = '*' ) {
        $tables = array( 'basic' => $this->nameAndId( $fields ) );
        $options = array( 'nickname' => true );
        $tables['nickname'] = $this->nameAndId( $fields, $options );
        return Finance::variantMerge( $tables );
    } 
    
    public function listing( &$settings = array(), $name = 'listing' ) {
        $fields = array( 'id', 'name' );
        $tables = array( 'basic' => $this->nameAndId( $fields ) );
        $options = array( 'nickname' => true );
        $tables['brand'] = $this->nameAndId( $fields, $options );
        return Finance::variants( $tables ); 
    }
    
    /*****************************************
     *%FUNCTION: categories()
     *%DESCRIPTION:
     * Used to retrieve all the category names from 
     * the database, using the most specific first.
     *%ARGUMENTS:
     * None
     *%RETURNS:
     * THe array of category names.
     */
    public function categories() {
        return $this->namesById();
    }
    
    public function labelByCategory( $table, $level = 2, &$columns = array() ) {     
        if ( $level <= 1 ) {
            $columns['category'] = "'All'";
        } else {
            $categories = $this->table();
            $name = $this->name();
            
            /* Get the Nth level categories */
            $query = "SELECT `right`, `name` FROM ${categories} WHERE `depth` = ${level} ORDER BY `left` DESC";
            $result = $this->query( $query );
            if ( $result === false ) {
                return;
            }
            
            $category_names = $this->toValue( Category_model::get()->unknownName() );
            while( $row = mysql_fetch_assoc( $result ) ) {
                $category_names = "IF( ${name}.right < $row[right], '$row[name]', ${category_names} )"; 
            }
            
            $columns['category'] = $category_names;
        }    
        
        return $this->mergeWith( $this, $columns, $table );
    }
    
    public function filterByCategory( $table, $category, $exact = false, &$columns = array() ) {
        if ( !$this->id( $category, false ) ) {
            return $table;
        }
        
        $category = $this->info( $category );
        
        $name = $this->name();
        
        $columns['left'] = $this->prefixName( 'left', $name );
        $columns['right'] = $this->prefixName( 'right', $name );
        $columns['category'] = $this->prefixName( 'category', $name );
        
        $sql = $this->mergeWith( $this, $columns, $table );
        if ( $exact === true ) {
            $sql .= " AND ${name}.`name` = '$category[name]'";
        } else {
            $sql .= " AND ${name}.`left` >= $category[left]";
            $sql .= " AND ${name}.`right` <= $category[right]";    
        }
        
        return $sql;
    }
}
