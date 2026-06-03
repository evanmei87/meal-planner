from fastmcp import FastMCP

mcp = FastMCP("Food & Nutrition Intelligence")

# Import tools
from tools.generate_plan import generate_meal_plan
from tools.update_state import update_state
from tools.search_web import search_web_with_context

# Register tools
mcp.tool("generate_meal_plan", generate_meal_plan, description="Generate a meal plan based on current state and user query.")
mcp.tool("update_state", update_state, description="Update state.json with generated plan and grocery list.")
mcp.tool("search_web", search_web_with_context, description="Search web with @Web context wrapper for nutritional data.")

if __name__ == "__main__":
    mcp.run()
