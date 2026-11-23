"""Run once from a scheduler, or poll selected sources in a dedicated worker process."""
import argparse
import json
import time
from .listing_store import FirestoreListingStore
from .listing_service import ListingService
from .listing_collection import SourceCollector


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--interval', type=int, default=0, help='Seconds between runs, minimum 3600; omit for one run.')
    args = parser.parse_args()
    if args.interval and args.interval < 3600:
        parser.error('Use at least 3600 seconds between collection runs.')
    collector = SourceCollector(ListingService(FirestoreListingStore()))
    while True:
        print(json.dumps(collector.run()), flush=True)
        if not args.interval: break
        time.sleep(args.interval)


if __name__ == '__main__': main()
