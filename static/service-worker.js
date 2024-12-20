self.addEventListener('push', function (event) {
    const data = event.data.json();
    console.log('Push received:', data);

    const options = {
        body: data.body,
        icon: '/static/img/icon.png', // Path to your icon
        badge: '/static/img/badge.png' // Path to your badge
    };

    event.waitUntil(self.registration.showNotification(data.title, options));
});
