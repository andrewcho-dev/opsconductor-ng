"""
OpsConductor Automation Service Libraries
Contains execution libraries for different platforms and protocols
"""

__version__ = "1.0.0"
__author__ = "OpsConductor Team"

# Available libraries
AVAILABLE_LIBRARIES = [
    'windows_powershell',
    'connection_manager',
    'linux_ssh',  # Future implementation
    'network_analyzer'  # Network analysis and protocol analysis
]

def get_library_info():
    """Get information about available libraries"""
    return {
        'version': __version__,
        'available_libraries': AVAILABLE_LIBRARIES,
        'description': 'Automation execution libraries for OpsConductor'
    }
