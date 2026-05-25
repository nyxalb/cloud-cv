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

    # Update count
    counter_container = db.get_container_client("counter")
    item = counter_container.read_item(item="1", partition_key="1")
    item["count"] += 1
    counter_container.replace_item(item="1", body=item)

    # Get IP from browser
    ip = req.params.get('ip', 'Unknown')

    # Do geo lookup server-side in Azure Function
    country, city, country_code = 'Unknown', 'Unknown', '??'
    if ip and ip != 'Unknown':
        try:
            url = f"https://freeipapi.com/api/json/{ip}"
            r = urllib.request.Request(url, headers={
                'User-Agent': 'Mozilla/5.0',
                'Accept': 'application/json'
            })
            with urllib.request.urlopen(r, timeout=5) as resp:
                geo = json.loads(resp.read())
            country = geo.get('countryName', 'Unknown')
            city = geo.get('cityName', 'Unknown')
            country_code = geo.get('countryCode', '??')
        except Exception as e:
            pass

    # Store privately in Cosmos DB
    visits_container = db.get_container_client("visits")
    visits_container.create_item({
        "id": datetime.utcnow().strftime('%Y%m%d%H%M%S%f'),
        "ip": ip,
        "country": country,
        "city": city,
        "countryCode": country_code,
        "timestamp": datetime.utcnow().isoformat(),
        "partition": "visit"
    })

    return func.HttpResponse(
        json.dumps({"count": item["count"]}),
        mimetype="application/json",
        headers={"Access-Control-Allow-Origin": "*"}
    )
@app.route(route="visitormap", auth_level=func.AuthLevel.ANONYMOUS)
def visitormap(req: func.HttpRequest) -> func.HttpResponse:

    client = cosmos.CosmosClient.from_connection_string(
        os.environ["COSMOS_CONNECTION"]
    )
    container = client.get_database_client("cvsite").get_container_client("visits")

    # Count visits per country
    query = """
        SELECT c.country, c.countryCode, COUNT(1) as visits
        FROM c
        WHERE c.country != 'Unknown'
        GROUP BY c.country, c.countryCode
    """
    try:
        countries = list(container.query_items(
            query=query,
            enable_cross_partition_query=True
        ))
    except:
        countries = []

    return func.HttpResponse(
        json.dumps({"countries": countries}),
        mimetype="application/json",
        headers={"Access-Control-Allow-Origin": "*"}
    )