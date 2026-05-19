import requests
import json

base_url = "https://grupoanimal.mx"
endpoint = "/api/graphql"

def graphql_request(query: str) -> dict:
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0"
    }
    payload = {"query": query}
    response = requests.post(f"{base_url}{endpoint}", json=payload, headers=headers)
    response.raise_for_status()
    return response.json()

# Example: Get homepage articles
homepage_query = """
{
  apHomepage {
    animalPolTicoHome {
      notasDelHomepageAP {
        nodes {
          __typename
          databaseId
          slug
          date
          uri
          title
        }
      }
    }
  }
}
"""
result = graphql_request(homepage_query)
print(json.dumps(result, indent=2))
