package com.qrscanner

import android.Manifest
import android.content.pm.PackageManager
import android.graphics.Color
import android.graphics.Paint
import android.graphics.Path
import android.graphics.drawable.ShapeDrawable
import android.graphics.drawable.shapes.PathShape
import android.os.Bundle
import android.view.View
import android.widget.TextView
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import androidx.camera.core.*
import androidx.camera.lifecycle.ProcessCameraProvider
import androidx.camera.view.PreviewView
import androidx.core.app.ActivityCompat
import androidx.core.content.ContextCompat
import com.chaquo.python.Python
import com.chaquo.python.android.AndroidPlatform
import com.dynamsoft.dbr.BarcodeReader
import com.dynamsoft.dbr.DBRLicenseVerificationListener
import java.util.concurrent.ExecutorService
import java.util.concurrent.Executors

class MainActivity : AppCompatActivity() {
    private lateinit var previewView: PreviewView
    private var imageCapture: ImageCapture? = null
    private var cameraExecutor: ExecutorService = Executors.newSingleThreadExecutor()
    private var barcodeReader: BarcodeReader? = null
    private var python: Python? = null
    private lateinit var resultText: TextView
    private lateinit var roiBorder: View
    private lateinit var debugText: TextView
    private var decodeAttemptCount = 0
    private var lastDecodeTime = 0L

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        previewView = findViewById(R.id.previewView)
        resultText = findViewById(R.id.resultText)
        roiBorder = findViewById(R.id.roiBorder)
        debugText = findViewById(R.id.debugText)
        
        // ROI 영역 테두리 설정
        setupROIBorder()
        
        // 디버그 텍스트 표시 (개발 중)
        debugText.visibility = android.view.View.VISIBLE
        resultText.setTextColor(Color.WHITE)

        // Python 초기화
        if (!Python.isStarted()) {
            Python.start(AndroidPlatform(this))
        }
        python = Python.getInstance()
        
        // Python 모듈 테스트
        try {
            val qrUtils = python?.getModule("qr_utils")
            android.util.Log.d("MainActivity", "Python module loaded: $qrUtils")
        } catch (e: Exception) {
            android.util.Log.e("MainActivity", "Failed to load Python module", e)
        }

        // Dynamsoft 초기화 (9.x 버전: 정적 메서드 사용)
        BarcodeReader.initLicense("t0085YQEAADYdcL2llMa8vH1Rtnun+43saE/kdAE7ZbIxMQGRMtSzVSZRI8vfOK4Ids52rjekwzh87yABFLraXw5Va1BV7NnBjI8m7qbw3kxOprI75ExJpw==", object : DBRLicenseVerificationListener {
            override fun DBRLicenseVerificationCallback(isSuccess: Boolean, error: Exception?) {
                if (isSuccess) {
                    try {
                        barcodeReader = BarcodeReader()
                    } catch (e: Exception) {
                        e.printStackTrace()
                        Toast.makeText(this@MainActivity, "Dynamsoft 초기화 실패", Toast.LENGTH_SHORT).show()
                    }
                } else {
                    error?.printStackTrace()
                    Toast.makeText(this@MainActivity, "Dynamsoft 라이선스 검증 실패", Toast.LENGTH_SHORT).show()
                }
            }
        })

