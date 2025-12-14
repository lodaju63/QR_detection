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
import com.dynamsoft.license.LicenseManager
import com.dynamsoft.license.LicenseVerificationListener
import com.dynamsoft.cvr.CaptureVisionRouter
import java.util.concurrent.ExecutorService
import java.util.concurrent.Executors

class MainActivity : AppCompatActivity() {
    private lateinit var previewView: PreviewView
    private var imageCapture: ImageCapture? = null
    private var cameraExecutor: ExecutorService = Executors.newSingleThreadExecutor()
    private var cvRouter: CaptureVisionRouter? = null  // V11: BarcodeReader 대신 CaptureVisionRouter 사용
    private var python: Python? = null
    private lateinit var resultText: TextView
    private lateinit var roiBorder: View
    private lateinit var debugText: TextView
    private lateinit var debugScrollView: android.widget.ScrollView
    private var decodeAttemptCount = 0
    private var lastDecodeTime = 0L
    private val logHistory = mutableListOf<String>()
    private var isLicenseValid = false  // 라이선스 검증 상태 추적

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        previewView = findViewById(R.id.previewView)
        resultText = findViewById(R.id.resultText)
        roiBorder = findViewById(R.id.roiBorder)
        debugText = findViewById(R.id.debugText)
        debugScrollView = findViewById(R.id.debugScrollView)
        
        // 디버그 텍스트 표시 (개발 중)
        debugText.visibility = android.view.View.VISIBLE
        addLog("⏳ 앱 시작", Color.WHITE)
        addLog("초기화 중...", Color.WHITE)
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

        // Dynamsoft 초기화 (V11.X: LicenseManager 사용)
        val licenseKey = "t0085YQEAADYdcL2llMa8vH1Rtnun+43saE/kdAE7ZbIxMQGRMtSzVSZRI8vfOK4Ids52rjekwzh87yABFLraXw5Va1BV7NnBjI8m7qbw3kxOprI75ExJpw=="
        android.util.Log.d("MainActivity", "Dynamsoft 라이선스 초기화 시작...")
        android.util.Log.d("MainActivity", "라이선스 키 길이: ${licenseKey.length}")
        
        try {
            // V11: LicenseManager.initLicense 사용
            LicenseManager.initLicense(licenseKey, this, object : LicenseVerificationListener {
                override fun onLicenseVerified(isSuccess: Boolean, error: Exception?) {
                    runOnUiThread {
                        if (isSuccess) {
                            try {
                                // V11: CaptureVisionRouter 인스턴스 생성
                                cvRouter = CaptureVisionRouter(this@MainActivity)
                                isLicenseValid = true
                                addLog("✅ Dynamsoft 초기화 완료", Color.GREEN)
                                android.util.Log.d("MainActivity", "Dynamsoft 초기화 성공")
                                
                                // 라이선스 검증 성공 후 권한이 이미 허용되어 있으면 카메라 시작
                                if (allPermissionsGranted()) {
                                    addLog("카메라 시작 중...", Color.GREEN)
                                    startCamera()
                                } else {
                                    addLog("카메라 권한 대기 중...", Color.YELLOW)
                                }
                            } catch (e: Exception) {
                                e.printStackTrace()
                                isLicenseValid = false
                                addLog("❌ Dynamsoft 초기화 실패: ${e.message}", Color.RED)
                                Toast.makeText(this@MainActivity, "Dynamsoft 초기화 실패", Toast.LENGTH_SHORT).show()
                            }
                        } else {
                            isLicenseValid = false
                            error?.printStackTrace()
                            val errorMsg = error?.message ?: "알 수 없는 오류"
                            val errorClass = error?.javaClass?.simpleName ?: "Unknown"
                            addLog("❌ 라이선스 검증 실패!", Color.RED)
                            addLog("오류 타입: $errorClass", Color.RED)
                            addLog("메시지: $errorMsg", Color.RED)
                            addLog("인터넷 연결을 확인하세요", Color.YELLOW)
                            
                            // 상세 로그 출력
                            android.util.Log.e("MainActivity", "Dynamsoft 라이선스 검증 실패", error)
                            android.util.Log.e("MainActivity", "Error class: $errorClass")
                            android.util.Log.e("MainActivity", "Error message: $errorMsg")
                            if (error != null) {
                                android.util.Log.e("MainActivity", "Error stack trace: ${error.stackTraceToString()}")
                            }
                            
                            Toast.makeText(this@MainActivity, "Dynamsoft 라이선스 검증 실패: $errorMsg", Toast.LENGTH_LONG).show()
                            
                            // 라이선스 검증 실패 시 카메라 시작하지 않음
                            addLog("⚠️ 라이선스 없이 카메라는 시작되지 않습니다", Color.RED)
                        }
                    }
                }
            })
        } catch (e: Exception) {
            e.printStackTrace()
            isLicenseValid = false
            addLog("❌ 라이선스 초기화 중 오류: ${e.message}", Color.RED)
            android.util.Log.e("MainActivity", "License initialization error", e)
        }

