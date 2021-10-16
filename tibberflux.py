import argparse
import json
import logging
from typing import Dict, List

from gql import Client, gql
from gql.transport.requests import RequestsHTTPTransport
from influxdb import InfluxDBClient, SeriesHelper

DEFAULT_CONF_FILENAME = "tibberflux.json"
DEFAULT_TIBBER_URL = "https://api.tibber.com/v1-beta/gql"


class TibberSeriesHelper(SeriesHelper):
    class Meta:
        series_name = "tibber"
        fields = ["cost", "consumption", "unitPrice", "unitPriceVAT"]
        tags = ["home"]


def get_influx_data(url: str, token: str):
    headers = {"Authorization": "Bearer " + token}
    transport = RequestsHTTPTransport(url=url, headers=headers)
    client = Client(transport=transport, fetch_schema_from_transport=True)
    query = gql(
        """
    {
      viewer {
        homes {
          consumption(resolution: HOURLY, last: 48, filterEmptyNodes: true) {
            nodes {
              from
              to
              cost
              unitPrice
              unitPriceVAT
              consumption
              consumptionUnit
            }
          }
        }
      }
    }

"""
    )

    response = client.execute(query)

    res = []
    home = 0
    for data in response["viewer"]["homes"]:
        for val in data["consumption"]["nodes"]:
            res.append({"home": home, **val})
        home += 1

    return res


def tibberflux(client, data: List[Dict]) -> None:

    for val in data:
        TibberSeriesHelper(
            time=val["from"],
            home=val["home"],
            cost=val["cost"],
            consumption=val["consumption"],
            unitPrice=val["unitPrice"],
            unitPriceVAT=val["unitPriceVAT"],
        )

    if client is not None:
        if data:
            TibberSeriesHelper.commit(client=client)
        else:
            logging.warning("No datapoints")
    else:
        print(TibberSeriesHelper._json_body_())


def main() -> None:
    """Main function"""

    parser = argparse.ArgumentParser(description="Tibber to InfluxDB exporter")
    parser.add_argument(
        "--conf",
        dest="conf_filename",
        default=DEFAULT_CONF_FILENAME,
        metavar="filename",
        help="configuration file",
        required=False,
    )
    parser.add_argument("--test", dest="test", action="store_true", help="Test mode")
    parser.add_argument(
        "--debug", dest="debug", action="store_true", help="Print debug information"
    )
    args = parser.parse_args()

    if args.debug:
        logging.basicConfig(level=logging.DEBUG)

    with open(args.conf_filename, "rt") as config_file:
        config = json.load(config_file)

    influx_config = config["influxdb"]
    tibber_config = config["tibber"]

    client = (
        InfluxDBClient(
            host=influx_config["hostname"],
            port=influx_config.get("port", 8086),
            username=influx_config["username"],
            password=influx_config["password"],
            ssl=True,
            verify_ssl=True,
            database=influx_config["database"],
        )
        if not args.test
        else None
    )

    tibber_url = tibber_config.get("url", DEFAULT_TIBBER_URL)
    tibber_token = tibber_config["token"]

    data = get_influx_data(url=tibber_url, token=tibber_token)
    tibberflux(client, data)


if __name__ == "__main__":
    main()
