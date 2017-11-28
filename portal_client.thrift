namespace	py VirtualMachineService


typedef i64 id
typedef i32 int





/**
 * This Struct defines a Flavor.
 */
 struct Flavor{

	1:required i32 vcpus,
	2:required i32 ram,
	3:required i32 disk,
	4:required string name
	5:required string openstack_id
	6:optional string description
	
	
}
/**
 * This Struct defines an Image.
 */
struct Image{
	1:required string name
	2:required i32 min_disk
	3:required i32 min_ram
	4:required string status
	5:optional string created_at
	6:optional string updated_at
	7:required string openstack_id
	8:optional string description
}
/**
 * This Struct defines a VirtualMachine.
 */
struct VM {
   
    
    1: required Flavor flav,
	2: required Image img,
	3: required string status
	4: optional map<string,string> metadata
	5: optional string project_id
	6: required string keyname
	7: required string openstack_id
	8: required string name
	9: required string created_at
	
}


/**
 * Exceptions inherit from language-specific base exceptions.
 */
exception nameException {
    /**@ Name already used. */
    1: string Reason
}

exception serverNotFoundException {
    /**@ Server not found. */
    1: string Reason
}

exception networkNotFoundException{
    /**@ Network not found. */
    1: string Reason
}

exception imageNotFoundException {
    /**@ Image not found. */
    1: string Reason
}

exception flavorNotFoundException {
    /**@ flavor not found. */
    1: string Reason
}

exception authenticationException {
    /**@ Authentication failed */
    1: string Reason
}

/**
 *
 * This VirtualMachiine service deploys methods for creating,deleting,stopping etc. VirtualMachines in Openstack.
 */
service VirtualMachineService {
    string import_keypair(1:string keyname,2:string public_key)
    /**@
     * This Method Creates a new keypair.
     */
	string create_keypair(1:string keyname)
	 /**@
     * This Method returns a list with all Flavors.
     */
	list<Flavor> get_Flavors()
	 /**@
     * This Method returns a list with all Images.
     */
	list<Image> get_Images()
	 /**@
     * This Method returns a list with all VirtualMachines.
     */
	list<VM> get_servers( )
	 /**@
     * This Method deletes a server.
     */
	bool delete_server(1:string servername) throws (1:serverNotFoundException e)
	 /**@
     * This Method adds Metadata to a Server
     */
	map<string,string> add_metadata_to_server(1:string servername,2:map<string,string> metadata) throws (1:serverNotFoundException e)
	 /**@
     * This Method deletey Metadata from a server.
     */
	set<string> delete_metadata_from_server(1:string servername,2:set<string> keys) throws (1:serverNotFoundException e)
	 /**@
     * This Method adds a floating IP to a Server.
     */
	string add_floating_ip_to_server(1:string servername,2:string network) throws (1:serverNotFoundException e, 2:networkNotFoundException f)
	 /**@
     * This Method creates a connection to the openstack API.
     */
	bool create_connection(1:string username,2:string password ,3:string auth_url,4:string project_name,5:string user_domain_name,6:string project_domain_name ) throws (1:authenticationException e),
	 /**@
     * This Method starts a VirtualMachine.
     */
    bool start_server(1:string flavor, 2:string image,3:string public_key,4:string servername,5:string username,6:string elixir_id) throws (1:nameException e),
	/**
	*This Method returns a Server with specific Openstack_ID
	*/
	VM get_server(1:string servername) throws (1:serverNotFoundException e),
	/**@
     * This Method stops a VirtualMachine.
     */
    bool stop_server(1:string servername) throws (1:serverNotFoundException e),
	/**@
     * This Method pause a VirtualMachine.
     */
    bool pause_server(1:string servername) throws (1:serverNotFoundException e),
						  /**@
     * This Method unpause a VirtualMachine.
     */
    bool unpause_server(1:string servername) throws (1:serverNotFoundException e),
}