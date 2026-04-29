"""Constants for PC Power Free."""

DOMAIN = "pc_power_free"

CONF_AGENT_PORT = "agent_port"
CONF_API_TOKEN = "api_token"
CONF_BROADCAST_ADDRESS = "broadcast_address"
CONF_BROADCAST_PORT = "broadcast_port"
CONF_CAPABILITIES = "capabilities"
CONF_DISCOVERY_SUBNETS = "discovery_subnets"
CONF_MACHINE_ID = "machine_id"
CONF_PLATFORM = "platform"
CONF_SCAN_INTERVAL = "scan_interval"

DISCOVERY_CACHE = "discoveries"
MANUAL_DISCOVERY_OPTION = "__manual__"

DEFAULT_AGENT_PORT = 58477
DEFAULT_BROADCAST_ADDRESS = "255.255.255.255"
DEFAULT_BROADCAST_PORT = 9
DEFAULT_DISCOVERY_SUBNETS = ""
DEFAULT_SCAN_INTERVAL = 30

ZEROCONF_SERVICE_TYPE = "_pcpowerfree._tcp.local."

STATUS_AGENT_VERSION = "agent_version"
STATUS_BOOTED_AT = "booted_at"
STATUS_CAPABILITIES = "capabilities"
STATUS_COMMAND_GUARD_ACTIVE = "command_guard_active"
STATUS_COMMAND_GUARD_MODE = "command_guard_mode"
STATUS_COMMAND_GUARD_UNTIL_TS = "command_guard_until_ts"
STATUS_HOST = "host"
STATUS_HOSTNAME = "hostname"
STATUS_LAST_COMMAND = "last_command"
STATUS_LAST_COMMAND_AT = "last_command_at"
STATUS_MAC_ADDRESSES = "mac_addresses"
STATUS_MACHINE_ID = "machine_id"
STATUS_ONLINE = "online"
STATUS_PLATFORM = "platform"
STATUS_REACHABLE = "reachable"
STATUS_UPTIME_SECONDS = "uptime_seconds"
