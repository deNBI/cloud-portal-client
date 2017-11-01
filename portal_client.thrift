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
	
}


/**
 * Exceptions inherit from language-specific base exceptions.
 */
exception instanceException {
    /**@ The reason for this exception. */
    1: string Reason
}

/**
 *
 * This VirtualMachiine service deploys methods for creating,deleting,stopping etc. VirtualMachines in Openstack.
 */
service VirtualMachineService {
    /**@
     * This Method Creates a new keypair.
     */
	string create_keypar(1:string username,2:string password ,3:string auth_url,4:string project_name,5:string user_domain_name,6:string project_domain_name ,7:string keyname)
	 /**@
     * This Method returns a list with all Flavors.
     */
	list<Flavor> get_Flavors(1:string username,2:string password ,3:string auth_url,4:string project_name,5:string user_domain_name,6:string project_domain_name )
	 /**@
     * This Method returns a list with all Images.
     */
	list<Image> get_Images(1:string username,2:string password ,3:string auth_url,4:string project_name,5:string user_domain_name,6:string project_domain_name )
	 /**@
     * This Method returns a list with all VirtualMachines.
     */
	list<VM> get_servers(1:string username,2:string password ,3:string auth_url,4:string project_name,5:string user_domain_name,6:string project_domain_name )
	 /**@
     * This Method deletes a server.
     */
	bool delete_server(1:string username,2:string password ,3:string auth_url,4:string project_name,5:string user_domain_name,6:string project_domain_name ,7:string servername)
	 /**@
     * This Method adds Metadata to a Server
     */
	map<string,string> add_metadata_to_server(1:string username,2:string password ,3:string auth_url,4:string project_name,5:string user_domain_name,6:string project_domain_name ,7:string servername,8:map<string,string> metadata)
	 /**@
     * This Method deletey Metadata from a server.
     */
	set<string> delete_metadata_from_server(1:string username,2:string password ,3:string auth_url,4:string project_name,5:string user_domain_name,6:string project_domain_name ,7:string servername,8:set<string> keys)
	 /**@
     * This Method adds a floating IP to a Server.
     */
	string add_floating_ip_to_server(1:string username,2:string password ,3:string auth_url,4:string project_name,5:string user_domain_name,6:string project_domain_name ,7:string servername,8:string network)
	 /**@
     * This Method creates a connection to the openstack API.
     */
	bool create_connection(1:string username,2:string password ,3:string auth_url,4:string project_name,5:string user_domain_name,6:string project_domain_name ) throws (1:instanceException e), 
	 /**@
     * This Method starts a VirtualMachine.
     */
    bool start_server(1:string username,2:string password,3:string auth_url,4:string project_name,5:string user_domain_name,
                          6:string project_domain_name,7:Flavor flavor, 8:Image image, 9:string keyname,10:string servername,11:string network) throws (1:instanceException e),
	/**@
     * This Method stops a VirtualMachine.
     */
    bool stop_server(1:string username,2:string password,3:string auth_url,4:string project_name,5:string user_domain_name,
                          6:string project_domain_name,7:string servername) throws (1:instanceException e),
	/**@
     * This Method pause a VirtualMachine.
     */
    bool pause_server(1:string username,2:string password,3:string auth_url,4:string project_name,5:string user_domain_name,
                          6:string project_domain_name,8:string servername) throws (1:instanceException e),
						  /**@
     * This Method unpause a VirtualMachine.
     */
    bool unpause_server(1:string username,2:string password,3:string auth_url,4:string project_name,5:string user_domain_name,
                          6:string project_domain_name,9:string servername) throws(1:instanceException e),
}