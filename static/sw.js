self.addEventListener("push", (event) => {
  let payload = {};
  if (event.data) {
    try {
      payload = event.data.json();
    } catch {
      payload = { title: "Serenity Alerts", body: event.data.text() };
    }
  }
  const title = payload.title || "Serenity Alerts";
  const options = {
    body: payload.body || "New alert",
    icon: "/icon.svg",
    badge: "/icon.svg",
    data: { url: payload.url || "/", source_url: payload.source_url || "" }
  };
  event.waitUntil(self.registration.showNotification(title, options));
});

self.addEventListener("notificationclick", (event) => {
  event.notification.close();
  const url = event.notification.data?.url || "/";
  event.waitUntil(clients.openWindow(url));
});
