package com.example.beardetector

import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.content.IntentFilter
import android.os.Build
import android.os.Bundle
import android.widget.Button
import androidx.activity.enableEdgeToEdge
import androidx.annotation.RequiresApi
import androidx.appcompat.app.AppCompatActivity
import androidx.core.view.ViewCompat
import androidx.core.view.WindowInsetsCompat
import androidx.localbroadcastmanager.content.LocalBroadcastManager  // <-- Import nou
import com.google.android.gms.location.LocationServices
import com.google.android.gms.maps.CameraUpdateFactory
import com.google.android.gms.maps.GoogleMap
import com.google.android.gms.maps.OnMapReadyCallback
import com.google.android.gms.maps.SupportMapFragment
import com.google.android.gms.maps.model.BitmapDescriptorFactory
import com.google.android.gms.maps.model.LatLng
import com.google.android.gms.maps.model.Marker
import com.google.android.gms.maps.model.MarkerOptions

class MainActivity : AppCompatActivity(), OnMapReadyCallback {

    private var mMap: GoogleMap? = null
    private val locatieUrs = LatLng(45.602275, 25.549736)
    private val bearMarkers = mutableListOf<Marker>() // Lista de markere (urși)

    // Receiver pentru coordonate noi
    private val bearLocationReceiver = object : BroadcastReceiver() {
        override fun onReceive(context: Context?, intent: Intent?) {
            val lat = intent?.getDoubleExtra("latitude", 0.0) ?: 0.0
            val lng = intent?.getDoubleExtra("longitude", 0.0) ?: 0.0
            addBearMarker(lat, lng)
        }
    }

    @RequiresApi(Build.VERSION_CODES.M)
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        setContentView(R.layout.activity_main)

        // CERE PERMISIUNI SMS
        if (checkSelfPermission(android.Manifest.permission.RECEIVE_SMS) != android.content.pm.PackageManager.PERMISSION_GRANTED ||
            checkSelfPermission(android.Manifest.permission.READ_SMS) != android.content.pm.PackageManager.PERMISSION_GRANTED) {
            requestPermissions(
                arrayOf(
                    android.Manifest.permission.RECEIVE_SMS,
                    android.Manifest.permission.READ_SMS
                ), 1
            )
        }
        // PERMISIUNE LOCATIE
        if (checkSelfPermission(android.Manifest.permission.ACCESS_FINE_LOCATION) != android.content.pm.PackageManager.PERMISSION_GRANTED) {
            requestPermissions(
                arrayOf(android.Manifest.permission.ACCESS_FINE_LOCATION, android.Manifest.permission.ACCESS_COARSE_LOCATION),
                2
            )
        }

        // PERMISIUNE NOTIFICARI
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            if (checkSelfPermission(android.Manifest.permission.POST_NOTIFICATIONS)
                != android.content.pm.PackageManager.PERMISSION_GRANTED) {
                requestPermissions(
                    arrayOf(android.Manifest.permission.POST_NOTIFICATIONS),
                    3
                )
            }
        }

        // Înregistrează broadcast receiver pentru urși
        LocalBroadcastManager.getInstance(this).registerReceiver(
            bearLocationReceiver,
            IntentFilter("com.example.beardetector.NEW_BEAR_LOCATION")
        )

        ViewCompat.setOnApplyWindowInsetsListener(findViewById(R.id.main)) { v, insets ->
            val systemBars = insets.getInsets(WindowInsetsCompat.Type.systemBars())
            v.setPadding(systemBars.left, systemBars.top, systemBars.right, systemBars.bottom)
            insets
        }

        val mapFragment = supportFragmentManager.findFragmentById(R.id.map_fragment) as? SupportMapFragment
        mapFragment?.getMapAsync(this)
    }

    @RequiresApi(Build.VERSION_CODES.M)
    override fun onMapReady(map: GoogleMap?) {
        mMap = map

        // Activează "my location" dacă ai permis
        if (checkSelfPermission(android.Manifest.permission.ACCESS_FINE_LOCATION) == android.content.pm.PackageManager.PERMISSION_GRANTED) {
            mMap?.isMyLocationEnabled = true

            val fusedLocationProviderClient = LocationServices.getFusedLocationProviderClient(this)
            fusedLocationProviderClient.lastLocation.addOnSuccessListener { location ->
                if (location != null) {
                    val myLatLng = LatLng(location.latitude, location.longitude)
                    mMap?.moveCamera(CameraUpdateFactory.newLatLngZoom(myLatLng, 17f))
                } else {
                    mMap?.moveCamera(CameraUpdateFactory.newLatLngZoom(locatieUrs, 17f))
                }
            }
        } else {
            mMap?.moveCamera(CameraUpdateFactory.newLatLngZoom(locatieUrs, 17f))
        }

        // Butoane zoom
        val zoomInButton = findViewById<Button>(R.id.btnZoomIn)
        val zoomOutButton = findViewById<Button>(R.id.btnZoomOut)

        zoomInButton.setOnClickListener {
            val currentZoom = mMap?.cameraPosition?.zoom ?: 15f
            mMap?.animateCamera(CameraUpdateFactory.zoomTo(currentZoom + 1))
        }

        zoomOutButton.setOnClickListener {
            val currentZoom = mMap?.cameraPosition?.zoom ?: 15f
            mMap?.animateCamera(CameraUpdateFactory.zoomTo(currentZoom - 1))
        }
    }

    // Funcție pentru adăugare marker de urs (nu se șterg cele vechi!)
    private fun addBearMarker(lat: Double, lng: Double) {
        val location = LatLng(lat, lng)
        val marker = mMap?.addMarker(
            MarkerOptions()
                .position(location)
                .title("Alertă urs!")
                .icon(BitmapDescriptorFactory.fromResource(R.drawable.bear_icon2))
        )
        marker?.let { bearMarkers.add(it) }
        mMap?.animateCamera(CameraUpdateFactory.newLatLngZoom(location, 17f), 2000, null)
    }

    override fun onDestroy() {
        super.onDestroy()
        LocalBroadcastManager.getInstance(this).unregisterReceiver(bearLocationReceiver)
    }
}
