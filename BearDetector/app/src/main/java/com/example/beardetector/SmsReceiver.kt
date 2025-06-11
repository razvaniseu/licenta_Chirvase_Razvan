package com.example.beardetector

import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.os.Build
import android.os.Bundle
import android.telephony.SmsMessage
import androidx.annotation.RequiresApi
import androidx.localbroadcastmanager.content.LocalBroadcastManager   // <-- Adaugă acest import
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import androidx.core.app.NotificationCompat

class SmsReceiver : BroadcastReceiver() {
    @RequiresApi(Build.VERSION_CODES.M)
    override fun onReceive(context: Context, intent: Intent) {
        val bundle: Bundle? = intent.extras
        bundle?.let {
            val pdus = it["pdus"] as? Array<*>
            pdus?.forEach { pdu ->
                val format = it.getString("format")
                val sms = if (format != null)
                    SmsMessage.createFromPdu(pdu as ByteArray, format)
                else
                    SmsMessage.createFromPdu(pdu as ByteArray)
                val messageBody = sms.messageBody

                // Caută coordonatele în text (ex: "Locatie: 45.12345, 25.12345")
                val regex = Regex("""(-?\d+\.\d+),\s*(-?\d+\.\d+)""")
                val matchResult = regex.find(messageBody)

                if (matchResult != null) {
                    val (lat, lng) = matchResult.destructured
                    val latitude = lat.toDouble()
                    val longitude = lng.toDouble()

                    // 🟢 AICI adaugi Toast-ul:
                    android.widget.Toast.makeText(
                        context,
                        "Urs detectat la: $latitude, $longitude",
                        android.widget.Toast.LENGTH_LONG
                    ).show()

                    // 2. Notificare push
                    val channelId = "bear_alert_channel"
                    val notificationManager = context.getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager

                    // Creează canalul de notificări pentru Android 8+
                    if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
                        val channel = NotificationChannel(
                            channelId,
                            "Bear Alerts",
                            NotificationManager.IMPORTANCE_HIGH
                        ).apply {
                            description = "Notificări pentru alerte de urs"
                        }
                        notificationManager.createNotificationChannel(channel)
                    }

                    val intentToOpen = Intent(context, MainActivity::class.java).apply {
                        flags = Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TASK
                    }
                    val pendingIntent = PendingIntent.getActivity(
                        context, 0, intentToOpen,
                        PendingIntent.FLAG_IMMUTABLE or PendingIntent.FLAG_UPDATE_CURRENT
                    )

                    val notification = NotificationCompat.Builder(context, channelId)
                        .setSmallIcon(R.drawable.notificare_urs24)
                        .setContentTitle("Alertă URS!")
                        .setContentText("Urs detectat la: $latitude, $longitude")
                        .setPriority(NotificationCompat.PRIORITY_HIGH)
                        .setAutoCancel(true)
                        .setContentIntent(pendingIntent)
                        .build()

                    notificationManager.notify(System.currentTimeMillis().toInt(), notification)



                    // Trimite broadcast cu coordonatele detectate către MainActivity PRIN LocalBroadcastManager
                    val mapIntent = Intent("com.example.beardetector.NEW_BEAR_LOCATION")
                    mapIntent.putExtra("latitude", latitude)
                    mapIntent.putExtra("longitude", longitude)
                    LocalBroadcastManager.getInstance(context).sendBroadcast(mapIntent)
                }
            }
        }
    }
}
