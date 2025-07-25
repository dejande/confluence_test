#!/usr/bin/env python3

from langchain.tools import BaseTool
from pydantic import BaseModel, Field
from typing import Optional, Type, Dict, Any
import json

# Import our existing functions
from confluence_reader import run as confluence_run, describe as confluence_describe


class ConfluenceExtractorInput(BaseModel):
    """Input schema for Confluence Extractor tool."""
    url: str = Field(description="Confluence page URL to extract content from")
    include_comments: bool = Field(default=True, description="Include page comments and nested replies")
    debug: bool = Field(default=False, description="Enable debug output")
    output_file: Optional[str] = Field(default=None, description="Optional file path to save extracted content")
    email: Optional[str] = Field(default=None, description="Confluence email (optional if env var set)")
    api_token: Optional[str] = Field(default=None, description="Confluence API token (optional if env var set)")


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
    description: str = "Extract Confluence pages with text, images, tables, and comments into LLM-optimized format. Supports OCR for table images and complete comment threading."
    args_schema: Type[BaseModel] = ConfluenceExtractorInput
    return_direct: bool = False

    def _run(self, 
             url: str,
             include_comments: bool = False,
             debug: bool = False,
             output_file: Optional[str] = None,
             email: Optional[str] = None,
             api_token: Optional[str] = None) -> str:
        """
        Execute the Confluence extraction.
        
        Args:
            url: Confluence page URL
            include_comments: Whether to include page comments and replies
            debug: Enable debug output
            output_file: Optional file path to save content
            email: Confluence email (optional if env var set)
            api_token: Confluence API token (optional if env var set)
            
        Returns:
            Extracted content as LLM-optimized text string
        """
        try:
            # Prepare parameters for the extraction function
            params = {
                'url': url,
                'include_comments': include_comments,
                'debug': debug
            }
            
            if output_file:
                params['output_file'] = output_file
            if email:
                params['email'] = email
            if api_token:
                params['api_token'] = api_token
            
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

    async def _arun(self, 
                    url: str,
                    include_comments: bool = False,
                    debug: bool = False,
                    output_file: Optional[str] = None,
                    email: Optional[str] = None,
                    api_token: Optional[str] = None) -> str:
        """Async version of the extraction (currently just calls sync version)."""
        return self._run(url, include_comments, debug, output_file, email, api_token)

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