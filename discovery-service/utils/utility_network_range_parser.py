#!/usr/bin/env python3
"""
Network Range Parser Utility Module
Handles parsing and optimization of network ranges for discovery
"""

import ipaddress
import re
from typing import List
from .logging import get_logger

logger = get_logger("discovery-service.network-range-parser")


class NetworkRangeParserUtility:
    """Utility class for parsing and optimizing network ranges"""
    
    @staticmethod
    def parse_network_ranges(range_input: str) -> List[str]:
        """
        Parse various network range formats into individual IP addresses
        Supports: CIDR, IP ranges, comma-separated IPs, single IPs
        """
        if not range_input or not range_input.strip():
            raise ValueError("Empty network range input")
        
        # Split by comma and process each entry
        entries = [entry.strip() for entry in range_input.split(',')]
        all_ips = []
        
        for entry in entries:
            if not entry:
                continue
            try:
                parsed_ips = NetworkRangeParserUtility._parse_single_entry(entry)
                all_ips.extend(parsed_ips)
            except Exception as e:
                logger.error(f"Failed to parse network range entry '{entry}': {e}")
                raise ValueError(f"Invalid network range format: {entry}")
        
        if not all_ips:
            raise ValueError("No valid IP addresses found in input")
        
        # Remove duplicates while preserving order
        unique_ips = list(dict.fromkeys(all_ips))
        logger.info(f"Parsed {len(unique_ips)} unique IP addresses from input")
        
        return unique_ips
    
    @staticmethod
    def _parse_single_entry(entry: str) -> List[str]:
        """Parse a single network range entry"""
        entry = entry.strip()
        
        # CIDR notation (e.g., 192.168.1.0/24)
        if '/' in entry:
            return NetworkRangeParserUtility._parse_cidr(entry)
        
        # IP range (e.g., 192.168.1.100-120 or 192.168.1.100-192.168.1.120)
        elif '-' in entry:
            return NetworkRangeParserUtility._parse_ip_range(entry)
        
        # Single IP address
        else:
            return NetworkRangeParserUtility._parse_single_ip(entry)
    
    @staticmethod
    def _parse_cidr(cidr: str) -> List[str]:
        """Parse CIDR notation (e.g., 192.168.1.0/24)"""
        try:
            network = ipaddress.IPv4Network(cidr, strict=False)
            # Limit to reasonable size to prevent memory issues
            if network.num_addresses > 65536:  # /16 or larger
                raise ValueError(f"Network range too large: {cidr} ({network.num_addresses} addresses)")
            
            return [str(ip) for ip in network.hosts()]
        except ipaddress.AddressValueError as e:
            raise ValueError(f"Invalid CIDR notation: {cidr}")
    
    @staticmethod
    def _parse_ip_range(ip_range: str) -> List[str]:
        """Parse IP range (e.g., 192.168.1.100-120 or 192.168.1.100-192.168.1.120)"""
        try:
            start_str, end_str = ip_range.split('-', 1)
            start_str = start_str.strip()
            end_str = end_str.strip()
            
            # Full IP range (192.168.1.100-192.168.1.120)
            if '.' in end_str:
                start_ip = ipaddress.IPv4Address(start_str)
                end_ip = ipaddress.IPv4Address(end_str)
            
            # Partial range (192.168.1.100-120)
            else:
                start_ip = ipaddress.IPv4Address(start_str)
                # Extract the base network and replace last octet
                base_parts = start_str.split('.')
                if len(base_parts) != 4:
                    raise ValueError("Invalid IP format in range")
                
                base_parts[3] = end_str
                end_ip = ipaddress.IPv4Address('.'.join(base_parts))
            
            if start_ip > end_ip:
                raise ValueError("Start IP must be less than or equal to end IP")
            
            # Limit range size
            range_size = int(end_ip) - int(start_ip) + 1
            if range_size > 1024:
                raise ValueError(f"IP range too large: {range_size} addresses")
            
            ips = []
            current_ip = start_ip
            while current_ip <= end_ip:
                ips.append(str(current_ip))
                current_ip += 1
            
            return ips
            
        except (ValueError, ipaddress.AddressValueError) as e:
            raise ValueError(f"Invalid IP range format: {ip_range}")
    
    @staticmethod
    def _parse_single_ip(ip: str) -> List[str]:
        """Parse and validate a single IP address"""
        try:
            ipaddress.IPv4Address(ip)
            return [ip]
        except ipaddress.AddressValueError:
            raise ValueError(f"Invalid IP address: {ip}")
    
    @staticmethod
    def optimize_targets_for_nmap(targets: List[str]) -> List[str]:
        """
        Optimize target list for efficient nmap scanning by grouping consecutive IPs
        """
        if not targets:
            return []
        
        # Convert to IPv4Address objects for sorting and grouping
        try:
            ip_objects = [ipaddress.IPv4Address(ip) for ip in targets]
            ip_objects.sort()
        except ipaddress.AddressValueError as e:
            logger.error(f"Invalid IP address in targets: {e}")
            return targets  # Return original list if conversion fails
        
        # Group consecutive IPs into ranges
        optimized = NetworkRangeParserUtility._group_consecutive_ips(ip_objects)
        
        logger.info(f"Optimized {len(targets)} targets into {len(optimized)} ranges")
        return optimized
    
    @staticmethod
    def _group_consecutive_ips(ips: List[ipaddress.IPv4Address]) -> List[str]:
        """Group consecutive IP addresses into ranges for efficient nmap scanning"""
        if not ips:
            return []
        
        ranges = []
        start = ips[0]
        end = ips[0]
        
        for i in range(1, len(ips)):
            current = ips[i]
            
            # If current IP is consecutive to the end of current range
            if int(current) == int(end) + 1:
                end = current
            else:
                # End current range and start new one
                ranges.append(NetworkRangeParserUtility._format_ip_range(start, end))
                start = current
                end = current
        
        # Add the last range
        ranges.append(NetworkRangeParserUtility._format_ip_range(start, end))
        
        return ranges
    
    @staticmethod
    def _format_ip_range(start: ipaddress.IPv4Address, end: ipaddress.IPv4Address) -> str:
        """Format IP range for nmap scanning"""
        if start == end:
            return str(start)
        
        # Check if we can use CIDR notation
        try:
            # Try to find a network that covers exactly this range
            range_size = int(end) - int(start) + 1
            
            # Check if range size is a power of 2 and properly aligned
            if range_size & (range_size - 1) == 0:  # Power of 2
                prefix_len = 32 - range_size.bit_length() + 1
                if prefix_len >= 0:
                    network = ipaddress.IPv4Network(f"{start}/{prefix_len}", strict=False)
                    if network.network_address == start and network.broadcast_address == end:
                        return str(network)
        except:
            pass
        
        # Use range notation for nmap
        start_parts = str(start).split('.')
        end_parts = str(end).split('.')
        
        # Find the first differing octet
        for i in range(4):
            if start_parts[i] != end_parts[i]:
                # If only the last octet differs, use short range notation
                if i == 3:
                    return f"{'.'.join(start_parts[:3])}.{start_parts[3]}-{end_parts[3]}"
                else:
                    # Use full range notation
                    return f"{start}-{end}"
        
        return str(start)  # Should not reach here, but fallback