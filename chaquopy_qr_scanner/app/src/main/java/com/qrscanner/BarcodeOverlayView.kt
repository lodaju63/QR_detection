package com.qrscanner

import android.content.Context
import android.graphics.Canvas
import android.graphics.Color
import android.graphics.Paint
import android.graphics.Rect
import android.util.AttributeSet
import android.view.View

class BarcodeOverlayView @JvmOverloads constructor(
    context: Context,
    attrs: AttributeSet? = null,
    defStyleAttr: Int = 0
) : View(context, attrs, defStyleAttr) {
    
    private var barcodeRect: Rect? = null
    private val paint = Paint().apply {
        color = Color.GREEN
        style = Paint.Style.STROKE
        strokeWidth = 8f
        isAntiAlias = true
    }
    
    fun setBarcodeRect(rect: Rect?) {
        barcodeRect = rect
        invalidate()
    }
    
    fun clearBarcodeRect() {
        barcodeRect = null
        invalidate()
    }
    
    override fun onDraw(canvas: Canvas) {
        super.onDraw(canvas)
        
        barcodeRect?.let { rect ->
            // 이미지 좌표를 화면 좌표로 변환
            val previewView = parent as? View
            if (previewView != null) {
                val scaleX = width.toFloat() / previewView.width.toFloat()
                val scaleY = height.toFloat() / previewView.height.toFloat()
                
                val screenRect = Rect(
                    (rect.left * scaleX).toInt(),
                    (rect.top * scaleY).toInt(),
                    (rect.right * scaleX).toInt(),
                    (rect.bottom * scaleY).toInt()
                )
                
                // 바코드 박스 그리기
                canvas.drawRect(screenRect, paint)
                
                // 모서리에 작은 사각형 그리기 (시각적 강조)
                val cornerSize = 30f
                paint.strokeWidth = 6f
                
                // 왼쪽 위
                canvas.drawLine(screenRect.left.toFloat(), screenRect.top.toFloat(),
                    screenRect.left + cornerSize, screenRect.top.toFloat(), paint)
                canvas.drawLine(screenRect.left.toFloat(), screenRect.top.toFloat(),
                    screenRect.left.toFloat(), screenRect.top + cornerSize, paint)
                
                // 오른쪽 위
                canvas.drawLine(screenRect.right.toFloat(), screenRect.top.toFloat(),
                    screenRect.right - cornerSize, screenRect.top.toFloat(), paint)
                canvas.drawLine(screenRect.right.toFloat(), screenRect.top.toFloat(),
                    screenRect.right.toFloat(), screenRect.top + cornerSize, paint)
                
                // 왼쪽 아래
                canvas.drawLine(screenRect.left.toFloat(), screenRect.bottom.toFloat(),
                    screenRect.left + cornerSize, screenRect.bottom.toFloat(), paint)
                canvas.drawLine(screenRect.left.toFloat(), screenRect.bottom.toFloat(),
                    screenRect.left.toFloat(), screenRect.bottom - cornerSize, paint)
                
                // 오른쪽 아래
                canvas.drawLine(screenRect.right.toFloat(), screenRect.bottom.toFloat(),
                    screenRect.right - cornerSize, screenRect.bottom.toFloat(), paint)
                canvas.drawLine(screenRect.right.toFloat(), screenRect.bottom.toFloat(),
                    screenRect.right.toFloat(), screenRect.bottom - cornerSize, paint)
                
                paint.strokeWidth = 8f
            }
        }
    }
}
