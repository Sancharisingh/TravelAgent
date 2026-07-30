
# LangGraph Multi-Agent Travel Booking System with Long-Term Memory

import os
import ast
import json
import re
from typing import TypedDict, Annotated
import operator
import asyncio
import psycopg
from psycopg.rows import dict_row
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.postgres import PostgresSaver
from langchain_core.messages import (
    AnyMessage,
    HumanMessage,
    AIMessage,
    SystemMessage,
)

from langchain_groq import ChatGroq

# from tools.tavily_tool import tavily_search

from mcp_client import tavily_mcp_search

from mcp_client import (
    tavily_mcp_search,
    get_airports,
    get_airlines,
    aviation_mcp_call,extract_destination,forecast_mcp_search,weather_mcp_search
)


#from tools.flight_tool import search_flights


from dotenv import load_dotenv
from attraction_availability import check_attraction_availability
from travel_requirements import check_hotel_pricing_requirements
#load_dotenv()
load_dotenv(override=True)
DATABASE_URL = os.getenv("DATABASE_URL")

HOTEL_KEYWORDS = (
    "hotel",
    "hotels",
    "homestay",
    "homestays",
    "resort",
    "resorts",
    "stay",
    "stays",
    "accommodation",
    "lodging",
    "guest house",
)

PRICE_PATTERN = re.compile(
    r"(?:₹|rs\.?|inr)\s?\d[\d,]*(?:\s?(?:per night|/night|night|total|onwards|taxes)?)?",
    re.IGNORECASE,
)

BOOKING_KEYWORDS = (
    "book",
    "booking",
    "reserve",
    "reservation",
    "rooms",
    "availability",
    "official",
)

BLOCKED_HOTEL_DOMAINS = (
    "bestbuy.com",
    "merriam-webster.com",
    "dictionary.cambridge.org",
    "facebook.com",
    "bestproducts.com",
)

# LLM
llm = ChatGroq(
    model="llama-3.3-70b-versatile"
)

# State
class TravelState(TypedDict):
    messages: Annotated[list[AnyMessage], operator.add]
    user_query: str
    route_plan: str
    flight_results: str
    hotel_results: str
    itinerary: str
    llm_calls: int
    weather_results: str
    attraction_results: str

# Flight Agent
# def flight_agent(state: TravelState):
#     query = state["user_query"]
#     flight_data = search_flights(query)
#     return {
#         "flight_results": flight_data,
#         "messages": [
#             AIMessage(content=f"Flight results fetched")
#         ],
#         "llm_calls": state.get("llm_calls", 0) + 1
#     }


# Flight Tool Router Prompt
FLIGHT_AGENT_PROMPT = """
You are a travel flight expert.

User Query:
{query}

Airport Information:
{airport_data}

Airline Information:
{airline_data}

Generate:

1. Likely departure airport
2. Likely arrival airport
3. Airlines serving this route
4. Typical flight duration
5. Estimated airfare range
6. Peak season pricing warning
7. Booking advice

Return concise travel guidance.
"""



# Flight Agent
def flight_agent(state: TravelState):
    print("\nINSIDE FLIGHT AGENT\n")

    query = state["user_query"]

    try:

        airports = asyncio.run(
            aviation_mcp_call(
                "list_airports"
            )
        )

        airlines = asyncio.run(
            aviation_mcp_call(
                "list_airlines"
            )
        )

        prompt = FLIGHT_AGENT_PROMPT.format(
            query=query,
            airport_data=str(airports)[:3000],
            airline_data=str(airlines)[:3000]
        )

        response = llm.invoke([
            SystemMessage(
                content="You are an expert travel flight planner."
            ),
            HumanMessage(content=prompt)
        ])

        flight_data = response.content

    except Exception as e:

        flight_data = f"Flight information unavailable: {str(e)}"

    return {
        "flight_results": flight_data,
        "messages": [
            AIMessage(
                content="Flight recommendations generated"
            )
        ],
        "llm_calls": state.get("llm_calls", 0) + 1
    }


