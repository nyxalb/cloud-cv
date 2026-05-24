import azure.functions as func
import azure.cosmos.cosmos_client as cosmos
import os, json

app = func.FunctionApp()

@app.route(route="counter", auth_level=func.AuthLevel.ANONYMOUS)
def counter(req: func.HttpRequest) -> func.HttpResponse:

    client = cosmos.CosmosClient.from_connection_string(
        os.environ["COSMOS_CONNECTION"]
    )
    container = (client
        .get_database_client("cvsite")
        .get_container_client("counter"))

    item = container.read_item(item="1", partition_key="1")
    item["count"] += 1
    container.replace_item(item="1", body=item)

    return func.HttpResponse(
        json.dumps({"count": item["count"]}),
        mimetype="application/json",
        headers={"Access-Control-Allow-Origin": "*"}
    )