        // 권한 확인
        if (allPermissionsGranted()) {
            startCamera()
        } else {
            ActivityCompat.requestPermissions(
                this,
                REQUIRED_PERMISSIONS,
                REQUEST_CODE_PERMISSIONS
            )
        }
    }

    private fun allPermissionsGranted() = REQUIRED_PERMISSIONS.all {
        ContextCompat.checkSelfPermission(
            baseContext, it
        ) == PackageManager.PERMISSION_GRANTED
    }

    private fun startCamera() {
        val cameraProviderFuture = ProcessCameraProvider.getInstance(this)

        cameraProviderFuture.addListener({
            val cameraProvider: ProcessCameraProvider = cameraProviderFuture.get()

            val preview = Preview.Builder()
                .build()
                .also {
                    it.setSurfaceProvider(previewView.surfaceProvider)
                }

            imageCapture = ImageCapture.Builder()
                .build()

            val imageAnalyzer = ImageAnalysis.Builder()
                .setBackpressureStrategy(ImageAnalysis.STRATEGY_KEEP_ONLY_LATEST)
                .build()
                .also {
                    val roiRect = calculateROIRect()
                    it.setAnalyzer(cameraExecutor, QRCodeAnalyzer(barcodeReader, python, { text ->
                        runOnUiThread {
                            resultText.text = "QR: $text"
                            resultText.setTextColor(Color.GREEN)
                            debugText.text = "✅ 해독 성공! (시도: $decodeAttemptCount)"
                            debugText.setTextColor(Color.GREEN)
                            decodeAttemptCount = 0
                        }
                    }, roiRect) { attemptCount, hasResult ->
                        runOnUiThread {
                            decodeAttemptCount = attemptCount
                            val currentTime = System.currentTimeMillis()
                            val fps = if (currentTime - lastDecodeTime > 0 && lastDecodeTime > 0) {
                                1000 / (currentTime - lastDecodeTime)
                            } else {
                                0
                            }
                            lastDecodeTime = currentTime
                            
                            if (!hasResult) {
                                debugText.text = "🔍 스캔 중... (시도: $attemptCount, FPS: $fps)"
                                debugText.setTextColor(Color.YELLOW)
                            }
                        }
                    })
                }

            val cameraSelector = CameraSelector.DEFAULT_BACK_CAMERA

            try {
                cameraProvider.unbindAll()
                cameraProvider.bindToLifecycle(
                    this,
                    cameraSelector,
                    preview,
                    imageCapture,
                    imageAnalyzer
                )
            } catch (e: Exception) {
                e.printStackTrace()
                Toast.makeText(this, "카메라 시작 실패: ${e.message}", Toast.LENGTH_SHORT).show()
            }
        }, ContextCompat.getMainExecutor(this))
    }

    override fun onRequestPermissionsResult(
        requestCode: Int,
        permissions: Array<String>,
        grantResults: IntArray
    ) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults)
        if (requestCode == REQUEST_CODE_PERMISSIONS) {
            if (allPermissionsGranted()) {
                startCamera()
            } else {
                Toast.makeText(
                    this,
                    "카메라 권한이 필요합니다.",
                    Toast.LENGTH_SHORT
                ).show()
                finish()
            }
        }
    }

    override fun onDestroy() {
        super.onDestroy()
        cameraExecutor.shutdown()
        // Dynamsoft 9.x에서는 destroy() 메서드가 private이므로 제거
        // barcodeReader?.destroy()
    }

    private fun setupROIBorder() {
        // ROI 영역 전체 테두리 그리기 (반투명 배경 + 테두리)
        roiBorder.post {
            val width = roiBorder.width.toFloat()
            val height = roiBorder.height.toFloat()
            
            // 전체 사각형 테두리
            val path = Path()
            path.addRect(0f, 0f, width, height, Path.Direction.CW)
            
            val shapeDrawable = ShapeDrawable(PathShape(path, width, height))
            val paint = shapeDrawable.paint
            paint.color = Color.GREEN
            paint.style = Paint.Style.STROKE
            paint.strokeWidth = 6f
            paint.isAntiAlias = true
            
            // 배경은 반투명 (XML에서 설정했지만 여기서도 확인)
            roiBorder.background = shapeDrawable
        }
    }
    
    private fun calculateROIRect(): android.graphics.Rect? {
        // ROI 영역 계산 (화면 중앙 50% 영역 - 반으로 줄임)
        return try {
            val margin = 80 // dp를 픽셀로 변환 (40dp -> 80dp로 증가하여 영역을 반으로 줄임)
            val displayMetrics = resources.displayMetrics
            val marginPx = (margin * displayMetrics.density).toInt()
            
            val screenWidth = previewView.width
            val screenHeight = previewView.height
            
            if (screenWidth > 0 && screenHeight > 0) {
                android.graphics.Rect(
                    marginPx,
                    marginPx,
                    screenWidth - marginPx,
                    screenHeight - marginPx
                )
            } else {
                null
            }
        } catch (e: Exception) {
            null
        }
    }

    companion object {
        private const val REQUEST_CODE_PERMISSIONS = 10
        private val REQUIRED_PERMISSIONS = arrayOf(Manifest.permission.CAMERA)
    }
}
