#!/usr/bin/env python3

"""
Example usage of the Confluence Extractor as a LangChain tool.

This demonstrates how to use the ConfluenceExtractorTool in various LangChain scenarios:
1. As a standalone tool
2. With an agent
3. In a chain
"""

import os
from langchain.agents import initialize_agent, AgentType
from langchain.schema import HumanMessage
from confluence_langchain_tool import create_confluence_tool

# Try to import LLM - use a fallback if not available
try:
    from langchain_openai import OpenAI
    LLM_AVAILABLE = True
except ImportError:
    try:
        from langchain_community.llms import OpenAI
        LLM_AVAILABLE = True
    except ImportError:
        print("⚠️  OpenAI not available. Install with: pip install langchain-openai")
        LLM_AVAILABLE = False
        OpenAI = None


def example_standalone_usage():
    """Example 1: Using the tool standalone"""
    print("=== Standalone Tool Usage ===")
    
    # Create the tool
    confluence_tool = create_confluence_tool()
    
    # Use the tool directly - with JSON config
    result = confluence_tool._run('{"url": "https://cosylab.atlassian.net/wiki/spaces/CBK/pages/103579649/Services+-+June+FY25", "include_comments": true}')
    
    print("Extracted Content:")
    print(result[:500] + "..." if len(result) > 500 else result)
    print()


def example_agent_usage():
    """Example 2: Using with a LangChain agent"""
    print("=== Agent Usage ===")
    
    if not LLM_AVAILABLE:
        print("❌ LLM not available. Skipping agent example.")
        return
    
    if not os.getenv('OPENAI_API_KEY'):
        print("❌ OPENAI_API_KEY not set. Skipping agent example.")
        return
    
    # Initialize LLM with GPT-4o-mini (much larger context window)
    llm = OpenAI(model="gpt-4o-mini", temperature=0)  # Requires OPENAI_API_KEY
    
    # Create tools list
    tools = [create_confluence_tool()]
    
    # Initialize agent with error handling
    agent = initialize_agent(
        tools=tools,
        llm=llm,
        agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
        verbose=True,
        handle_parsing_errors=True
    )
    
    # Use the agent
    query = """
    Extract the content from this Confluence page including comments: 
    https://cosylab.atlassian.net/wiki/spaces/CBK/pages/103579649/Services+-+June+FY25
    Then summarize the main points and any key discussions from the comments.
    """
    
    try:
        result = agent.run(query)
        print("Agent Result:")
        print(result)
    except Exception as e:
        print(f"Agent execution failed: {e}")
    print()


def example_chain_usage():
    """Example 3: Using in a custom chain"""
    print("=== Chain Usage ===")
    
    if not LLM_AVAILABLE:
        print("❌ LLM not available. Skipping chain example.")
        return
    
    if not os.getenv('OPENAI_API_KEY'):
        print("❌ OPENAI_API_KEY not set. Skipping chain example.")
        return
    
    from langchain.chains import LLMChain
    from langchain.prompts import PromptTemplate
    
    # Create the tool
    confluence_tool = create_confluence_tool()
    
    # Create a prompt template
    prompt = PromptTemplate(
        input_variables=["confluence_content"],
        template="""
        Based on the following Confluence page content, please:
        1. Summarize the main points
        2. Identify any action items or decisions
        3. Note key discussion points from comments
        
        Confluence Content:
        {confluence_content}
        
        Summary:
        """
    )
    
    # Create LLM chain with GPT-4o-mini
    llm = OpenAI(model="gpt-4o-mini", temperature=0)
    chain = LLMChain(llm=llm, prompt=prompt)
    
    # Extract content first
    confluence_content = confluence_tool._run("https://cosylab.atlassian.net/wiki/spaces/CBK/pages/103579649/Services+-+June+FY25")
    
    # Run the chain
    try:
        result = chain.run(confluence_content=confluence_content)
        print("Chain Result:")
        print(result)
    except Exception as e:
        print(f"Chain execution failed: {e}")
    print()


def example_tool_schema():
    """Example 4: Inspecting tool schema"""
    print("=== Tool Schema ===")
    
    tool = create_confluence_tool()
    
    print(f"Tool Name: {tool.name}")
    print(f"Description: {tool.description}")
    print(f"Return Direct: {tool.return_direct}")
    print()
    
    print("Input Schema:")
    print(tool.args_schema.schema())
    print()
    
    print("Parameters Schema:")
    params_schema = tool.get_params_schema()
    print(params_schema)


if __name__ == "__main__":
    print("Confluence LangChain Tool Examples")
    print("=" * 50)
    print()
    
    # Set up environment variables reminder
    if not os.getenv('CONFLUENCE_EMAIL') or not os.getenv('CONFLUENCE_API_TOKEN'):
        print("⚠️  Remember to set environment variables:")
        print("   export CONFLUENCE_EMAIL='your.email@example.com'")
        print("   export CONFLUENCE_API_TOKEN='your_api_token'")
        print()
    
    # Run examples (comment out the ones that require API keys)
    example_tool_schema()
    
    # Uncomment these if you have the required environment variables set:
    example_standalone_usage()
    
    # Uncomment if you have OpenAI API key:
    example_agent_usage()
    example_chain_usage()
    
    print("Examples completed!")