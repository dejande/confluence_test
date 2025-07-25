#!/usr/bin/env python3

from langchain.tools import BaseTool
from pydantic import BaseModel, Field
from typing import Optional, Type, Dict, Any
import json

# Import our existing functions
from confluence_reader import run as confluence_run, describe as confluence_describe


class ConfluenceExtractorInput(BaseModel):
    """Input schema for Confluence Extractor tool."""
    query: str = Field(description="Confluence page URL or JSON config. Examples: 'https://domain.atlassian.net/wiki/pages/123456' or '{\"url\": \"https://...\", \"include_comments\": true}'")


class ConfluenceExtractorTool(BaseTool):
    """
    LangChain tool for extracting Confluence pages with OCR and comment processing.
    
    This tool converts Confluence pages into LLM-optimized text format, including:
    - Clean text extraction from HTML
    - Table extraction from embedded images using OCR
    - Page comments with nested reply threads
    - Content context and discussion threads
    """
    
    name: str = "confluence_extractor"
    description: str = "Extract Confluence pages with text, images, tables, and comments into LLM-optimized format. Input can be a URL or JSON config with options."
    args_schema: Type[BaseModel] = ConfluenceExtractorInput
    return_direct: bool = False

    def _run(self, query: str) -> str:
        """
        Execute the Confluence extraction.
        
        Args:
            query: Confluence page URL or JSON config string
            
        Returns:
            Extracted content as LLM-optimized text string
        """
        try:
            # Parse input - could be URL or JSON config
            if query.strip().startswith('{'):
                # JSON config
                try:
                    params = json.loads(query)
                except json.JSONDecodeError:
                    return f"Error: Invalid JSON config: {query}"
            else:
                # Simple URL
                params = {
                    'url': query.strip(),
                    'include_comments': True,  # Default to including comments for LLM use
                    'debug': False
                }
            
            # Run the extraction
            result = confluence_run(params)
            
            if result['status'] == 'success':
                # Return the clean content for LangChain use
                content = result['content']
                
                # Add metadata header for context
                metadata = f"# {result['title']}\n"
                metadata += f"**Source:** {result['url']}\n"
                metadata += f"**Page ID:** {result['page_id']}\n"
                metadata += f"**Type:** {result['type']}\n\n"
                
                return metadata + content
            else:
                return f"Error extracting Confluence page: {result['message']}"
                
        except Exception as e:
            return f"Error in Confluence extraction: {str(e)}"

    async def _arun(self, query: str) -> str:
        """Async version of the extraction (currently just calls sync version)."""
        return self._run(query)

    def get_params_schema(self) -> Dict[str, Any]:
        """Get the parameter schema for the tool."""
        agent_desc = confluence_describe()
        return agent_desc['parameters']


# Convenience function to create the tool instance
def create_confluence_tool() -> ConfluenceExtractorTool:
    """Create a Confluence extractor tool instance."""
    return ConfluenceExtractorTool()


# Example usage
if __name__ == "__main__":
    # Create the tool
    tool = create_confluence_tool()
    
    # Example usage
    print("Tool Name:", tool.name)
    print("Tool Description:", tool.description)
    print()
    
    # Test extraction (requires environment variables to be set)
    test_url = "https://your-domain.atlassian.net/wiki/spaces/SPACE/pages/123456/Test+Page"
    
    try:
        result = tool._run(url=test_url, include_comments=True, debug=True)
        print("Extraction Result:")
        print(result[:500] + "..." if len(result) > 500 else result)
    except Exception as e:
        print(f"Test failed (expected if no valid URL/credentials): {e}")