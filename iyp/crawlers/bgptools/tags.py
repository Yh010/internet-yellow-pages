import sys
import logging
import requests
from datetime import datetime, time, timezone
from iyp import BaseCrawler

#curl -s https://bgp.tools/asns.csv | head -n 5
URL = 'https://bgp.tools/tags/'
ORG = 'BGP.Tools'
NAME = 'bgptools.tags'

TAGS = {
        'cdn': 'Content Delivery Network', 
        'dsl': 'Home ISP', 
        'a10k': 'Alexa 10k Host', 
        'icrit': 'Internet Critical Infra', 
        'tor': 'ToR Services', 
        'anycast': 'Anycast', 
        'perso': 'Personal ASN', 
        'ddosm': 'DDoS Mitigation',
        'vpn': 'VPN Host',
        'vpsh': 'Server Hosting',
        'uni': 'Academic',
        'gov': 'Government',
        'event': 'Event',
        'mobile': 'Mobile Data/Carrier',
        'satnet': 'Satellite Internet',
        'biznet': 'Business Broadband',
        'corp': 'Corporate/Enterprise'
       }

class Crawler(BaseCrawler):
    def __init__(self, organization, url, name):

        self.headers = {
            'user-agent': 'IIJ/Internet Health Report - admin@ihr.live'
        }

        super().__init__(organization, url, name)

    def run(self):
        """Fetch the AS name file from BGP.Tools website and process lines one by one"""

        for tag, label in TAGS.items():
            url = URL+tag+'.csv'
            # Reference information for data pushed to the wikibase
            self.reference = {
                'reference_org': ORG,
                'reference_url': url,
                'reference_name': NAME,
                'reference_time': datetime.combine(datetime.utcnow(), time.min, timezone.utc)
                }

            req = requests.get(url, headers=self.headers)
            if req.status_code != 200:
                print(req.text)
                sys.exit('Error while fetching AS names')

            self.tag_qid = self.iyp.get_node('Tag', {'label': label}, create=True)
            for line in req.text.splitlines():
                # skip header
                if line.startswith('asn'):
                    continue

                # Parse given line to get ASN, name, and country code 
                asn, _, _ = line.partition(',')
                asn_qid = self.iyp.get_node('AS', {'asn': asn[2:]}, create=True)
                statements = [ [ 'CATEGORIZED', self.tag_qid, self.reference ] ] # Set AS name

                try:
                    # Update AS name and country
                    self.iyp.add_links(asn_qid, statements)

                except Exception as error:
                    # print errors and continue running
                    print('Error for: ', line)
                    print(error)


if __name__ == '__main__':

    scriptname = sys.argv[0].replace('/','_')[0:-3]
    FORMAT = '%(asctime)s %(processName)s %(message)s'
    logging.basicConfig(
            format=FORMAT, 
            filename='log/'+scriptname+'.log',
            level=logging.INFO, 
            datefmt='%Y-%m-%d %H:%M:%S'
            )
    logging.info("Start: %s" % sys.argv)

    asnames = Crawler(ORG, URL, NAME)
    asnames.run()
    asnames.close()

    logging.info("End: %s" % sys.argv)
