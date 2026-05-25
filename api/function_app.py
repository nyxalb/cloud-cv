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

    # Get all visits with known countries
    query = "SELECT c.country, c.countryCode FROM c WHERE c.country != 'Unknown'"
    try:
        items = list(container.query_items(
            query=query,
            enable_cross_partition_query=True
        ))
        # Count manually
        counts = {}
        for item in items:
            key = item['countryCode']
            if key not in counts:
                counts[key] = {'country': item['country'], 'countryCode': key, 'visits': 0}
            counts[key]['visits'] += 1
        countries = list(counts.values())
    except Exception as e:
        countries = []

    return func.HttpResponse(
        json.dumps({"countries": countries}),
        mimetype="application/json",
        headers={"Access-Control-Allow-Origin": "*"}
    )
@app.route(route="contact", auth_level=func.AuthLevel.ANONYMOUS, methods=["POST"])
def contact(req: func.HttpRequest) -> func.HttpResponse:

    try:
        body = req.get_json()
        name = body.get('name', 'Unknown')
        email = body.get('email', 'Unknown')
        message = body.get('message', '')

        from azure.communication.email import EmailClient

        client = EmailClient.from_connection_string(
            os.environ["COMMUNICATION_CONNECTION"]
        )

        # Get your sender address from Azure managed domain
        sender = os.environ["SENDER_ADDRESS"]

        message_body = f"""
New contact form submission from mariokola.co.uk

Name:    {name}
Email:   {email}

Message:
{message}

---
Sent from your CV site contact form
        """

        email_message = {{
            "senderAddress": sender,
            "recipients": {{
                "to": [{{"address": "mario@mariokola.co.uk"}}]
            }},
            "content": {{
                "subject": f"CV Site — Message from {name}",
                "plainText": message_body
            }}
        }}

        poller = client.begin_send(email_message)
        poller.result()

        return func.HttpResponse(
            json.dumps({{"success": True, "message": "Email sent!"}}),
            mimetype="application/json",
            headers={{"Access-Control-Allow-Origin": "*"}}
        )

    except Exception as e:
        return func.HttpResponse(
            json.dumps({{"success": False, "error": str(e)}}),
            mimetype="application/json",
            status_code=500,
            headers={{"Access-Control-Allow-Origin": "*"}}
        )