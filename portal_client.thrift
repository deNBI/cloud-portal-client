namespace	py VirtualMachineService


typedef i64 id
typedef i32 int


const list<Flavor> FLAVOR_LIST = [
	{"vcpus":32,"ram":64,"disk":20,"name":'de.NBI.large'},
	{"vcpus":2,"ram":2,"disk":25,"name":'BiBiGrid Debug'},
	{"vcpus":2,"ram":2,"disk":40,"name":'unibi.mirco'},
	{"vcpus":8,"ram":16,"disk":70,"name":'unibi.small'},
	{"vcpus":16,"ram":32,"disk":120,"name":'unibi.medium'},
	{"vcpus":32,"ram":64,"disk":220,"name":'unibi.large'},
	{"vcpus":16,"ram":32,"disk":20,"name":'de.NBI.medium'},
	{"vcpus":2,"ram":2,"disk":20,"name":'de.NBI.default'},
	{"vcpus":8,"ram":16,"disk":20,"name":'de.NBI.small'},
	{"vcpus":4,"ram":8,"disk":70,"name":'unibi.tiny'},
	]
const list<string> IMAGES_LIST=[
		'Ubuntu 14.04 LTS (07/24/17)' ,
		'cirros',
		'BiBiGrid slave 14.04 (06/20/17)',
		'BiBiGrid master 14.04 (08/02/17)',
		'BiBiGrid slave 14.04 (08/01/17)',
		'Ubuntu 16.04 LTS (07/24/17)',	
		'BiBiGrid master 14.04 (06/20/17)']


enum serverStatus{
    ACTIVE = 1,
    BUilding = 2,
    DELETED = 3,
    ERROR = 4,
    HARD_REBOOT = 5,
    PASSWORD = 6,
    PAUSED = 7,
    REBOOT = 8,
    REBUILD = 9,
    RESCUED = 10,
    RESIZED = 11,
    REVERT_RESIZE = 12,
    SHUTOFF = 13,
    SOFT_DELETED = 14,
    STOPPED = 15,
    SUSPENDED = 16,
    UNKNOWN = 17,
    VERIFY_RESIZE = 18
}




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
	
}
struct VM {
    /** A unique identifier for this task. */
    
    1: required Flavor flav,
	2: required string img,
	3: required serverStatus status
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
	list<string> get_Images(1:string username,2:string password ,3:string auth_url,4:string project_name,5:string user_domain_name,6:string project_domain_name )
	list<VM> get_servers(1:string username,2:string password ,3:string auth_url,4:string project_name,5:string user_domain_name,6:string project_domain_name )
	bool delete_server(1:string username,2:string password ,3:string auth_url,4:string project_name,5:string user_domain_name,6:string project_domain_name ,7:string servername)
	
	string add_floating_ip_to_server(1:string username,2:string password ,3:string auth_url,4:string project_name,5:string user_domain_name,6:string project_domain_name ,7:string servername)
	bool create_connection(1:string username,2:string password ,3:string auth_url,4:string project_name,5:string user_domain_name,6:string project_domain_name ) throws (1:instanceException e), 
    bool start_server(1:string username,2:string password,3:string auth_url,4:string project_name,5:string user_domain_name,
                          6:string project_domain_name,7:string flavor, 8:string image, 9:string keyname,10:string servername,11:string network) throws (1:instanceException e),
    bool stop_server(1:string username,2:string password,3:string auth_url,4:string project_name,5:string user_domain_name,
                          6:string project_domain_name,7:string servername) throws (1:instanceException e),
    bool pause_server(1:string username,2:string password,3:string auth_url,4:string project_name,5:string user_domain_name,
                          6:string project_domain_name,8:string servername) throws (1:instanceException e),
    bool unpause_server(1:string username,2:string password,3:string auth_url,4:string project_name,5:string user_domain_name,
                          6:string project_domain_name,9:string servername) throws(1:instanceException e),
}