#!/usr/bin/env python3
"""
FHIR Integration Configuration and Setup
Configuration management for HL7 FHIR R4 integration
"""

import os
import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from enum import Enum
import configparser
from pathlib import Path

logger = logging.getLogger(__name__)

class FHIRServerType(Enum):
    """FHIR server implementation types"""
    HAPI_FHIR = "hapi_fhir"
    MICROSOFT_FHIR = "microsoft_fhir"
    AWS_HEALTHLAKE = "aws_healthlake"
    GOOGLE_HEALTHCARE = "google_healthcare"
    CERNER_POWERCHART = "cerner_powerchart"
    EPIC_INTERCONNECT = "epic_interconnect"
    ALLSCRIPTS_DEVELOPER = "allscripts_developer"
    CUSTOM = "custom"

class AuthenticationMethod(Enum):
    """FHIR authentication methods"""
    NONE = "none"
    BASIC = "basic"
    OAUTH2 = "oauth2"
    BEARER_TOKEN = "bearer_token"
    CLIENT_CREDENTIALS = "client_credentials"
    MUTUAL_TLS = "mutual_tls"

@dataclass
class FHIRServerConfig:
    """FHIR server configuration"""
    name: str
    server_type: FHIRServerType
    base_url: str
    fhir_version: str = "4.0.1"
    auth_method: AuthenticationMethod = AuthenticationMethod.NONE
    
    # Authentication parameters
    client_id: Optional[str] = None
    client_secret: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    token_url: Optional[str] = None
    scope: Optional[str] = None
    
    # Connection settings
    timeout_seconds: int = 30
    max_retries: int = 3
    verify_ssl: bool = True
    
    # Feature flags
    supports_bulk_export: bool = False
    supports_subscriptions: bool = False
    supports_smart_on_fhir: bool = False
    
    # Resource capabilities
    supported_resources: List[str] = field(default_factory=lambda: [
        "Patient", "Observation", "DiagnosticReport", "DocumentReference"
    ])
    
    # Custom headers
    custom_headers: Dict[str, str] = field(default_factory=dict)

@dataclass
class FHIRMappingConfig:
    """FHIR data mapping configuration"""
    patient_identifier_system: str = "http://clinchat-rag.local/patient-id"
    practitioner_identifier_system: str = "http://clinchat-rag.local/practitioner-id"
    organization_identifier_system: str = "http://clinchat-rag.local/organization-id"
    
    # Code system mappings
    document_type_system: str = "http://loinc.org"
    observation_code_system: str = "http://loinc.org"
    condition_code_system: str = "http://snomed.info/sct"
    medication_code_system: str = "http://www.nlm.nih.gov/research/umls/rxnorm"
    
    # Default codes
    default_document_code: str = "34133-9"  # Summary of episode note
    default_organization_code: str = "clinchat-rag-org"

