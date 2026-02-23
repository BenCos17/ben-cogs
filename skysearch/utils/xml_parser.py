"""
XML parsing utilities for SkySearch cog

This module provides a utility class for parsing XML data from APIs, with
safe error handling and convenient methods for common XML operations.

Example usage:
    ```python
    from ..utils.xml_parser import XMLParser
    
    parser = XMLParser()
    
    # Fetch and parse XML from a URL
    async with aiohttp.ClientSession() as session:
        root = await parser.fetch_and_parse_xml(session, "https://api.example.com/data.xml")
        if root:
            airports = parser.find_elements(root, ".//Airport")
            for airport in airports:
                code = parser.get_text(airport, "ARPT")
                print(f"Airport code: {code}")
    ```
"""

import xml.etree.ElementTree as ET
from typing import Optional, List, Dict, Any
import aiohttp


class XMLParser:
    """
    Utility class for parsing XML data from APIs.
    
    Provides safe, convenient methods for common XML parsing operations
    with built-in error handling. All methods return None or empty lists
    on failure, making it easy to handle errors gracefully.
    
    All methods are static, so you can use them without instantiating the class:
    ```python
    root = XMLParser.parse_xml_string(xml_data)
    ```
    
    Or instantiate for convenience:
    ```python
    parser = XMLParser()
    root = parser.parse_xml_string(xml_data)
    ```
    """
    
    @staticmethod
    def parse_xml_string(xml_string: str) -> Optional[ET.Element]:
        """
        Parse an XML string into an ElementTree Element.
        
        Args:
            xml_string: The XML string to parse
            
        Returns:
            ElementTree Element root, or None if parsing fails
        """
        try:
            return ET.fromstring(xml_string)
        except ET.ParseError:
            return None
    
    @staticmethod
    def find_elements(root: ET.Element, xpath: str) -> List[ET.Element]:
        """
        Find elements matching an XPath expression.
        
        Args:
            root: The root ElementTree Element
            xpath: XPath expression (e.g., ".//Airport")
            
        Returns:
            List of matching elements
        """
        try:
            return root.findall(xpath)
        except Exception:
            return []
    
    @staticmethod
    def get_text(element: ET.Element, tag: str, default: str = "") -> str:
        """
        Get text content from a child element.
        
        Args:
            element: The parent ElementTree Element
            tag: Tag name of the child element
            default: Default value if element not found
            
        Returns:
            Text content of the child element, or default
        """
        child = element.find(tag)
        if child is not None and child.text:
            return child.text.strip()
        return default
    
    @staticmethod
    async def fetch_and_parse_xml(
        session: aiohttp.ClientSession,
        url: str,
        headers: Optional[Dict[str, str]] = None
    ) -> Optional[ET.Element]:
        """
        Fetch XML from a URL and parse it.
        
        Args:
            session: aiohttp ClientSession
            url: URL to fetch XML from
            headers: Optional HTTP headers
            
        Returns:
            Parsed ElementTree Element root, or None if fetch/parse fails
        """
        try:
            async with session.get(url, headers=headers) as response:
                if response.status != 200:
                    return None
                xml_text = await response.text()
                return XMLParser.parse_xml_string(xml_text)
        except Exception:
            return None
