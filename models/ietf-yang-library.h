/* Container holding the entire YANG library of this server. */
#define YANGLIB_YANG_LIBRARY_PATH "/yanglib:yang-library"
/* A set of modules that may be used by one or more schemas.  A module set does not have to be referentially complete, i.e., it may define modules that contain import statements for other modules not included in the module set. */
#define YANGLIB_YANG_LIBRARY_MODULE_SET_PATH "/yanglib:yang-library/module-set"
/* An arbitrary name of the module set. */
#define YANGLIB_YANG_LIBRARY_MODULE_SET_NAME "name"
/* An entry in this list represents a module implemented by the server, as per Section 5.6.5 of RFC 7950, with a particular set of supported features and deviations. */
#define YANGLIB_YANG_LIBRARY_MODULE_SET_MODULE_PATH "module"
/* The YANG module or submodule name. */
#define YANGLIB_YANG_LIBRARY_MODULE_SET_MODULE_NAME "name"
/* The YANG module or submodule revision date.  If no revision statement is present in the YANG module or submodule, this leaf is not instantiated. */
#define YANGLIB_YANG_LIBRARY_MODULE_SET_MODULE_REVISION "revision"
/* The XML namespace identifier for this module. */
#define YANGLIB_YANG_LIBRARY_MODULE_SET_MODULE_NAMESPACE "namespace"
/* Contains a URL that represents the YANG schema resource for this module or submodule.  This leaf will only be present if there is a URL available for retrieval of the schema for this entry. */
#define YANGLIB_YANG_LIBRARY_MODULE_SET_MODULE_LOCATION "location"
/* Each entry represents one submodule within the parent module. */
#define YANGLIB_YANG_LIBRARY_MODULE_SET_MODULE_SUBMODULE_PATH "submodule"
/* The YANG module or submodule name. */
#define YANGLIB_YANG_LIBRARY_MODULE_SET_MODULE_SUBMODULE_NAME "name"
/* The YANG module or submodule revision date.  If no revision statement is present in the YANG module or submodule, this leaf is not instantiated. */
#define YANGLIB_YANG_LIBRARY_MODULE_SET_MODULE_SUBMODULE_REVISION "revision"
/* Contains a URL that represents the YANG schema resource for this module or submodule.  This leaf will only be present if there is a URL available for retrieval of the schema for this entry. */
#define YANGLIB_YANG_LIBRARY_MODULE_SET_MODULE_SUBMODULE_LOCATION "location"
/* List of all YANG feature names from this module that are supported by the server, regardless whether they are defined in the module or any included submodule. */
#define YANGLIB_YANG_LIBRARY_MODULE_SET_MODULE_FEATURE "feature"
/* List of all YANG deviation modules used by this server to modify the conformance of the module associated with this entry.  Note that the same module can be used for deviations for multiple modules, so the same entry MAY appear within multiple 'module' entries.  This reference MUST NOT (directly or indirectly) refer to the module being deviated.  Robust clients may want to make sure that they handle a situation where a module deviates itself (directly or indirectly) gracefully. */
#define YANGLIB_YANG_LIBRARY_MODULE_SET_MODULE_DEVIATION "deviation"
/* An entry in this list indicates that the server imports reusable definitions from the specified revision of the module but does not implement any protocol-accessible objects from this revision.  Multiple entries for the same module name MAY exist.  This can occur if multiple modules import the same module but specify different revision dates in the import statements. */
#define YANGLIB_YANG_LIBRARY_MODULE_SET_IMPORT_ONLY_MODULE_PATH "import-only-module"
/* The YANG module name. */
#define YANGLIB_YANG_LIBRARY_MODULE_SET_IMPORT_ONLY_MODULE_NAME "name"
/* The YANG module revision date. A zero-length string is used if no revision statement is present in the YANG module. */
#define YANGLIB_YANG_LIBRARY_MODULE_SET_IMPORT_ONLY_MODULE_REVISION "revision"
/* The XML namespace identifier for this module. */
#define YANGLIB_YANG_LIBRARY_MODULE_SET_IMPORT_ONLY_MODULE_NAMESPACE "namespace"
/* Contains a URL that represents the YANG schema resource for this module or submodule.  This leaf will only be present if there is a URL available for retrieval of the schema for this entry. */
#define YANGLIB_YANG_LIBRARY_MODULE_SET_IMPORT_ONLY_MODULE_LOCATION "location"
/* Each entry represents one submodule within the parent module. */
#define YANGLIB_YANG_LIBRARY_MODULE_SET_IMPORT_ONLY_MODULE_SUBMODULE_PATH "submodule"
/* The YANG module or submodule name. */
#define YANGLIB_YANG_LIBRARY_MODULE_SET_IMPORT_ONLY_MODULE_SUBMODULE_NAME "name"
/* The YANG module or submodule revision date.  If no revision statement is present in the YANG module or submodule, this leaf is not instantiated. */
#define YANGLIB_YANG_LIBRARY_MODULE_SET_IMPORT_ONLY_MODULE_SUBMODULE_REVISION "revision"
/* Contains a URL that represents the YANG schema resource for this module or submodule.  This leaf will only be present if there is a URL available for retrieval of the schema for this entry. */
#define YANGLIB_YANG_LIBRARY_MODULE_SET_IMPORT_ONLY_MODULE_SUBMODULE_LOCATION "location"
/* A datastore schema that may be used by one or more datastores.  The schema must be valid and referentially complete, i.e., it must contain modules to satisfy all used import statements for all modules specified in the schema. */
#define YANGLIB_YANG_LIBRARY_SCHEMA_PATH "/yanglib:yang-library/schema"
/* An arbitrary name of the schema. */
#define YANGLIB_YANG_LIBRARY_SCHEMA_NAME "name"
/* A set of module-sets that are included in this schema. If a non-import-only module appears in multiple module sets, then the module revision and the associated features and deviations must be identical. */
#define YANGLIB_YANG_LIBRARY_SCHEMA_MODULE_SET "module-set"
/* A datastore supported by this server.  Each datastore indicates which schema it supports.  The server MUST instantiate one entry in this list per specific datastore it supports. Each datastore entry with the same datastore schema SHOULD reference the same schema. */
#define YANGLIB_YANG_LIBRARY_DATASTORE_PATH "/yanglib:yang-library/datastore"
/* The identity of the datastore. */
#define YANGLIB_YANG_LIBRARY_DATASTORE_NAME "name"
/* A reference to the schema supported by this datastore. All non-import-only modules of the schema are implemented with their associated features and deviations. */
#define YANGLIB_YANG_LIBRARY_DATASTORE_SCHEMA "schema"
/* A server-generated identifier of the contents of the '/yang-library' tree.  The server MUST change the value of this leaf if the information represented by the '/yang-library' tree, except '/yang-library/content-id', has changed. */
#define YANGLIB_YANG_LIBRARY_CONTENT_ID "content-id"
/* Contains YANG module monitoring information. */
#define YANGLIB_MODULES_STATE_PATH "/yanglib:modules-state"
/* Contains a server-specific identifier representing the current set of modules and submodules.  The server MUST change the value of this leaf if the information represented by the 'module' list instances has changed. */
#define YANGLIB_MODULES_STATE_MODULE_SET_ID "/yanglib:modules-state/module-set-id"
/* Each entry represents one revision of one module currently supported by the server. */
#define YANGLIB_MODULES_STATE_MODULE_PATH "/yanglib:modules-state/module"
/* The YANG module or submodule name. */
#define YANGLIB_MODULES_STATE_MODULE_NAME "name"
/* The YANG module or submodule revision date. A zero-length string is used if no revision statement is present in the YANG module or submodule. */
#define YANGLIB_MODULES_STATE_MODULE_REVISION "revision"
/* Contains a URL that represents the YANG schema resource for this module or submodule.  This leaf will only be present if there is a URL available for retrieval of the schema for this entry. */
#define YANGLIB_MODULES_STATE_MODULE_SCHEMA "schema"
/* The XML namespace identifier for this module. */
#define YANGLIB_MODULES_STATE_MODULE_NAMESPACE "namespace"
/* List of YANG feature names from this module that are supported by the server, regardless of whether they are defined in the module or any included submodule. */
#define YANGLIB_MODULES_STATE_MODULE_FEATURE "feature"
/* List of YANG deviation module names and revisions used by this server to modify the conformance of the module associated with this entry.  Note that the same module can be used for deviations for multiple modules, so the same entry MAY appear within multiple 'module' entries.  The deviation module MUST be present in the 'module' list, with the same name and revision values. The 'conformance-type' value will be 'implement' for the deviation module. */
#define YANGLIB_MODULES_STATE_MODULE_DEVIATION_PATH "deviation"
/* The YANG module or submodule name. */
#define YANGLIB_MODULES_STATE_MODULE_DEVIATION_NAME "name"
/* The YANG module or submodule revision date. A zero-length string is used if no revision statement is present in the YANG module or submodule. */
#define YANGLIB_MODULES_STATE_MODULE_DEVIATION_REVISION "revision"
/* Indicates the type of conformance the server is claiming for the YANG module identified by this entry. */
#define YANGLIB_MODULES_STATE_MODULE_CONFORMANCE_TYPE "conformance-type"
#define YANGLIB_MODULES_STATE_MODULE_CONFORMANCE_TYPE_IMPLEMENT 0
#define YANGLIB_MODULES_STATE_MODULE_CONFORMANCE_TYPE_IMPORT 1
/* Each entry represents one submodule within the parent module. */
#define YANGLIB_MODULES_STATE_MODULE_SUBMODULE_PATH "submodule"
/* The YANG module or submodule name. */
#define YANGLIB_MODULES_STATE_MODULE_SUBMODULE_NAME "name"
/* The YANG module or submodule revision date. A zero-length string is used if no revision statement is present in the YANG module or submodule. */
#define YANGLIB_MODULES_STATE_MODULE_SUBMODULE_REVISION "revision"
/* Contains a URL that represents the YANG schema resource for this module or submodule.  This leaf will only be present if there is a URL available for retrieval of the schema for this entry. */
#define YANGLIB_MODULES_STATE_MODULE_SUBMODULE_SCHEMA "schema"

