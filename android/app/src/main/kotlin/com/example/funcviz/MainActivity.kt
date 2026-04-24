package com.example.funcviz

import android.annotation.SuppressLint
import android.graphics.Bitmap
import android.os.Bundle
import android.view.KeyEvent
import android.view.View
import android.view.WindowManager
import android.webkit.WebChromeClient
import android.webkit.WebSettings
import android.webkit.WebView
import android.webkit.WebViewClient
import androidx.appcompat.app.AlertDialog
import androidx.appcompat.app.AppCompatActivity
import com.example.funcviz.databinding.ActivityMainBinding

class MainActivity : AppCompatActivity() {

    private lateinit var binding: ActivityMainBinding
    private var serverUrl = "http://192.168.1.100:8000"
    private var isLoaded = false

    @SuppressLint("SetJavaScriptEnabled")
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        
        window.addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON)
        
        binding = ActivityMainBinding.inflate(layoutInflater)
        setContentView(binding.root)
        
        setupWebView()
        showServerDialog()
    }

    @SuppressLint("SetJavaScriptEnabled")
    private fun setupWebView() {
        val webView = binding.webView
        val settings = webView.settings
        
        settings.javaScriptEnabled = true
        settings.domStorageEnabled = true
        settings.databaseEnabled = true
        settings.allowFileAccess = true
        settings.allowContentAccess = true
        settings.allowFileAccessFromFileURLs = true
        settings.allowUniversalAccessFromFileURLs = true
        settings.setSupportZoom(true)
        settings.builtInZoomControls = true
        settings.displayZoomControls = false
        settings.useWideViewPort = true
        settings.loadWithOverviewMode = true
        settings.cacheMode = WebSettings.LOAD_DEFAULT
        settings.mediaPlaybackRequiresUserGesture = false
        
        webView.webViewClient = object : WebViewClient() {
            override fun onPageStarted(view: WebView?, url: String?, favicon: Bitmap?) {
                super.onPageStarted(view, url, favicon)
                binding.progressBar.visibility = View.VISIBLE
                binding.statusText.text = "加载中..."
            }

            override fun onPageFinished(view: WebView?, url: String?) {
                super.onPageFinished(view, url)
                binding.progressBar.visibility = View.GONE
                binding.statusLayout.visibility = View.GONE
                isLoaded = true
            }

            override fun onReceivedError(
                view: WebView?,
                errorCode: Int,
                description: String?,
                failingUrl: String?
            ) {
                super.onReceivedError(view, errorCode, description, failingUrl)
                showError(description ?: "未知错误")
            }
        }
        
        webView.webChromeClient = object : WebChromeClient() {
            override fun onProgressChanged(view: WebView?, newProgress: Int) {
                super.onProgressChanged(view, newProgress)
                binding.progressBar.progress = newProgress
            }
        }
    }

    private fun showServerDialog() {
        val builder = AlertDialog.Builder(this)
        builder.setTitle("服务器地址配置")
        builder.setMessage("请输入 Web 服务器地址\n\n格式: http://IP地址:端口")
        
        val input = android.widget.EditText(this)
        input.setText(serverUrl)
        input.hint = "http://192.168.1.100:8000"
        val padding = resources.getDimensionPixelSize(R.dimen.dialog_padding)
        input.setPadding(padding, padding, padding, padding)
        builder.setView(input)
        
        builder.setPositiveButton("连接") { _, _ ->
            val url = input.text.toString().trim()
            if (url.isNotEmpty()) {
                serverUrl = url
                loadUrl()
            }
        }
        
        builder.setNegativeButton("取消") { _, _ ->
            finish()
        }
        
        builder.setCancelable(false)
        builder.show()
    }

    private fun loadUrl() {
        binding.statusLayout.visibility = View.VISIBLE
        binding.statusText.text = "正在连接服务器..."
        binding.progressBar.progress = 0
        
        binding.webView.loadUrl(serverUrl)
    }

    private fun showError(error: String) {
        binding.progressBar.visibility = View.GONE
        binding.statusText.text = "连接失败: $error"
        
        val builder = AlertDialog.Builder(this)
        builder.setTitle("连接失败")
        builder.setMessage("无法连接到服务器: $error\n\n请检查:\n1. 服务器是否已启动\n2. IP地址和端口是否正确\n3. 手机和电脑是否在同一局域网")
        builder.setPositiveButton("重试") { _, _ ->
            showServerDialog()
        }
        builder.setNegativeButton("退出") { _, _ ->
            finish()
        }
        builder.setCancelable(false)
        builder.show()
    }

    override fun onKeyDown(keyCode: Int, event: KeyEvent?): Boolean {
        if (keyCode == KeyEvent.KEYCODE_BACK && binding.webView.canGoBack()) {
            binding.webView.goBack()
            return true
        }
        return super.onKeyDown(keyCode, event)
    }

    override fun onResume() {
        super.onResume()
        binding.webView.onResume()
    }

    override fun onPause() {
        super.onPause()
        binding.webView.onPause()
    }

    override fun onDestroy() {
        binding.webView.destroy()
        super.onDestroy()
    }
}
