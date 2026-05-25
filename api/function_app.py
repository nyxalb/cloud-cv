import azure.functions as func
import azure.cosmos.cosmos_client as cosmos
import os, json, urllib.request
from datetime import datetime

app = func.FunctionApp()

@app.route(route="counter", auth_level=func.AuthLevel.ANONYMOUS)
def counter(req: func.HttpRequest) -> func.HttpResponse:

    client = cosmos.CosmosClient.from_connection_string(
        os.environ["COSMOS_CONNECTION"]
    )
    db = client.get_database_client("cvsite")

    # Update visit count
    counter_container = db.get_container_client("counter")
    item = counter_container.read_item(item="1", partition_key="1")
    item["count"] += 1
    counter_container.replace_item(item="1", body=item)

    # Get IP from frontend
    ip = req.params.get('ip', 'Unknown')

    # Get location from IP
    try:
        geo_url = f"https://ipapi.co/{ip}/json/"
        geo_req = urllib.request.Request(
            geo_url, headers={'User-Agent': 'Mozilla/5.0'}
        )
        with urllib.request.urlopen(geo_req, timeout=5) as response:
            geo = json.loads(response.read())
        country = geo.get('country_name', 'Unknown')
        city = geo.get('city', 'Unknown')
        country_code = geo.get('country_code', '??')
    except:
        country, city, country_code = 'Unknown', 'Unknown', '??'

    # Store visit — IP is private, only in DB
    visits_container = db.get_container_client("visits")
    visit = {
        "id": str(datetime.utcnow().timestamp()).replace('.', ''),
        "country": country,
        "city": city,
        "countryCode": country_code,
        "timestamp": datetime.utcnow().isoformat(),
        "ip": ip  # private — only stored in DB, never sent to frontend
    }
    visits_container.create_item(visit)

    # Return public data only — NO ip in response
    return func.HttpResponse(
        json.dumps({
            "count": item["count"],
            "country": country,
            "city": city,
            "countryCode": country_code
        }),
        mimetype="application/json",
        headers={"Access-Control-Allow-Origin": "*"}
    )


@app.route(route="visits", auth_level=func.AuthLevel.ANONYMOUS)
def visits(req: func.HttpRequest) -> func.HttpResponse:

    client = cosmos.CosmosClient.from_connection_string(
        os.environ["COSMOS_CONNECTION"]
    )
    container = client.get_database_client("cvsite").get_container_client("visits")

    # Return public data only — NO ip field returned
    query = """SELECT TOP 20 c.country, c.city, c.countryCode, c.timestamp
               FROM c ORDER BY c._ts DESC"""
    items = list(container.query_items(
        query=query, enable_cross_partition_query=True
    ))

    # Count visits per country for the public map
    country_query = """SELECT c.country, c.countryCode, COUNT(1) as visits
                       FROM c GROUP BY c.country, c.countryCode"""
    country_counts = list(container.query_items(
        query=country_query, enable_cross_partition_query=True
    ))

    return func.HttpResponse(
        json.dumps({
            "recent": items,
            "countries": country_counts
        }),
        mimetype="application/json",
        headers={"Access-Control-Allow-Origin": "*"}
    )