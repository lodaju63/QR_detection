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
    private val onResult: (String) -> Unit,
    private val roiRect: android.graphics.Rect? = null,
    private val onDecodeAttempt: ((Int, Boolean) -> Unit)? = null
) : ImageAnalysis.Analyzer {
    
    private var attemptCount = 0

    override fun analyze(imageProxy: ImageProxy) {
        val mediaImage = imageProxy.image
        if (mediaImage != null && barcodeReader != null) {
            when (mediaImage.format) {
                ImageFormat.YUV_420_888 -> {
                    // 방법 1: Dynamsoft로 QR 코드 읽기 (우선)
                    try {
                        attemptCount++
                        var bitmap = mediaImageToBitmap(mediaImage)
                        
                        // ROI 영역이 지정되어 있으면 해당 영역만 추출
                        if (roiRect != null && roiRect.width() > 0 && roiRect.height() > 0) {
                            // ROI 좌표를 이미지 크기에 맞게 조정
                            val scaleX = bitmap.width.toFloat() / imageProxy.width.toFloat()
                            val scaleY = bitmap.height.toFloat() / imageProxy.height.toFloat()
                            
                            val roiLeft = (roiRect.left * scaleX).toInt().coerceAtLeast(0)
                            val roiTop = (roiRect.top * scaleY).toInt().coerceAtLeast(0)
                            val roiRight = (roiRect.right * scaleX).toInt().coerceAtMost(bitmap.width)
                            val roiBottom = (roiRect.bottom * scaleY).toInt().coerceAtMost(bitmap.height)
                            
                            if (roiRight > roiLeft && roiBottom > roiTop) {
                                val roiBitmap = Bitmap.createBitmap(
                                    bitmap,
                                    roiLeft,
                                    roiTop,
                                    roiRight - roiLeft,
                                    roiBottom - roiTop
                                )
                                bitmap = roiBitmap
                                android.util.Log.d("QRCodeAnalyzer", "Using ROI: ${roiRight - roiLeft}x${roiBottom - roiTop} from ${bitmap.width}x${bitmap.height}")
                            }
                        }
                        
                        // Dynamsoft Android SDK는 decodeBufferedImage 사용
                        val results = barcodeReader?.decodeBufferedImage(bitmap)
                        val logMsg = "시도 #$attemptCount | 결과: ${results?.size ?: 0}개 | 이미지: ${bitmap.width}x${bitmap.height}"
                        android.util.Log.d("QRCodeAnalyzer", logMsg)
                        
                        // UI 콜백 호출 (매 프레임마다)
                        onDecodeAttempt?.invoke(attemptCount, false)
                        
                        var hasResult = false
                        if (results != null && results.isNotEmpty()) {
                            for (result in results) {
                                val text = result.barcodeText
                                android.util.Log.d("QRCodeAnalyzer", "Found barcode: $text, format: ${result.barcodeFormatString}")
                                if (text != null && text.isNotEmpty()) {
                                    hasResult = true
                                    onResult(text)
                                    onDecodeAttempt?.invoke(attemptCount, true)
                                    attemptCount = 0
                                    imageProxy.close()
                                    return
                                }
                            }
                        }
                        
                        // 해독 시도 결과 콜백 (성공하지 못한 경우)
                        onDecodeAttempt?.invoke(attemptCount, false)
                        
                    } catch (e: Exception) {
                        android.util.Log.e("QRCodeAnalyzer", "Decode error at attempt #$attemptCount", e)
                        e.printStackTrace()
                        onDecodeAttempt?.invoke(attemptCount, false)
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