        // 권한 확인 (Dynamsoft 초기화 완료 후 카메라 시작)
        // 카메라는 Dynamsoft 초기화 성공 후 startCamera()에서 호출됨
        if (!allPermissionsGranted()) {
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
        // 라이선스 검증이 완료되지 않았거나 실패한 경우 카메라 시작하지 않음
        if (!isLicenseValid || cvRouter == null) {
            addLog("⚠️ 라이선스 검증이 완료되지 않아 카메라를 시작할 수 없습니다", Color.RED)
            return
        }
        
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
                    it.setAnalyzer(cameraExecutor, QRCodeAnalyzer(cvRouter, python, { text ->
                        runOnUiThread {
                            resultText.text = "QR: $text"
                            resultText.setTextColor(Color.GREEN)
                            addLog("✅ 해독 성공! (시도: $decodeAttemptCount)", Color.GREEN)
                            addLog("QR 코드: $text", Color.GREEN)
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
                                // 주기적으로 상태 업데이트 (매 10번째 시도마다)
                                if (attemptCount % 10 == 0) {
                                    val roiInfo = if (roiRect != null) "${roiRect.width()}x${roiRect.height()}" else "계산중"
                                    addLog("🔍 스캔 중... 시도: $attemptCount | FPS: $fps | ROI: $roiInfo", Color.YELLOW)
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
                    addLog("✅ 카메라 시작 완료", Color.GREEN)
                    addLog("QR 코드를 스캔하세요...", Color.GREEN)
                }
            } catch (e: Exception) {
                e.printStackTrace()
                runOnUiThread {
                    addLog("❌ 카메라 시작 실패: ${e.message}", Color.RED)
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
                // 라이선스 검증이 성공하고 Dynamsoft가 초기화되었을 때만 카메라 시작
                if (isLicenseValid && cvRouter != null) {
                    addLog("카메라 권한 획득", Color.GREEN)
                    startCamera()
                } else {
                    addLog("⚠️ Dynamsoft 초기화 대기 중...", Color.YELLOW)
                }
            } else {
                addLog("❌ 카메라 권한 거부됨", Color.RED)
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
        // V11: CaptureVisionRouter 정리 (V11에서는 자동으로 정리됨)
        cvRouter = null
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

    private fun addLog(message: String, color: Int) {
        val timestamp = java.text.SimpleDateFormat("HH:mm:ss", java.util.Locale.getDefault()).format(java.util.Date())
        val logEntry = "[$timestamp] $message"
        logHistory.add(logEntry)
        
        // 최대 20개 로그만 유지
        if (logHistory.size > 20) {
            logHistory.removeAt(0)
        }
        
        // 모든 로그를 하나의 텍스트로 합치기
        val fullLog = logHistory.joinToString("\n")
        debugText.text = fullLog
        
        // 마지막 로그의 색상으로 설정 (전체는 흰색으로)
        debugText.setTextColor(Color.WHITE)
        
        // 스크롤을 맨 아래로
        debugScrollView.post {
            debugScrollView.fullScroll(android.view.View.FOCUS_DOWN)
        }
        
        android.util.Log.d("MainActivity", logEntry)
    }

    companion object {
        private const val REQUEST_CODE_PERMISSIONS = 10
        private val REQUIRED_PERMISSIONS = arrayOf(Manifest.permission.CAMERA)
    }
}
