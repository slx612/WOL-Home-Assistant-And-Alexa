"""Constants for PC Power Free."""

DOMAIN = "pc_power_free"

CONF_AGENT_PORT = "agent_port"
CONF_API_TOKEN = "api_token"
CONF_BROADCAST_ADDRESS = "broadcast_address"
CONF_BROADCAST_PORT = "broadcast_port"
CONF_DISCOVERY_SUBNETS = "discovery_subnets"
CONF_MACHINE_ID = "machine_id"
CONF_SCAN_INTERVAL = "scan_interval"

DISCOVERY_CACHE = "discoveries"
MANUAL_DISCOVERY_OPTION = "__manual__"

DEFAULT_AGENT_PORT = 8777
DEFAULT_BROADCAST_ADDRESS = "255.255.255.255"
DEFAULT_BROADCAST_PORT = 9
DEFAULT_DISCOVERY_SUBNETS = ""
DEFAULT_SCAN_INTERVAL = 30

ZEROCONF_SERVICE_TYPE = "_pcpowerfree._tcp.local."

STATUS_AGENT_VERSION = "agent_version"
STATUS_HOST = "host"
STATUS_HOSTNAME = "hostname"
STATUS_LAST_COMMAND = "last_command"
STATUS_MAC_ADDRESSES = "mac_addresses"
STATUS_MACHINE_ID = "machine_id"
STATUS_ONLINE = "online"
STATUS_REACHABLE = "reachable"