class FHIRConfigManager:
    """FHIR configuration management"""
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize configuration manager"""
        self.config_path = config_path or self._get_default_config_path()
        self.servers: Dict[str, FHIRServerConfig] = {}
        self.mapping_config = FHIRMappingConfig()
        self._load_config()
    
    def _get_default_config_path(self) -> str:
        """Get default configuration file path"""
        return os.path.join(os.path.dirname(__file__), "fhir_config.ini")
    
    def _load_config(self):
        """Load configuration from file"""
        if not os.path.exists(self.config_path):
            logger.warning(f"Config file not found: {self.config_path}, using defaults")
            self._create_default_config()
            return
        
        try:
            config = configparser.ConfigParser()
            config.read(self.config_path)
            
            # Load server configurations
            for section_name in config.sections():
                if section_name.startswith("server:"):
                    server_name = section_name.replace("server:", "")
                    server_config = self._parse_server_config(config[section_name])
                    server_config.name = server_name
                    self.servers[server_name] = server_config
                
                elif section_name == "mapping":
                    self._parse_mapping_config(config[section_name])
            
            logger.info(f"Loaded {len(self.servers)} FHIR server configurations")
            
        except Exception as e:
            logger.error(f"Failed to load FHIR config: {e}")
            self._create_default_config()
    
    def _parse_server_config(self, config_section) -> FHIRServerConfig:
        """Parse server configuration section"""
        return FHIRServerConfig(
            name="",  # Will be set by caller
            server_type=FHIRServerType(config_section.get("server_type", "hapi_fhir")),
            base_url=config_section.get("base_url"),
            fhir_version=config_section.get("fhir_version", "4.0.1"),
            auth_method=AuthenticationMethod(config_section.get("auth_method", "none")),
            client_id=config_section.get("client_id"),
            client_secret=config_section.get("client_secret"),
            username=config_section.get("username"),
            password=config_section.get("password"),
            token_url=config_section.get("token_url"),
            scope=config_section.get("scope"),
            timeout_seconds=config_section.getint("timeout_seconds", 30),
            max_retries=config_section.getint("max_retries", 3),
            verify_ssl=config_section.getboolean("verify_ssl", True),
            supports_bulk_export=config_section.getboolean("supports_bulk_export", False),
            supports_subscriptions=config_section.getboolean("supports_subscriptions", False),
            supports_smart_on_fhir=config_section.getboolean("supports_smart_on_fhir", False),
            supported_resources=config_section.get("supported_resources", "Patient,Observation,DiagnosticReport,DocumentReference").split(",")
        )
    
    def _parse_mapping_config(self, config_section):
        """Parse mapping configuration section"""
        self.mapping_config.patient_identifier_system = config_section.get(
            "patient_identifier_system", self.mapping_config.patient_identifier_system
        )
        self.mapping_config.practitioner_identifier_system = config_section.get(
            "practitioner_identifier_system", self.mapping_config.practitioner_identifier_system
        )
        self.mapping_config.document_type_system = config_section.get(
            "document_type_system", self.mapping_config.document_type_system
        )
        self.mapping_config.observation_code_system = config_section.get(
            "observation_code_system", self.mapping_config.observation_code_system
        )
    
    def _create_default_config(self):
        """Create default configuration"""
        # Default public HAPI FHIR server
        default_server = FHIRServerConfig(
            name="hapi_public",
            server_type=FHIRServerType.HAPI_FHIR,
            base_url="http://hapi.fhir.org/baseR4",
            fhir_version="4.0.1",
            auth_method=AuthenticationMethod.NONE,
            timeout_seconds=30,
            supports_bulk_export=False,
            supports_subscriptions=False,
            supported_resources=["Patient", "Observation", "DiagnosticReport", "DocumentReference"]
        )
        
        self.servers["hapi_public"] = default_server
        
        # Save default configuration
        self.save_config()
    
    def add_server(self, server_config: FHIRServerConfig):
        """Add FHIR server configuration"""
        self.servers[server_config.name] = server_config
        logger.info(f"Added FHIR server configuration: {server_config.name}")
    
    def get_server(self, server_name: str) -> Optional[FHIRServerConfig]:
        """Get FHIR server configuration"""
        return self.servers.get(server_name)
    
    def list_servers(self) -> List[str]:
        """List available FHIR servers"""
        return list(self.servers.keys())
    
    def save_config(self):
        """Save configuration to file"""
        try:
            config = configparser.ConfigParser()
            
            # Save server configurations
            for server_name, server_config in self.servers.items():
                section_name = f"server:{server_name}"
                config[section_name] = {
                    "server_type": server_config.server_type.value,
                    "base_url": server_config.base_url,
                    "fhir_version": server_config.fhir_version,
                    "auth_method": server_config.auth_method.value,
                    "timeout_seconds": str(server_config.timeout_seconds),
                    "max_retries": str(server_config.max_retries),
                    "verify_ssl": str(server_config.verify_ssl),
                    "supports_bulk_export": str(server_config.supports_bulk_export),
                    "supports_subscriptions": str(server_config.supports_subscriptions),
                    "supports_smart_on_fhir": str(server_config.supports_smart_on_fhir),
                    "supported_resources": ",".join(server_config.supported_resources)
                }
                
                # Add optional auth parameters if present
                if server_config.client_id:
                    config[section_name]["client_id"] = server_config.client_id
                if server_config.client_secret:
                    config[section_name]["client_secret"] = server_config.client_secret
                if server_config.username:
                    config[section_name]["username"] = server_config.username
                if server_config.password:
                    config[section_name]["password"] = server_config.password
                if server_config.token_url:
                    config[section_name]["token_url"] = server_config.token_url
                if server_config.scope:
                    config[section_name]["scope"] = server_config.scope
            
            # Save mapping configuration
            config["mapping"] = {
                "patient_identifier_system": self.mapping_config.patient_identifier_system,
                "practitioner_identifier_system": self.mapping_config.practitioner_identifier_system,
                "document_type_system": self.mapping_config.document_type_system,
                "observation_code_system": self.mapping_config.observation_code_system
            }
            
            # Ensure config directory exists
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            
            # Write configuration file
            with open(self.config_path, "w") as config_file:
                config.write(config_file)
            
            logger.info(f"FHIR configuration saved to {self.config_path}")
            
        except Exception as e:
            logger.error(f"Failed to save FHIR config: {e}")

class FHIRServerTemplates:
    """Pre-configured FHIR server templates"""
    
    @staticmethod
    def get_hapi_fhir_public() -> FHIRServerConfig:
        """Public HAPI FHIR server template"""
        return FHIRServerConfig(
            name="hapi_public",
            server_type=FHIRServerType.HAPI_FHIR,
            base_url="http://hapi.fhir.org/baseR4",
            fhir_version="4.0.1",
            auth_method=AuthenticationMethod.NONE,
            supports_bulk_export=False,
            supports_subscriptions=True,
            supported_resources=["Patient", "Observation", "DiagnosticReport", "DocumentReference", "Practitioner", "Organization"]
        )
    
    @staticmethod
    def get_microsoft_fhir_template() -> FHIRServerConfig:
        """Microsoft FHIR Service template"""
        return FHIRServerConfig(
            name="microsoft_fhir",
            server_type=FHIRServerType.MICROSOFT_FHIR,
            base_url="https://your-workspace-fhir.fhir.azurehealthcareapis.com",
            fhir_version="4.0.1",
            auth_method=AuthenticationMethod.OAUTH2,
            token_url="https://login.microsoftonline.com/your-tenant-id/oauth2/v2.0/token",
            scope="https://your-workspace-fhir.fhir.azurehealthcareapis.com/.default",
            supports_bulk_export=True,
            supports_smart_on_fhir=True,
            supported_resources=["Patient", "Observation", "DiagnosticReport", "DocumentReference", "Practitioner", "Organization", "Condition", "MedicationRequest"]
        )
    
    @staticmethod
    def get_aws_healthlake_template() -> FHIRServerConfig:
        """AWS HealthLake template"""
        return FHIRServerConfig(
            name="aws_healthlake",
            server_type=FHIRServerType.AWS_HEALTHLAKE,
            base_url="https://healthlake.us-east-1.amazonaws.com/datastore/your-datastore-id/r4/",
            fhir_version="4.0.1",
            auth_method=AuthenticationMethod.CLIENT_CREDENTIALS,
            supports_bulk_export=True,
            supports_subscriptions=False,
            supported_resources=["Patient", "Observation", "DiagnosticReport", "DocumentReference", "Condition", "MedicationRequest", "Procedure"]
        )
    
    @staticmethod
    def get_epic_template() -> FHIRServerConfig:
        """Epic FHIR server template"""
        return FHIRServerConfig(
            name="epic_fhir",
            server_type=FHIRServerType.EPIC_INTERCONNECT,
            base_url="https://fhir.epic.com/interconnect-fhir-oauth/api/FHIR/R4",
            fhir_version="4.0.1",
            auth_method=AuthenticationMethod.OAUTH2,
            supports_smart_on_fhir=True,
            supports_bulk_export=False,
            supported_resources=["Patient", "Observation", "DiagnosticReport", "DocumentReference", "Condition", "MedicationRequest", "AllergyIntolerance"]
        )

def setup_fhir_config_interactive():
    """Interactive FHIR configuration setup"""
    print("🏥 ClinChat-RAG FHIR Configuration Setup")
    print("=" * 50)
    
    config_manager = FHIRConfigManager()
    
    while True:
        print("\n📋 Available options:")
        print("1. Add new FHIR server")
        print("2. List existing servers")
        print("3. Use server template")
        print("4. Test server connection")
        print("5. Save and exit")
        
        choice = input("\nSelect option (1-5): ").strip()
        
        if choice == "1":
            _add_server_interactive(config_manager)
        elif choice == "2":
            _list_servers(config_manager)
        elif choice == "3":
            _use_template(config_manager)
        elif choice == "4":
            _test_connection(config_manager)
        elif choice == "5":
            config_manager.save_config()
            print("✅ Configuration saved successfully!")
            break
        else:
            print("❌ Invalid option. Please select 1-5.")

def _add_server_interactive(config_manager: FHIRConfigManager):
    """Add server configuration interactively"""
    print("\n🔧 Add New FHIR Server")
    print("-" * 25)
    
    name = input("Server name: ").strip()
    base_url = input("Base URL: ").strip()
    
    print("\nServer types:")
    for i, server_type in enumerate(FHIRServerType, 1):
        print(f"{i}. {server_type.value}")
    
    try:
        type_choice = int(input("Select server type (1-8): ").strip())
        server_type = list(FHIRServerType)[type_choice - 1]
    except (ValueError, IndexError):
        server_type = FHIRServerType.HAPI_FHIR
    
    print("\nAuthentication methods:")
    for i, auth_method in enumerate(AuthenticationMethod, 1):
        print(f"{i}. {auth_method.value}")
    
    try:
        auth_choice = int(input("Select auth method (1-6): ").strip())
        auth_method = list(AuthenticationMethod)[auth_choice - 1]
    except (ValueError, IndexError):
        auth_method = AuthenticationMethod.NONE
    
    # Create server configuration
    server_config = FHIRServerConfig(
        name=name,
        server_type=server_type,
        base_url=base_url,
        auth_method=auth_method
    )
    
    # Add authentication details if needed
    if auth_method in [AuthenticationMethod.OAUTH2, AuthenticationMethod.CLIENT_CREDENTIALS]:
        server_config.client_id = input("Client ID: ").strip()
        server_config.client_secret = input("Client Secret: ").strip()
        server_config.token_url = input("Token URL: ").strip()
        server_config.scope = input("Scope (optional): ").strip() or None
    
    elif auth_method == AuthenticationMethod.BASIC:
        server_config.username = input("Username: ").strip()
        server_config.password = input("Password: ").strip()
    
    elif auth_method == AuthenticationMethod.BEARER_TOKEN:
        # Note: In production, tokens should be managed securely
        print("Note: Bearer tokens should be configured via environment variables in production")
    
    config_manager.add_server(server_config)
    print(f"✅ Added server configuration: {name}")

def _list_servers(config_manager: FHIRConfigManager):
    """List existing server configurations"""
    servers = config_manager.list_servers()
    
    if not servers:
        print("\n📭 No FHIR servers configured")
        return
    
    print(f"\n📋 Configured FHIR Servers ({len(servers)})")
    print("-" * 30)
    
    for server_name in servers:
        server = config_manager.get_server(server_name)
        if server:
            print(f"• {server_name}")
            print(f"  URL: {server.base_url}")
            print(f"  Type: {server.server_type.value}")
            print(f"  Auth: {server.auth_method.value}")
            print(f"  Resources: {len(server.supported_resources)}")
            print()

def _use_template(config_manager: FHIRConfigManager):
    """Use predefined server templates"""
    print("\n📄 FHIR Server Templates")
    print("-" * 25)
    
    templates = {
        "1": ("Public HAPI FHIR", FHIRServerTemplates.get_hapi_fhir_public),
        "2": ("Microsoft FHIR Service", FHIRServerTemplates.get_microsoft_fhir_template),
        "3": ("AWS HealthLake", FHIRServerTemplates.get_aws_healthlake_template),
        "4": ("Epic FHIR", FHIRServerTemplates.get_epic_template)
    }
    
    for key, (name, _) in templates.items():
        print(f"{key}. {name}")
    
    choice = input("\nSelect template (1-4): ").strip()
    
    if choice in templates:
        template_name, template_func = templates[choice]
        server_config = template_func()
        
        # Allow customization
        custom_name = input(f"Server name [{server_config.name}]: ").strip()
        if custom_name:
            server_config.name = custom_name
        
        if server_config.base_url.startswith("https://your-"):
            custom_url = input(f"Base URL [{server_config.base_url}]: ").strip()
            if custom_url:
                server_config.base_url = custom_url
        
        config_manager.add_server(server_config)
        print(f"✅ Added {template_name} configuration")
    else:
        print("❌ Invalid template selection")

def _test_connection(config_manager: FHIRConfigManager):
    """Test FHIR server connection"""
    servers = config_manager.list_servers()
    
    if not servers:
        print("\n❌ No servers configured for testing")
        return
    
    print("\n🔍 Test Server Connection")
    print("-" * 25)
    
    for i, server_name in enumerate(servers, 1):
        print(f"{i}. {server_name}")
    
    try:
        choice = int(input("Select server to test: ").strip())
        server_name = servers[choice - 1]
        server_config = config_manager.get_server(server_name)
        
        if server_config:
            print(f"Testing connection to {server_name}...")
            # Note: Actual connection testing would require the FHIRPatientExchange class
            print("⚠️  Connection testing requires the FHIR integration module to be loaded")
            print(f"Server URL: {server_config.base_url}")
            print(f"Auth Method: {server_config.auth_method.value}")
        
    except (ValueError, IndexError):
        print("❌ Invalid server selection")

if __name__ == "__main__":
    # Run interactive setup if called directly
    setup_fhir_config_interactive()