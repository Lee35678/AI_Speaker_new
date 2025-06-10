# Android Client for AI Speaker

This folder provides a minimal example for receiving fall detection alerts via Firebase Cloud Messaging (FCM).

## 1. Project Setup

1. Create a new Android project in **Android Studio** using Kotlin.
2. Register the app in the Firebase console and download the `google-services.json` file.
3. Place `google-services.json` in the app module and add the Google services plugin in `build.gradle`.
4. Add the dependency for Firebase Messaging:

```gradle
implementation 'com.google.firebase:firebase-messaging:23.4.1'
```

## 2. Subscribe to `fallAlerts`

Create `MyFirebaseMessagingService.kt` under `app/src/main/java/<your package>/`. Include
your package statement at the top of the file:

```kotlin
package com.android.fallalert  // replace with your app's package

import com.google.firebase.messaging.FirebaseMessagingService
import com.google.firebase.messaging.RemoteMessage
import com.google.firebase.messaging.FirebaseMessaging
import android.app.NotificationChannel
import android.app.NotificationManager
import android.os.Build
import androidx.core.app.NotificationCompat

class MyFirebaseMessagingService : FirebaseMessagingService() {
    override fun onNewToken(token: String) {
        // Called if a new FCM registration token is generated
        FirebaseMessaging.getInstance().subscribeToTopic("fallAlerts")
    }

    override fun onMessageReceived(remoteMessage: RemoteMessage) {
        val title = remoteMessage.notification?.title ?: "Fall Alert"
        val body = remoteMessage.notification?.body ?: "A fall event was detected"
        showNotification(title, body)
    }

    private fun showNotification(title: String, body: String) {
        val channelId = "fall_alerts"
        val manager = getSystemService(NOTIFICATION_SERVICE) as NotificationManager
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val channel = NotificationChannel(channelId, "Fall Alerts", NotificationManager.IMPORTANCE_HIGH)
            manager.createNotificationChannel(channel)
        }
        val notification = NotificationCompat.Builder(this, channelId)
            .setContentTitle(title)
            .setContentText(body)
            .setSmallIcon(android.R.drawable.ic_dialog_alert)
            .build()
        manager.notify(0, notification)
    }
}
```

Update `AndroidManifest.xml` to register the service:

```xml
<service
    android:name=".MyFirebaseMessagingService"
    android:exported="false">
    <intent-filter>
        <action android:name="com.google.firebase.MESSAGING_EVENT" />
    </intent-filter>
</service>
```

Make sure the `package` attribute in the `<manifest>` tag matches the package
name used in `MyFirebaseMessagingService.kt`.

## 3. Build and Run

1. Sync Gradle and build the project in Android Studio.
2. Install the app on your Android device or emulator.
3. When the Python `fall_module.py` calls `send_fcm_alert()`, you should receive a push notification.

## Additional Tasks

* Ensure environment variable `FCM_SERVER_KEY` is set in your Python environment so `fcm_module.py` can send notifications.
* For release builds, configure your own application ID, signing, and any extra permissions your project requires.
