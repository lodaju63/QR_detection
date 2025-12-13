package com.qrscanner

import android.graphics.ImageFormat
import androidx.camera.core.ImageAnalysis
import androidx.camera.core.ImageProxy
import com.dynamsoft.barcode.BarcodeReader
import com.dynamsoft.barcode.BarcodeReaderException
import com.dynamsoft.barcode.TextResult
import com.chaquo.python.Python
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
                    // Dynamsoft로 QR 코드 읽기
                    try {
                        val results = barcodeReader?.decodeBufferedImage(mediaImage)
                        results?.forEach { result ->
                            // QR 코드 텍스트 처리
                            val text = result.barcodeText
                            if (text.isNotEmpty()) {
                                onResult(text)
                            }
                        }
                    } catch (e: BarcodeReaderException) {
                        e.printStackTrace()
                    }
                }
            }
        }
        imageProxy.close()
    }
}
