from locust import HttpUser, task, between

class URLShortenerLoadTest(HttpUser):
    # Wait between 100ms and 1000ms between tasks
    wait_time = between(0.1, 1.0)
    short_code = None

    def on_start(self):
        """
        Runs once when a virtual user starts. It creates a dummy URL
        so the user can load test redirect actions against a valid code.
        """
        payload = {"original_url": "https://example.com"}
        # Disable redirect following on url creation
        with self.client.post("/api/v1/urls/", json=payload, catch_response=True) as response:
            if response.status_code == 201:
                data = response.json()
                self.short_code = data["short_code"]
            else:
                response.failure(f"Setup failed: could not create test URL (status {response.status_code})")

    @task
    def redirect_url(self):
        """Benchmark the redirection latency of the short code."""
        if self.short_code:
            # allow_redirects=False is critical to avoid benchmarking/spamming the target website
            self.client.get(
                f"/{self.short_code}",
                name="/{short_code}",
                allow_redirects=False,
            )
