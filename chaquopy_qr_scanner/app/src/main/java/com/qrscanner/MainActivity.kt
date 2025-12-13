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
        
        // 디버그 텍스트 표시 (개발 중)
        debugText.visibility = android.view.View.VISIBLE
        debugText.text = "⏳ 초기화 중...\n카메라를 시작합니다."
        debugText.setTextColor(Color.WHITE)
        resultText.setTextColor(Color.WHITE)
        
        // ROI 영역 테두리 설정 (레이아웃 완료 후)
        previewView.post {
            setupROIBorder()
        }

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
                runOnUiThread {
                    if (isSuccess) {
                        try {
                            barcodeReader = BarcodeReader()
                            debugText.text = "✅ Dynamsoft 초기화 완료\n카메라 시작 중..."
                            debugText.setTextColor(Color.GREEN)
                            android.util.Log.d("MainActivity", "Dynamsoft 초기화 성공")
                        } catch (e: Exception) {
                            e.printStackTrace()
                            debugText.text = "❌ Dynamsoft 초기화 실패: ${e.message}"
                            debugText.setTextColor(Color.RED)
                            Toast.makeText(this@MainActivity, "Dynamsoft 초기화 실패", Toast.LENGTH_SHORT).show()
                        }
                    } else {
                        error?.printStackTrace()
                        debugText.text = "❌ 라이선스 검증 실패: ${error?.message ?: "알 수 없는 오류"}"
                        debugText.setTextColor(Color.RED)
                        Toast.makeText(this@MainActivity, "Dynamsoft 라이선스 검증 실패", Toast.LENGTH_SHORT).show()
                    }
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
                                // 간단하고 명확한 로그 표시
                                val roiInfo = if (roiRect != null) "${roiRect.width()}x${roiRect.height()}" else "계산중"
                                val logText = "🔍 스캔 중...\n\n시도: $attemptCount\nFPS: $fps\nROI: $roiInfo\n\n[상태] QR 코드 대기 중"
                                debugText.text = logText
                                debugText.setTextColor(Color.YELLOW)
                                
                                // 주기적으로 로그 출력 (매 10번째 시도마다)
                                if (attemptCount % 10 == 0) {
                                    android.util.Log.d("MainActivity", "Scan attempt #$attemptCount, FPS: $fps, ROI: $roiInfo")
                                }
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
                runOnUiThread {
                    debugText.text = "✅ 카메라 시작 완료\nQR 코드를 스캔하세요..."
                    debugText.setTextColor(Color.GREEN)
                }
            } catch (e: Exception) {
                e.printStackTrace()
                runOnUiThread {
                    debugText.text = "❌ 카메라 시작 실패: ${e.message}"
                    debugText.setTextColor(Color.RED)
                }
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
        // ROI 영역 전체 테두리 그리기 (반투명 배경 + 전체 테두리)
        roiBorder.post {
            val width = roiBorder.width.toFloat()
            val height = roiBorder.height.toFloat()
            
            // 전체 사각형 테두리 (모서리만이 아니라 전체)
            val path = Path()
            path.addRect(0f, 0f, width, height, Path.Direction.CW)
            
            // 반투명 배경 + 테두리를 위한 레이어드 드로어블
            val shapeDrawable = ShapeDrawable(PathShape(path, width, height))
            val paint = shapeDrawable.paint
            paint.color = Color.GREEN
            paint.style = Paint.Style.STROKE
            paint.strokeWidth = 6f
            paint.isAntiAlias = true
            
            // 배경은 XML에서 설정 (#40FFFFFF - 반투명 흰색)
            // 여기서는 테두리만 추가
            roiBorder.background = shapeDrawable
            
            android.util.Log.d("MainActivity", "ROI Border setup: ${width}x${height}")
        }
    }
    
    private fun calculateROIRect(): android.graphics.Rect? {
        // ROI 영역 계산 (정사각형, 상단 중앙 배치)
        return try {
            val displayMetrics = resources.displayMetrics
            val topMarginPx = (60 * displayMetrics.density).toInt() // 상단 여백
            val bottomMarginPx = (200 * displayMetrics.density).toInt() // 하단 여백 (로그 공간)
            
            val screenWidth = previewView.width
            val screenHeight = previewView.height
            
            if (screenWidth > 0 && screenHeight > 0) {
                // 정사각형 크기 계산 (화면 너비의 70%)
                val roiSize = (screenWidth * 0.7f).toInt()
                val roiLeft = (screenWidth - roiSize) / 2
                val roiTop = topMarginPx
                val roiRight = roiLeft + roiSize
                val roiBottom = roiTop + roiSize
                
                android.util.Log.d("MainActivity", "ROI Rect: $roiLeft, $roiTop, $roiRight, $roiBottom (size: $roiSize)")
                
                android.graphics.Rect(
                    roiLeft,
                    roiTop,
                    roiRight,
                    roiBottom
                )
            } else {
                null
            }
        } catch (e: Exception) {
            android.util.Log.e("MainActivity", "Error calculating ROI", e)
            null
        }
    }

    companion object {
        private const val REQUEST_CODE_PERMISSIONS = 10
        private val REQUIRED_PERMISSIONS = arrayOf(Manifest.permission.CAMERA)
    }
}
