namespace py store

struct Item {
  1: string slug,
  2: string name,
  3: string description,
  4: optional i64 price
}

service Store {
  string createBasket(),
  void addToBasket(1: string basketId, 2: string itemSlug),
  list<string> getBasket(1: string basketId),
  list<Item> getInventory(),
  string pay(1: string basketId, 2: i64 total)
}

