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

    counter_container = db.get_container_client("counter")
    item = counter_container.read_item(item="1", partition_key="1")
    item["count"] += 1
    counter_container.replace_item(item="1", body=item)

    ip = req.params.get('ip') or req.headers.get('X-Forwarded-For', '').split(',')[0].strip()
    if not ip or ip == '127.0.0.1':
        ip = '8.8.8.8'

try:
    geo_url = f"https://ipapi.co/{ip}/json/"
    req2 = urllib.request.Request(geo_url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req2, timeout=5) as response:
        geo = json.loads(response.read())
    country = geo.get('country_name', 'Unknown')
    city = geo.get('city', 'Unknown')
    country_code = geo.get('country_code', '??')
except:
    country, city, country_code = 'Unknown', 'Unknown', '??'

    visits_container = db.get_container_client("visits")
    visit = {
        "id": str(datetime.utcnow().timestamp()).replace('.', ''),
        "country": country,
        "city": city,
        "countryCode": country_code,
        "timestamp": datetime.utcnow().isoformat()
    }
    visits_container.create_item(visit)

    return func.HttpResponse(
        json.dumps({
            "count": item["count"],
            "location": {"country": country, "city": city, "countryCode": country_code}
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

    query = "SELECT TOP 10 c.country, c.city, c.countryCode, c.timestamp FROM c ORDER BY c.timestamp DESC"
    items = list(container.query_items(query=query, enable_cross_partition_query=True))

    return func.HttpResponse(
        json.dumps({"visits": items}),
        mimetype="application/json",
        headers={"Access-Control-Allow-Origin": "*"}
    )

