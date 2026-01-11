from pprint import pprint
from gne import GeneralNewsExtractor
import requests




if __name__ == '__main__':
    html = requests.get("https://www.siwei.io/fusion-graphrag-2025/").text
    extractor = GeneralNewsExtractor()
    result = extractor.extract(html, noise_node_list=['//div[@class="comment-list"]'])
    pprint(result)