def route_agent(state: TravelState):
    prompt = f"""
    You are an India travel route planner.

    User Query:
    {state['user_query']}

    Flight/transport context:
    {state['flight_results']}

    If the user gave a broad destination such as a state, choose practical cities/towns/areas to stay in.
    Build a route plan that includes:
    1. Selected stay locations in order
    2. Which dates or nights belong to each location
    3. Why each location is useful for this trip
    4. Hotel search keywords for each stay location

    Keep it concise and do not invent hotel names or prices.
    """

    response = llm.invoke([
        SystemMessage(content="You choose practical routes before hotel search."),
        HumanMessage(content=prompt),
    ])

    return {
        "route_plan": response.content,
        "messages": [
            AIMessage(content="Route plan generated")
        ],
        "llm_calls": state.get("llm_calls", 0) + 1,
    }




# Hotel Agent
def hotel_agent(state: TravelState):
    destination = extract_destination(state["user_query"])
    query = (
        f"book hotels homestays resorts with price per night and booking link for this route in India. "
        f"Broad destination: {destination}. Route plan: {state['route_plan']}. "
        f"Travel request: {state['user_query']}"
    )

    try:
        raw_results = asyncio.run(
            tavily_mcp_search(query)
        )
        hotel_results = format_hotel_results(destination, raw_results)
    except Exception as e:
        hotel_results = f"Hotel information unavailable: {str(e)}"

    return {
        "hotel_results": hotel_results,
        "messages": [
            AIMessage(content="Hotel information fetched")
        ],
        "llm_calls": state.get("llm_calls", 0) + 1
    }


def format_hotel_results(destination: str, raw_results) -> str:
    results = extract_search_results(raw_results)
    relevant_results = []

    for result in results:
        url = str(result.get("url", ""))
        title = str(result.get("title", ""))
        content = str(result.get("content", ""))
        haystack = f"{title} {content} {url}".lower()

        if any(domain in url.lower() for domain in BLOCKED_HOTEL_DOMAINS):
            continue

        if any(keyword in haystack for keyword in HOTEL_KEYWORDS):
            relevant_results.append(
                {
                    "title": title,
                    "url": url,
                    "content": content,
                }
            )

    if not relevant_results:
        return (
            f"No relevant hotel/accommodation search results were found for {destination}. "
            "The search returned unrelated pages, so the app should not invent hotel names. "
            "Try a more specific query such as 'hotels in Tawang' or 'homestays in Ziro'."
        )

    lines = [
        f"Hotel and stay options found for {destination}:",
        "Use only the listed source links for booking. Do not invent hotel prices.",
    ]

    for index, result in enumerate(relevant_results[:5], start=1):
        snippet = result["content"].strip()
        price = extract_price(snippet)
        booking_note = (
            "Booking/source link available"
            if has_booking_signal(result["title"], result["url"], snippet)
            else "Source link available; booking page not confirmed"
        )

        if len(snippet) > 450:
            snippet = f"{snippet[:450].rsplit(' ', 1)[0]}..."

        lines.extend(
            [
                "",
                f"{index}. Hotel/Stay: {result['title']}",
                f"   Booking link: {result['url']}",
                f"   Price from source: {price or 'Live exact price not available in search result'}",
                f"   Booking status: {booking_note}",
                f"   Source details: {snippet or 'No snippet returned.'}",
            ]
        )

    return "\n".join(lines)


def extract_price(text: str) -> str:
    match = PRICE_PATTERN.search(text)
    return match.group(0).strip() if match else ""


def has_booking_signal(title: str, url: str, content: str) -> bool:
    haystack = f"{title} {url} {content}".lower()
    return any(keyword in haystack for keyword in BOOKING_KEYWORDS)


def extract_search_results(raw_results) -> list[dict]:
    payload = raw_results

    if isinstance(payload, list) and payload and isinstance(payload[0], dict):
        text_payload = payload[0].get("text")
        if text_payload:
            payload = text_payload

    if isinstance(payload, str):
        try:
            payload = json.loads(payload)
        except json.JSONDecodeError:
            try:
                payload = ast.literal_eval(payload)
            except (ValueError, SyntaxError):
                return []

    if isinstance(payload, dict):
        results = payload.get("results", [])
        return results if isinstance(results, list) else []

    return []







