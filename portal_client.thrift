namespace	py VirtualMachineService


typedef i64 id
typedef i32 int





/**
 * structs are mapped by Thrift to classes or structs in your language of
 * choice. This struct has two fields, an Identifier of type `id` and
 * a Description of type `string`. The Identifier defaults to DEFAULT_ID.
 */
 struct Flavor{

	1:required i32 vcpus,
	2:required i32 ram,
	3:required i32 disk,
	4:required string name
	5:required string openstack_id
	
	
}
struct Image{
	1:required string name
	2:required i32 min_disk
	3:required i32 min_ram
	4:required string status
	5:optional string created_at
	6:optional string updated_at
	7:required string openstack_id
}
struct VM {
    /** A unique identifier for this task. */
    
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
 * A service defines the API that is exposed to clients.
 *
 * This TaskManager service has one available endpoint for creating a task.
 */
service VirtualMachineService {
    /**@
     * Create a new task.
     *
     * This method accepts a Task struct and returns an i64.
     * It may throw a TaskException.
     */
	string create_keypar(1:string username,2:string password ,3:string auth_url,4:string project_name,5:string user_domain_name,6:string project_domain_name ,7:string keyname)
	list<Flavor> get_Flavors(1:string username,2:string password ,3:string auth_url,4:string project_name,5:string user_domain_name,6:string project_domain_name )
	list<Image> get_Images(1:string username,2:string password ,3:string auth_url,4:string project_name,5:string user_domain_name,6:string project_domain_name )
	list<VM> get_servers(1:string username,2:string password ,3:string auth_url,4:string project_name,5:string user_domain_name,6:string project_domain_name )
	bool delete_server(1:string username,2:string password ,3:string auth_url,4:string project_name,5:string user_domain_name,6:string project_domain_name ,7:string servername)
	
	string add_floating_ip_to_server(1:string username,2:string password ,3:string auth_url,4:string project_name,5:string user_domain_name,6:string project_domain_name ,7:string servername,8:string network)
	bool create_connection(1:string username,2:string password ,3:string auth_url,4:string project_name,5:string user_domain_name,6:string project_domain_name ) throws (1:instanceException e), 
    bool start_server(1:string username,2:string password,3:string auth_url,4:string project_name,5:string user_domain_name,
                          6:string project_domain_name,7:Flavor flavor, 8:Image image, 9:string keyname,10:string servername,11:string network) throws (1:instanceException e),
    bool stop_server(1:string username,2:string password,3:string auth_url,4:string project_name,5:string user_domain_name,
                          6:string project_domain_name,7:string servername) throws (1:instanceException e),
    bool pause_server(1:string username,2:string password,3:string auth_url,4:string project_name,5:string user_domain_name,
                          6:string project_domain_name,8:string servername) throws (1:instanceException e),
    bool unpause_server(1:string username,2:string password,3:string auth_url,4:string project_name,5:string user_domain_name,
                          6:string project_domain_name,9:string servername) throws(1:instanceException e),
}