package com.qrscanner

import android.graphics.ImageFormat
import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.media.Image
import androidx.camera.core.ImageAnalysis
import androidx.camera.core.ImageProxy
import com.dynamsoft.dbr.BarcodeReader
import com.dynamsoft.dbr.TextResult
import com.chaquo.python.Python
import com.chaquo.python.android.AndroidPlatform
import java.io.ByteArrayOutputStream
import java.nio.ByteBuffer

class QRCodeAnalyzer(
    private val barcodeReader: BarcodeReader?,
    private val python: Python?,
    private val onResult: (String) -> Unit
) : ImageAnalysis.Analyzer {

    override fun analyze(imageProxy: ImageProxy) {
        val mediaImage = imageProxy.image
        if (mediaImage != null) {
            when (mediaImage.format) {
                ImageFormat.YUV_420_888 -> {
                    // 방법 1: Dynamsoft로 QR 코드 읽기 (우선)
                    try {
                        val bitmap = mediaImageToBitmap(mediaImage)
                        // Dynamsoft Android SDK는 decodeBitmap 사용
                        val results = barcodeReader?.decodeBitmap(bitmap)
                        if (results != null && results.isNotEmpty()) {
                            for (result in results) {
                                val text = result.barcodeText
                                if (text != null && text.isNotEmpty()) {
                                    onResult(text)
                                    imageProxy.close()
                                    return
                                }
                            }
                        }
                    } catch (e: Exception) {
                        android.util.Log.e("QRCodeAnalyzer", "Decode error", e)
                        e.printStackTrace()
                    }
                    
                    // 방법 2: Python (OpenCV)로 QR 코드 읽기 (fallback)
                    // 주의: YUV 이미지를 Python으로 전달하는 것은 복잡하므로
                    // 일단 Dynamsoft만 사용하고, 필요시 추가 구현
                    // python?.let { py ->
                    //     val qrUtils = py.getModule("qr_utils")
                    //     // 이미지 변환 후 Python 함수 호출
                    // }
                }
            }
        }
        imageProxy.close()
    }
    
    private fun mediaImageToBitmap(mediaImage: Image): Bitmap {
        val yBuffer = mediaImage.planes[0].buffer
        val uBuffer = mediaImage.planes[1].buffer
        val vBuffer = mediaImage.planes[2].buffer
        
        val ySize = yBuffer.remaining()
        val uSize = uBuffer.remaining()
        val vSize = vBuffer.remaining()
        
        val nv21 = ByteArray(ySize + uSize + vSize)
        
        yBuffer.get(nv21, 0, ySize)
        vBuffer.get(nv21, ySize, vSize)
        uBuffer.get(nv21, ySize + vSize, uSize)
        
        val yuvImage = android.graphics.YuvImage(nv21, ImageFormat.NV21, mediaImage.width, mediaImage.height, null)
        val out = java.io.ByteArrayOutputStream()
        yuvImage.compressToJpeg(android.graphics.Rect(0, 0, mediaImage.width, mediaImage.height), 100, out)
        val imageBytes = out.toByteArray()
        return android.graphics.BitmapFactory.decodeByteArray(imageBytes, 0, imageBytes.size)
    }
}