def weather_agent(state: TravelState):

    city = extract_destination(state["user_query"])

    weather_data = asyncio.run(
        weather_mcp_search(city)
    )

    forecast_data = asyncio.run(
        forecast_mcp_search(city)
    )

    return {
        "weather_results": f"""
        Current Weather:
        {weather_data}

        Forecast:
        {forecast_data}
        """,
        "messages": [
            AIMessage(
                content="Weather information fetched"
            )
        ]
    }


def attraction_agent(state: TravelState):
    attraction_results = check_attraction_availability(state["user_query"])

    return {
        "attraction_results": attraction_results,
        "messages": [
            AIMessage(content="Trusted attraction availability checked")
        ],
    }





# Itinerary Agent
def itinerary_agent(state: TravelState):

    prompt = f"""
    Create a travel itinerary.
    User Query:
    {state['user_query']}

    Flight Results:
    {state['flight_results']}

    Hotel Results:
    {state['hotel_results']}

    Route Plan:
    {state['route_plan']}

    Weather Information:
    {state['weather_results']}

    Trusted Attraction Availability:
    {state['attraction_results']}

    Important:
    - In the Final Travel Plan, include a Hotel Options section.
    - For each hotel/stay, show the exact name, booking/source link, and exact price only if provided in Hotel Results.
    - If Hotel Results says "Live exact price not available", repeat that clearly. Do not write approximate hotel prices.
    - Do not invent hotel names, booking links, ratings, or prices.
    - Use the trusted attraction availability result when scheduling attractions.
    - If an attraction is closed on the requested date, move it to the suggested open day.
    - Put another listed open place/activity on the closed day.
    - If no trusted attraction-specific rule is found, say that official closure data was not available.
    - Do not claim closures from random websites or unsupported assumptions.
    """

    response = llm.invoke([
        SystemMessage(
            content="You are an expert travel planner"
        ),
        HumanMessage(content=prompt)
    ])

    return {
        "itinerary": response.content,
        "messages": [response],
        "llm_calls": state.get("llm_calls", 0) + 1
    }







graph = StateGraph(TravelState)

graph.add_node("flight_agent", flight_agent)
graph.add_node("route_agent", route_agent)
graph.add_node("hotel_agent", hotel_agent)
graph.add_node("weather_agent", weather_agent)
graph.add_node("attraction_agent", attraction_agent)
graph.add_node("itinerary_agent", itinerary_agent)


graph.add_edge(START, "flight_agent")
graph.add_edge("flight_agent", "route_agent")
graph.add_edge("route_agent", "hotel_agent")
graph.add_edge("hotel_agent", "weather_agent")
graph.add_edge("weather_agent", "attraction_agent")
graph.add_edge("attraction_agent", "itinerary_agent")
graph.add_edge("itinerary_agent", END)


# Persistent connection so both CLI and Streamlit can share the compiled app
CHECKPOINTER_STATUS = "PostgreSQL memory enabled."

try:
    _conn = psycopg.connect(DATABASE_URL, autocommit=True, row_factory=dict_row)
    checkpointer = PostgresSaver(_conn)
    checkpointer.setup()
    app = graph.compile(checkpointer=checkpointer)
except psycopg.OperationalError as exc:
    CHECKPOINTER_STATUS = (
        "PostgreSQL memory unavailable. The app is running without saved chat memory. "
        f"Reason: {exc}"
    )
    app = graph.compile()


if __name__ == "__main__":
    # config = {
    #     "configurable": {
    #         "thread_id": "user_aarohi"
    #     }
    # }

    # every run starts fresh.
    import uuid
    config = {
        "configurable": {
            "thread_id": str(uuid.uuid4())
        }
    }


    user_input = input("Enter travel request: ")
    requirement_check = check_hotel_pricing_requirements(user_input)

    if not requirement_check.is_complete:
        print(requirement_check.message)
        raise SystemExit(0)

    result = app.invoke(
        {
            "messages": [
                HumanMessage(content=user_input)
            ],
            "user_query": user_input,
            "route_plan": "",
            "flight_results": "",
            "hotel_results": "",
            "itinerary": "",
            "llm_calls": 0,
            "weather_results": "",
            "attraction_results": "",
        },
        config=config
    )

    print("\nFINAL RESPONSE:\n")

    for msg in result["messages"]:
        print(msg.content)
