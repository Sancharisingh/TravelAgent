# AI Travel Planning App using LangGraph + MCP

A multi-agent travel planner built with LangGraph, MCP servers, and real-time flight, hotel, weather, and attraction data.

This repository combines:

- `main.py`: LangGraph state graph orchestrating the travel planning pipeline
- `frontend.py`: Streamlit interface for interactive travel plan generation
- `mcp_client.py`: MCP client configuration for Tavily search, AviationStack, and weather providers
- `custom_weather_mcp_server.py`: local MCP weather server using OpenWeatherMap
- `aviationstack-mcp/`: local AviationStack MCP server package
- `travel_requirements.py` and `attraction_availability.py`: domain rules for hotel requirements and attraction availability

## Features

- Multi-agent travel planning pipeline
- Flight and route planning
- Hotel/accommodation discovery from Tavily MCP
- Real-time weather and forecast from a local OpenWeatherMap MCP server
- Curated attraction availability rules for popular Indian landmarks
- Optional PostgreSQL-backed LangGraph session memory
- Streamlit UI with agent progress tracking

## Architecture

The app uses a LangGraph `StateGraph` in `main.py` with the following agent stages:

1. `flight_agent`
2. `route_agent`
3. `hotel_agent`
4. `weather_agent`
5. `attraction_agent`
6. `itinerary_agent`

`mcp_client.py` configures three MCP tool providers:

- `tavily` via remote HTTP MCP
- `aviationstack` via local stdio MCP
- `weather` via a local custom MCP server

## Requirements

- Python 3.13+
- `streamlit`
- `langgraph`, `langchain`, `langchain-groq`, `langchain-tavily`
- `psycopg[binary]`, `psycopg_pool`
- `python-dotenv`
- `mcp`, `requests`
- PostgreSQL (optional for persistent memory)
- API keys for:
  - Groq
  - Tavily
  - AviationStack
  - OpenWeatherMap

## Setup

### 1. Create and activate a Python environment

```bash
python -m venv langgraph_env3
source langgraph_env3/bin/activate
```

### 2. Install dependencies

```bash
pip install langgraph langchain langchain-openai langchain-groq langchain-community langchain-tavily psycopg[binary] psycopg_pool python-dotenv tavily-python requests streamlit mcp
pip install -U "psycopg[binary,pool]" langgraph-checkpoint-postgres
```

### 3. Configure environment variables

Create a `.env` file in the project root with:

```env
GROQ_API_KEY=your_groq_api_key
TAVILY_API_KEY=your_tavily_api_key
AVIATIONSTACK_API_KEY=your_aviationstack_api_key
OPENWEATHER_API_KEY=your_openweathermap_api_key
DATABASE_URL=postgresql://postgres:password@localhost:5432/langgraph_memory_demo
```

### 4. Optional: PostgreSQL memory setup

If you want persistent LangGraph history, create a Postgres database and update `DATABASE_URL`:

```sql
CREATE DATABASE langgraph_memory_demo;
```

## Local MCP Servers

### AviationStack MCP

This repo includes `aviationstack-mcp/` as the local AviationStack MCP implementation.

To run the AviationStack MCP server:

```bash
cd aviationstack-mcp
python -m aviationstack_mcp mcp run
```

Ensure `AVIATIONSTACK_API_KEY` is set in `.env` or in the server environment.

### Weather MCP

Run the local OpenWeatherMap MCP server:

```bash
python custom_weather_mcp_server.py
```

The weather MCP exposes:

- `get_current_weather(city)`
- `get_forecast(city)`

## Usage

### CLI mode

```bash
python main.py
```

Provide a travel request when prompted. The app validates hotel booking details before generating a plan.

### Streamlit UI

```bash
streamlit run frontend.py
```

The Streamlit app lets you enter a trip description, watch the agent pipeline execute, and save the generated travel plan.

## Recommended query examples

- `Plan a complete 7-day Japan trip including flights, hotels and sightseeing under ₹2 lakhs from Delhi for 2 travellers starting 24 August 2026.`
- `Book a 5-day Paris itinerary from Mumbai for 4 people with hotel links and weather forecast.`

## Notes

- The hotel agent uses Tavily MCP search results and filters for accommodation-related pages.
- The itinerary agent combines flight, route, hotel, weather, and attraction data into a final travel plan.
- Attraction availability is checked via curated rules in `attraction_availability.py`.
- Generated travel plans are saved under `travel_plans/` as Markdown documents.

## Folder structure

- `main.py` — core LangGraph application
- `frontend.py` — Streamlit-powered UI
- `mcp_client.py` — MCP client setup and tool wrappers
- `custom_weather_mcp_server.py` — local OpenWeatherMap MCP server
- `travel_requirements.py` — hotel booking validation rules
- `attraction_availability.py` — curated attraction schedule rules
- `aviationstack-mcp/` — local AviationStack MCP package
- `travel_plans/` — saved generated plans

## Troubleshooting

- If PostgreSQL is unavailable, the app runs without saved memory.
- Confirm your `.env` file exists and contains the required API keys.
- Start the local AviationStack and weather MCP servers before using the app.
- Streamlit hides the menu and footer via custom CSS in `frontend.py`.

---

Happy planning! 🚀
