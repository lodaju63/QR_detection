package com.qrscanner

import android.graphics.ImageFormat
import android.media.Image
import androidx.camera.core.ImageAnalysis
import androidx.camera.core.ImageProxy
import com.dynamsoft.cvr.CaptureVisionRouter
import com.dynamsoft.core.basic_structures.ImageData
import com.dynamsoft.core.basic_structures.EnumImagePixelFormat
import com.dynamsoft.dbr.DecodedBarcodesResult
import com.dynamsoft.dbr.BarcodeResultItem
import com.dynamsoft.core.basic_structures.CapturedResult
import com.chaquo.python.Python
import java.nio.ByteBuffer

class QRCodeAnalyzer(
    private val router: CaptureVisionRouter?,  // V11: BarcodeReader 대신 CaptureVisionRouter 사용
    private val python: Python?,
    private val onResult: (String) -> Unit,
    private val roiRect: android.graphics.Rect? = null,
    private val onDecodeAttempt: ((Int, Boolean) -> Unit)? = null
) : ImageAnalysis.Analyzer {
    
    private var attemptCount = 0

    override fun analyze(imageProxy: ImageProxy) {
        if (router == null) {
            imageProxy.close()
            return
        }
        
        val mediaImage = imageProxy.image
        if (mediaImage == null) {
            imageProxy.close()
            return
        }
        
        when (mediaImage.format) {
            ImageFormat.YUV_420_888 -> {
                try {
                    attemptCount++
                    
                    // V11: YUV 이미지를 ImageData로 변환
                    val yBuffer = mediaImage.planes[0].buffer
                    val ySize = yBuffer.remaining()
                    val yData = ByteArray(ySize)
                    yBuffer.get(yData)
                    
                    val width = imageProxy.width
                    val height = imageProxy.height
                    val stride = mediaImage.planes[0].rowStride
                    
                    // ROI 영역이 지정되어 있으면 해당 영역만 추출
                    var actualWidth = width
                    var actualHeight = height
                    var actualData = yData
                    var actualStride = stride
                    var offsetX = 0
                    var offsetY = 0
                    
                    if (roiRect != null && roiRect.width() > 0 && roiRect.height() > 0) {
                        // ROI 좌표를 이미지 크기에 맞게 조정
                        val scaleX = width.toFloat() / imageProxy.width.toFloat()
                        val scaleY = height.toFloat() / imageProxy.height.toFloat()
                        
                        val roiLeft = (roiRect.left * scaleX).toInt().coerceAtLeast(0)
                        val roiTop = (roiRect.top * scaleY).toInt().coerceAtLeast(0)
                        val roiRight = (roiRect.right * scaleX).toInt().coerceAtMost(width)
                        val roiBottom = (roiRect.bottom * scaleY).toInt().coerceAtMost(height)
                        
                        if (roiRight > roiLeft && roiBottom > roiTop) {
                            actualWidth = roiRight - roiLeft
                            actualHeight = roiBottom - roiTop
                            offsetX = roiLeft
                            offsetY = roiTop
                            
                            // ROI 영역만 추출 (Y 평면만)
                            actualData = ByteArray(actualHeight * actualStride)
                            for (y in 0 until actualHeight) {
                                val srcOffset = (offsetY + y) * actualStride + offsetX
                                val dstOffset = y * actualStride
                                System.arraycopy(yData, srcOffset, actualData, dstOffset, actualWidth)
                            }
                            
                            android.util.Log.d("QRCodeAnalyzer", "Using ROI: ${actualWidth}x${actualHeight} from ${width}x${height}")
                        }
                    }
                    
                    // V11: ImageData 생성 (Grayscale)
                    val imageData = ImageData().apply {
                        bytes = actualData
                        this.width = actualWidth
                        this.height = actualHeight
                        this.stride = actualStride
                        format = EnumImagePixelFormat.IPF_GRAYSCALED
                    }
                    
                    // V11: capture 메서드로 바코드 해독
                    val result: CapturedResult? = router.capture(imageData, "ReadSingleBarcode")
                    
                    val logMsg = "시도 #$attemptCount | 결과: ${if (result != null) "있음" else "없음"} | 이미지: ${actualWidth}x${actualHeight}"
                    android.util.Log.d("QRCodeAnalyzer", logMsg)
                    
                    var hasResult = false
                    if (result != null) {
                        val decodedResult: DecodedBarcodesResult? = result.decodedBarcodesResult
                        if (decodedResult != null && decodedResult.items.isNotEmpty()) {
                            for (item: BarcodeResultItem in decodedResult.items) {
                                val text = item.text
                                android.util.Log.d("QRCodeAnalyzer", "Found barcode: $text, format: ${item.format}")
                                if (!text.isNullOrEmpty()) {
                                    hasResult = true
                                    onResult(text)
                                    onDecodeAttempt?.invoke(attemptCount, true)
                                    attemptCount = 0
                                    imageProxy.close()
                                    return
                                }
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
            }
        }
        imageProxy.close()
    }
}
