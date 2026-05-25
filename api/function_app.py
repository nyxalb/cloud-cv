import azure.functions as func
import azure.cosmos.cosmos_client as cosmos
import os, json
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

    # Read what frontend sent
    ip = req.params.get('ip', 'Unknown')
    country = req.params.get('country', 'Unknown')
    city = req.params.get('city', 'Unknown')
    country_code = req.params.get('cc', '??')

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

    # Return ONLY the count to the public
    return func.HttpResponse(
        json.dumps({"count": item["count"]}),
        mimetype="application/json",
        headers={"Access-Control-Allow-Origin": "*"}
    )