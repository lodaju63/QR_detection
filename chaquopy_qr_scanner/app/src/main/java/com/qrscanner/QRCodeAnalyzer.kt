package com.qrscanner

import android.graphics.ImageFormat
import android.graphics.Bitmap
import android.graphics.ImageDecoder
import androidx.camera.core.ImageAnalysis
import androidx.camera.core.ImageProxy
import com.dynamsoft.barcode.BarcodeReader
import com.dynamsoft.barcode.BarcodeReaderException
import com.chaquo.python.Python
import com.chaquo.python.android.AndroidPlatform
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
                        val results = barcodeReader?.decodeBufferedImage(mediaImage)
                        results?.forEach { result ->
                            val text = result.barcodeText
                            if (text.isNotEmpty()) {
                                onResult(text)
                                imageProxy.close()
                                return
                            }
                        }
                    } catch (e: BarcodeReaderException) {
                        e.printStackTrace()
                    }
                    
                    // 방법 2: Python (OpenCV)로 QR 코드 읽기 (fallback)
                    try {
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
                        
                        // Python으로 전달
                        python?.let { py ->
                            val qrUtils = py.getModule("qr_utils")
                            val numpy = py.getModule("numpy")
                            
                            // YUV to BGR 변환 (Python에서 처리)
                            val imageArray = numpy.callAttr("frombuffer", nv21, "uint8")
                            val decoded = qrUtils.callAttr("decode_qr_opencv", imageArray)
                            
                            if (decoded != null && decoded.toString().isNotEmpty()) {
                                onResult(decoded.toString())
                            }
                        }
                    } catch (e: Exception) {
                        e.printStackTrace()
                    }
                }
            }
        }
        imageProxy.close()
    }
}
