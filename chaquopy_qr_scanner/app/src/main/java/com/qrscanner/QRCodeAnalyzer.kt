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
}
