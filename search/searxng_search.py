import argparse, os, requests

import urllib.parse


def parse_args():
    parser = argparse.ArgumentParser(description="Test searxng search engine")
    parser.add_argument("--query", type=str, nargs='+', help="query to search")
    parser.add_argument("--number_of_results", type=int, default=10, help="number of results to return")
    parser.add_argument("--target_domain", type=str, default="", help="target domain to search")
    args = parser.parse_args()
    return args

def build_query(queries: list):
    # query = " ".join(queries)
    # encoded_query = urllib.parse.quote(query, safe='\u4e00-\u9fff')
    encoded_query = "+".join(queries)
    return encoded_query

def build_query_target_domain(query: str, target_domain: str):
    # query = f"{query} site:{target_domain}"
    # encoded_query = urllib.parse.quote(query, safe='\u4e00-\u9fff')
    encoded_query = f"{query} site:{target_domain}"
    return encoded_query

def web_search(query, number_of_results=-1):
    base_url = os.getenv("SEARCH_HOST")
    # print(f"Searching for: {query}")
    if number_of_results == -1:
        url = f"{base_url}/search?q={query}&format=json"
    else:
        url = f"{base_url}/search?q={query}&number_of_results={number_of_results}&format=json"
    response = requests.get(url)
    results = response.json()
    # # result_num1 = results["number_of_results"]
    # result_detail = results["results"]
    # result_num = len(result_detail)
    # # print(f"Number of results: {result_num1}/{result_num2}")
    # print(f"Number of results: {result_num}")
    # print("Details:")
    # for i, result in enumerate(result_detail):
    #     print(f"{i+1}.")
    #     print(f"{result}")
    #     # print(f"{result['title']} - {result['url']} - {result['publishedDate']}")
    #     # print(f"{result['content']}")
    return results

def sort_results(results, sort_by='score'):
    if sort_by not in ['score', 'publishedDate']:
        print(f"Invalid sort_by value: {sort_by}")
        return results
    # 按指定字段降序排序
    sorted_results = sorted(results, key=lambda x: x[sort_by], reverse=True)
    return sorted_results
        
if __name__ == "__main__":
    args = parse_args()
    # check if query is provided
    if len(args.query) == 0:
        print("Please provide a query")
        exit(1)
    # build query
    if len(args.query) > 1:
        query = build_query(args.query)
    else:
        query = args.query[0]

    if args.target_domain:
        query = build_query_target_domain(query, args.target_domain)

    res = web_search(query, args.number_of_results)
