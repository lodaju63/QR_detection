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
import com.dynamsoft.core.basic_structures.Quadrilateral
import android.graphics.Point as AndroidPoint
import com.chaquo.python.Python
import java.nio.ByteBuffer

class QRCodeAnalyzer(
    private val router: CaptureVisionRouter?,  // V11: BarcodeReader 대신 CaptureVisionRouter 사용
    private val python: Python?,
    private val onResult: (String, android.graphics.Rect?) -> Unit,  // 바코드 텍스트와 위치 정보 전달
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
                    
                    // 디버그 로그는 첫 시도와 매 100번째 시도마다만 출력
                    if (attemptCount == 1 || attemptCount % 100 == 0) {
                        android.util.Log.d("QRCodeAnalyzer", "ImageData: ${actualWidth}x${actualHeight}, stride: ${imageData.stride}")
                    }
                    
                    // V11: capture 메서드로 바코드 해독
                    val result: CapturedResult? = router.capture(imageData, "ReadSingleBarcode")
                    
                    // 로그 빈도 줄이기: 매 50번째 시도마다만 로그 출력
                    if (attemptCount % 50 == 0) {
                        android.util.Log.d("QRCodeAnalyzer", "시도 #$attemptCount | 결과: ${if (result != null) "있음" else "없음"}")
                    }
                    
                    var hasResult = false
                    if (result != null) {
                        // V11: CapturedResult에서 바코드 결과 직접 접근
                        try {
                            // 방법 1: getDecodedBarcodesResult() 직접 호출
                            val decodedBarcodesResult = result.decodedBarcodesResult
                            
                            if (decodedBarcodesResult != null) {
                                val barcodeItems = decodedBarcodesResult.items
                                
                                if (barcodeItems != null && barcodeItems.isNotEmpty()) {
                                    for (barcodeItem: BarcodeResultItem in barcodeItems) {
                                        val text = barcodeItem.text
                                        if (!text.isNullOrEmpty()) {
                                            hasResult = true
                                            
                                            // 바코드 위치 정보 추출
                                            val barcodeRect = try {
                                                val location: Quadrilateral? = barcodeItem.location
                                                if (location != null) {
                                                    val points = location.points
                                                    if (points != null && points.size >= 4) {
                                                        // 4개 점에서 바운딩 박스 계산
                                                        var minX = Int.MAX_VALUE
                                                        var minY = Int.MAX_VALUE
                                                        var maxX = Int.MIN_VALUE
                                                        var maxY = Int.MIN_VALUE
                                                        
                                                        for (i in 0 until points.size) {
                                                            val point = points[i]
                                                            // Point 객체의 x, y 속성 접근
                                                            val x = when {
                                                                point is AndroidPoint -> point.x.toFloat()
                                                                else -> {
                                                                    // 리플렉션으로 접근 시도
                                                                    try {
                                                                        val getXMethod = point.javaClass.getMethod("getX")
                                                                        (getXMethod.invoke(point) as? Number)?.toFloat() ?: 
                                                                        (point.javaClass.getField("x").get(point) as? Number)?.toFloat() ?: 0f
                                                                    } catch (e: Exception) {
                                                                        try {
                                                                            (point.javaClass.getField("x").get(point) as? Number)?.toFloat() ?: 0f
                                                                        } catch (e2: Exception) {
                                                                            0f
                                                                        }
                                                                    }
                                                                }
                                                            }
                                                            val y = when {
                                                                point is AndroidPoint -> point.y.toFloat()
                                                                else -> {
                                                                    try {
                                                                        val getYMethod = point.javaClass.getMethod("getY")
                                                                        (getYMethod.invoke(point) as? Number)?.toFloat() ?:
                                                                        (point.javaClass.getField("y").get(point) as? Number)?.toFloat() ?: 0f
                                                                    } catch (e: Exception) {
                                                                        try {
                                                                            (point.javaClass.getField("y").get(point) as? Number)?.toFloat() ?: 0f
                                                                        } catch (e2: Exception) {
                                                                            0f
                                                                        }
                                                                    }
                                                                }
                                                            }
                                                            minX = minOf(minX, x.toInt())
                                                            minY = minOf(minY, y.toInt())
                                                            maxX = maxOf(maxX, x.toInt())
                                                            maxY = maxOf(maxY, y.toInt())
                                                        }
                                                        
                                                        // ROI 오프셋 추가 (전체 이미지 좌표로 변환)
                                                        android.graphics.Rect(
                                                            minX + offsetX,
                                                            minY + offsetY,
                                                            maxX + offsetX,
                                                            maxY + offsetY
                                                        )
                                                    } else null
                                                } else null
                                            } catch (e: Exception) {
                                                android.util.Log.e("QRCodeAnalyzer", "Error getting location: ${e.message}")
                                                null
                                            }
                                            
                                            android.util.Log.d("QRCodeAnalyzer", "✅ Found barcode: $text, rect: $barcodeRect")
                                            onResult(text, barcodeRect)
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
                            if (items != null && items.isNotEmpty()) {
                                for (item in items) {
                                    if (item is DecodedBarcodesResult) {
                                        val barcodeItems = item.items
                                        if (barcodeItems != null && barcodeItems.isNotEmpty()) {
                                            for (barcodeItem: BarcodeResultItem in barcodeItems) {
                                                val text = barcodeItem.text
                                                if (!text.isNullOrEmpty()) {
                                                    hasResult = true
                                                    
                                                    // 바코드 위치 정보 추출
                                                    val barcodeRect = try {
                                                        val location: Quadrilateral? = barcodeItem.location
                                                        if (location != null) {
                                                            val points = location.points
                                                            if (points != null && points.size >= 4) {
                                                                var minX = Int.MAX_VALUE
                                                                var minY = Int.MAX_VALUE
                                                                var maxX = Int.MIN_VALUE
                                                                var maxY = Int.MIN_VALUE
                                                                
                                                                for (point: Point in points) {
                                                                    val x = point.x.toInt()
                                                                    val y = point.y.toInt()
                                                                    minX = minOf(minX, x)
                                                                    minY = minOf(minY, y)
                                                                    maxX = maxOf(maxX, x)
                                                                    maxY = maxOf(maxY, y)
                                                                }
                                                                
                                                                android.graphics.Rect(
                                                                    minX + offsetX,
                                                                    minY + offsetY,
                                                                    maxX + offsetX,
                                                                    maxY + offsetY
                                                                )
                                                            } else null
                                                        } else null
                                                    } catch (e: Exception) {
                                                        null
                                                    }
                                                    
                                                    onResult(text, barcodeRect)
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
