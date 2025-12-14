package com.qrscanner

import android.graphics.ImageFormat
import android.media.Image
import androidx.camera.core.ImageAnalysis
import androidx.camera.core.ImageProxy
import com.dynamsoft.cvr.CaptureVisionRouter
import com.dynamsoft.cvr.CapturedResult
import com.dynamsoft.core.basic_structures.ImageData
import com.dynamsoft.core.basic_structures.EnumImagePixelFormat
import com.dynamsoft.dbr.DecodedBarcodesResult
import com.dynamsoft.dbr.BarcodeResultItem
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
                    // stride가 width보다 큰 경우 width로 조정 (패딩 제거)
                    val adjustedStride = if (actualStride >= actualWidth) actualWidth else actualStride
                    
                    // stride가 width와 다르면 데이터 재구성 필요
                    val finalData = if (actualStride != actualWidth) {
                        val newData = ByteArray(actualWidth * actualHeight)
                        for (y in 0 until actualHeight) {
                            val srcOffset = y * actualStride
                            val dstOffset = y * actualWidth
                            System.arraycopy(actualData, srcOffset, newData, dstOffset, actualWidth)
                        }
                        newData
                    } else {
                        actualData
                    }
                    
                    val imageData = ImageData().apply {
                        bytes = finalData
                        this.width = actualWidth
                        this.height = actualHeight
                        this.stride = actualWidth  // stride를 width와 동일하게 설정
                        format = EnumImagePixelFormat.IPF_GRAYSCALED
                    }
                    
                    android.util.Log.d("QRCodeAnalyzer", "ImageData: ${actualWidth}x${actualHeight}, stride: ${imageData.stride}, data size: ${finalData.size}")
                    
                    // V11: capture 메서드로 바코드 해독
                    val result: CapturedResult? = router.capture(imageData, "ReadSingleBarcode")
                    
                    val logMsg = "시도 #$attemptCount | 결과: ${if (result != null) "있음" else "없음"} | 이미지: ${actualWidth}x${actualHeight} stride: $actualStride"
                    android.util.Log.d("QRCodeAnalyzer", logMsg)
                    
                    var hasResult = false
                    if (result != null) {
                        // V11: CapturedResult에서 바코드 결과 직접 접근
                        try {
                            // 방법 1: getDecodedBarcodesResult() 직접 호출
                            val decodedBarcodesResult = result.decodedBarcodesResult
                            android.util.Log.d("QRCodeAnalyzer", "decodedBarcodesResult: $decodedBarcodesResult")
                            
                            if (decodedBarcodesResult != null) {
                                val barcodeItems = decodedBarcodesResult.items
                                android.util.Log.d("QRCodeAnalyzer", "barcodeItems: ${barcodeItems?.size ?: 0}개")
                                
                                if (barcodeItems != null && barcodeItems.isNotEmpty()) {
                                    for (barcodeItem: BarcodeResultItem in barcodeItems) {
                                        val text = barcodeItem.text
                                        android.util.Log.d("QRCodeAnalyzer", "Found barcode: $text, format: ${barcodeItem.format}")
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
                            
                            // 방법 2: items를 통한 접근 (fallback)
                            val items = result.items
                            android.util.Log.d("QRCodeAnalyzer", "result.items: ${items?.size ?: 0}개")
                            if (items != null && items.isNotEmpty()) {
                                for (item in items) {
                                    android.util.Log.d("QRCodeAnalyzer", "item type: ${item.javaClass.simpleName}")
                                    if (item is DecodedBarcodesResult) {
                                        val barcodeItems = item.items
                                        if (barcodeItems != null && barcodeItems.isNotEmpty()) {
                                            for (barcodeItem: BarcodeResultItem in barcodeItems) {
                                                val text = barcodeItem.text
                                                android.util.Log.d("QRCodeAnalyzer", "Found barcode (via items): $text")
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
                                }
                            }
                        } catch (e: Exception) {
                            android.util.Log.e("QRCodeAnalyzer", "Error accessing result: ${e.message}", e)
                        }
                    } else {
                        android.util.Log.d("QRCodeAnalyzer", "capture() returned null")
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
