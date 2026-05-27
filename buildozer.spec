[app]
title = Enemy Detector AI
package.name = enemydetector
package.domain = com.detector
source.dir = .
source.include_exts = py,png,jpg,kv,atlas
version = 1.0
requirements = python3,kivy,opencv,numpy,plyer,pyjnius
orientation = portrait
osx.python_version = 3
osx.kivy_version = 2.3.0
fullscreen = 1
android.permissions = INTERNET,SYSTEM_ALERT_WINDOW,FOREGROUND_SERVICE,FOREGROUND_SERVICE_MEDIA_PROJECTION,MEDIA_PROJECTION
android.api = 33
android.minapi = 26
android.ndk = 25b
android.sdk = 33
android.gradle_dependencies = androidx.core:core:1.10.0
android.add_src = java/
android.arch = arm64-v8a
android.allow_backup = True
android.logo.filename = %(source.dir)s/icon.png
android.presplash_color = #1a1a1a
android.statusbar_color = #1a1a1a
p4a.branch = develop
p4a.bootstrap = sdl2

[buildozer]
log_level = 2
warn_on_root = 1
