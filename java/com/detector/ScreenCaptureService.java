package com.detector;

import android.app.Activity;
import android.app.Service;
import android.content.Context;
import android.content.Intent;
import android.graphics.Bitmap;
import android.graphics.PixelFormat;
import android.hardware.display.DisplayManager;
import android.hardware.display.VirtualDisplay;
import android.media.Image;
import android.media.ImageReader;
import android.media.projection.MediaProjection;
import android.media.projection.MediaProjectionManager;
import android.os.Handler;
import android.os.HandlerThread;
import android.os.IBinder;
import android.util.DisplayMetrics;
import java.io.FileOutputStream;
import java.nio.ByteBuffer;

public class ScreenCaptureService extends Service {
    private MediaProjection projection;
    private VirtualDisplay virtualDisplay;
    private ImageReader imageReader;
    private HandlerThread handlerThread;
    private Bitmap latestBitmap;
    private int screenWidth, screenDensity, screenHeight;

    @Override
    public int onStartCommand(Intent intent, int flags, int startId) {
        int resultCode = intent.getIntExtra("resultCode", -1);
        Intent data = intent.getParcelableExtra("data");

        screenWidth = intent.getIntExtra("width", 1080);
        screenHeight = intent.getIntExtra("height", 2400);
        screenDensity = intent.getIntExtra("density", 440);

        handlerThread = new HandlerThread("ScreenCapture");
        handlerThread.start();
        Handler handler = new Handler(handlerThread.getLooper());

        MediaProjectionManager manager = (MediaProjectionManager)
                getSystemService(Context.MEDIA_PROJECTION_SERVICE);
        projection = manager.getMediaProjection(resultCode, data);

        imageReader = ImageReader.newInstance(
                screenWidth, screenHeight, PixelFormat.RGBA_8888, 2);
        imageReader.setOnImageAvailableListener(reader -> {
            Image image = reader.acquireLatestImage();
            if (image != null) {
                Image.Plane[] planes = image.getPlanes();
                ByteBuffer buffer = planes[0].getBuffer();
                latestBitmap = Bitmap.createBitmap(
                        screenWidth, screenHeight, Bitmap.Config.ARGB_8888);
                latestBitmap.copyPixelsFromBuffer(buffer);
                saveBitmap(latestBitmap);
                image.close();
            }
        }, handler);

        projection.registerCallback(new MediaProjection.Callback() {
            @Override
            public void onStop() {
                stopCapture();
            }
        }, handler);

        virtualDisplay = projection.createVirtualDisplay(
                "ScreenCapture",
                screenWidth, screenHeight, screenDensity,
                DisplayManager.VIRTUAL_DISPLAY_FLAG_AUTO_MIRROR,
                imageReader.getSurface(), null, handler);

        return START_STICKY;
    }

    private void saveBitmap(Bitmap bitmap) {
        try {
            FileOutputStream fos = new FileOutputStream("/sdcard/screen.png");
            bitmap.compress(Bitmap.CompressFormat.PNG, 80, fos);
            fos.close();
        } catch (Exception ignored) {}
    }

    private void stopCapture() {
        if (virtualDisplay != null) { virtualDisplay.release(); virtualDisplay = null; }
        if (imageReader != null) { imageReader.close(); imageReader = null; }
        if (projection != null) { projection.stop(); projection = null; }
        if (handlerThread != null) { handlerThread.quitSafely(); }
    }

    @Override
    public IBinder onBind(Intent intent) { return null; }

    @Override
    public void onDestroy() {
        stopCapture();
        super.onDestroy();
    }
}
