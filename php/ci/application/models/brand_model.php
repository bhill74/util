<?php

include_once( "finance.php" );
include_once( "city.php" );
include_once( "product.php" );

/************************************************************
 * Class Brand
 * 
 * This is the class used to query and manipulate information
 * corresonding to brands that are purchases. A brand is 
 * a company name, address, phone number and website.
 *  
 *
 *
 *
 *
 */
class Brand_model extends CI_Model {  
  /********************************************************** 
   * MySQL Table and Fields
   **********************************************************/
  
  /* The name of the brands table */
  public static $table = 'brands';

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
      $this->load->helper('finance_helper');

    $City = City::get();
    $city = $City->name();
    $fields = array( $City->field( 'address', 'The address of the brand' ),
		     $City->field( $city, 'The city of the brand' ),
		     $City->field( 'phone', 'The phone number of the brand' ),
		     $City->field( 'website', 'The website for the brand' ) );
    if ( !Finance::create( $fields ) ) {
      return false;
    }

    // Make sure this table contains UNIQUE brand entries.
    return $this->unique( 'unique', 
			  array( 'name', 
				 'address', $city ) );


    $this->dbforge->add_field(
        array( 'address', 


    $this->dbforge->create_table('brand');
    

  }
    
  /*****************************************
   *%FUNCTION: reset()
   *%DESCRIPTION:
   * Used to reset the brands table.
   *%ARGUMENTS:
   * None
   *%RETURNS:
   * The result of the reset query.
   */
  public function reset() {
    if ( !Finance::reset() ) {
      return false;
    }
    
    $City = City::get();
    $fields = array( $this->idField(), 'name', $City->name() );
    $values = array( $this->unknownId(), $this->unknownName(), $City->unknownId() );
    return $this->query( $this->insert( $this->table(), $fields, $values ) );
  }
  
  /********************************************************** 
   * MySQL Data Management
   * 
   * The following commands are used to manage and
   * maniuplate entries in the MySQL table(s).
   **********************************************************/ 
  
  /*****************************************
   *%FUNCTION: delete()
   *%DESCRIPTION:
   * Used to remove a brand from the list.
   *%ARGUMENTS:
   * product -- The name or ID of the brand to 
   * remove.
   *%RETURNS:
   * TRUE if the brand could be removed, FALSE
   * otherwise.
   */
  public function delete( $brand ) {
    if ( !$this->id( $brand ) ) {
      return false;
    }
    
    $this->db->where( 'id', $brand->id );
    $this->db->delete( 'brand' );
  } 
  
  /********************************************************** 
   * MySQL Data Queries
   * 
   * The following commands are used to extract information
   * from the table.
   **********************************************************/
  
  /*****************************************
   *%FUNCTION: brands()
   *%DESCRIPTION:
   * Used to retrieve all the brands from
   * the database. 
   *%ARGUMENTS:
   * None
   *%RETURNS:
   * The array of brand names.
   */
  public function brands() {
      return $this->db->get('brands');
  }
}

?>
