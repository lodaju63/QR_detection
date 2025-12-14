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
            // 이미 변환된 화면 좌표를 그대로 사용
            // 바코드 박스 그리기
            canvas.drawRect(rect, paint)
                
                // 모서리에 작은 사각형 그리기 (시각적 강조)
                val cornerSize = 30f
                paint.strokeWidth = 6f
                
                // 왼쪽 위
                canvas.drawLine(rect.left.toFloat(), rect.top.toFloat(),
                    rect.left + cornerSize, rect.top.toFloat(), paint)
                canvas.drawLine(rect.left.toFloat(), rect.top.toFloat(),
                    rect.left.toFloat(), rect.top + cornerSize, paint)
                
                // 오른쪽 위
                canvas.drawLine(rect.right.toFloat(), rect.top.toFloat(),
                    rect.right - cornerSize, rect.top.toFloat(), paint)
                canvas.drawLine(rect.right.toFloat(), rect.top.toFloat(),
                    rect.right.toFloat(), rect.top + cornerSize, paint)
                
                // 왼쪽 아래
                canvas.drawLine(rect.left.toFloat(), rect.bottom.toFloat(),
                    rect.left + cornerSize, rect.bottom.toFloat(), paint)
                canvas.drawLine(rect.left.toFloat(), rect.bottom.toFloat(),
                    rect.left.toFloat(), rect.bottom - cornerSize, paint)
                
                // 오른쪽 아래
                canvas.drawLine(rect.right.toFloat(), rect.bottom.toFloat(),
                    rect.right - cornerSize, rect.bottom.toFloat(), paint)
                canvas.drawLine(rect.right.toFloat(), rect.bottom.toFloat(),
                    rect.right.toFloat(), rect.bottom - cornerSize, paint)
                
                paint.strokeWidth = 8f
        }
    }
}
