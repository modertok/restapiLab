"""
Locust load test — Library API, endpoint: GET /books/

Tested endpoint: GET /books/
  Variations:
    • default params        (weight 5)
    • with pagination       (weight 3)
    • sorted by year        (weight 2)
    • filtered by status    (weight 2)
    • combined params       (weight 1)

Run via Docker:   docker compose up
Run headless:     docker compose --profile headless up locust-headless
"""
import random

from locust import HttpUser, between, task


class BooksAPIUser(HttpUser):
    """Simulates a client hitting GET /books/ with various query strings."""

    wait_time = between(1, 3)

    # ── Tasks ──────────────────────────────────────────────────────────────

    @task(5)
    def get_books_default(self):
        """Plain GET /books/ — most common access pattern."""
        with self.client.get(
            "/books/",
            name="GET /books/ [default]",
            catch_response=True,
        ) as resp:
            if resp.status_code == 200:
                data = resp.json()
                if "items" in data and "total" in data:
                    resp.success()
                else:
                    resp.failure("Response missing 'items' or 'total'")
            else:
                resp.failure(f"HTTP {resp.status_code}")

    @task(3)
    def get_books_paginated(self):
        """GET /books/ with limit + offset (simulates pagination)."""
        limit = random.choice([5, 10, 20])
        offset = random.randint(0, 10) * limit
        with self.client.get(
            f"/books/?limit={limit}&offset={offset}",
            name="GET /books/ [paginated]",
            catch_response=True,
        ) as resp:
            if resp.status_code == 200:
                resp.success()
            else:
                resp.failure(f"HTTP {resp.status_code}")

    @task(2)
    def get_books_sorted_by_year(self):
        """GET /books/ sorted by publication year."""
        with self.client.get(
            "/books/?sort_by=year",
            name="GET /books/ [sort_by=year]",
            catch_response=True,
        ) as resp:
            if resp.status_code == 200:
                resp.success()
            else:
                resp.failure(f"HTTP {resp.status_code}")

    @task(2)
    def get_books_filtered_by_status(self):
        """GET /books/ filtered by availability status."""
        status = random.choice(["available", "issued"])
        with self.client.get(
            f"/books/?status={status}",
            name="GET /books/ [status filter]",
            catch_response=True,
        ) as resp:
            if resp.status_code == 200:
                resp.success()
            else:
                resp.failure(f"HTTP {resp.status_code}")

    @task(1)
    def get_books_combined(self):
        """GET /books/ with filter + sort + pagination combined."""
        status = random.choice(["available", "issued"])
        sort = random.choice(["title", "year"])
        limit = random.choice([5, 10])
        with self.client.get(
            f"/books/?status={status}&sort_by={sort}&limit={limit}&offset=0",
            name="GET /books/ [combined]",
            catch_response=True,
        ) as resp:
            if resp.status_code == 200:
                resp.success()
            else:
                resp.failure(f"HTTP {resp.status_code}")
