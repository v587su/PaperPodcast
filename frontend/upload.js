const LANGS = {
    zh: {
        title: "PDF转播客 Demo",
        select: "选择PDF文件：",
        upload: "上传并生成播客",
        choose: "请选择一个PDF文件",
        uploading: "正在上传文件...",
        uploaded: "文件上传完成，正在处理...",
        success: "处理成功：",
        podcast: "播客文件已生成：",
        error: "发生错误：",
        neterr: "网络或服务器错误：",
        fail: "请求失败，状态码：",
        download: "下载播客",
        processing_time: "播客生成通常需要 3-5 分钟",
        progress: {
            script_start: "开始生成播客脚本...",
            script_success: "播客脚本生成成功",
            audio_start: "开始合成语音...",
            audio_success: "语音合成成功",
            complete: "播客生成完成！"
        }
    },
    en: {
        title: "PDF to Podcast Demo",
        select: "Select PDF file:",
        upload: "Upload and Generate Podcast",
        choose: "Please select a PDF file",
        uploading: "Uploading file...",
        uploaded: "File uploaded, processing...",
        success: "Success: ",
        podcast: "Podcast file generated: ",
        error: "Error: ",
        neterr: "Network or server error: ",
        fail: "Request failed, status: ",
        download: "Download Podcast",
        processing_time: "Podcast generation typically takes 3-5 minutes",
        progress: {
            script_start: "Generating podcast script...",
            script_success: "Script generated successfully",
            audio_start: "Starting audio synthesis...",
            audio_success: "Audio synthesis completed",
            complete: "Podcast generation complete!"
        }
    }
};

// 保存当前处理状态
let currentState = {
    isProcessing: false,
    currentFile: null,
    ws: null
};

function getLang() {
    // 优先 URL ?lang=，否则浏览器语言
    const urlLang = new URLSearchParams(window.location.search).get('lang');
    if (urlLang && LANGS[urlLang]) return urlLang;
    const nav = navigator.language || navigator.userLanguage;
    if (nav.startsWith('zh')) return 'zh';
    return 'en';
}

function setLang(lang) {
    if (LANGS[lang]) {
        // 保存当前状态
        const wasProcessing = currentState.isProcessing;
        const currentFile = currentState.currentFile;
        const ws = currentState.ws;
        
        // 更新URL中的语言参数
        const url = new URL(window.location.href);
        url.searchParams.set('lang', lang);
        window.history.pushState({}, '', url);
        
        // 重新加载页面但保持状态
        window.location.reload();
        
        // 恢复状态
        if (wasProcessing && currentFile) {
            currentState.isProcessing = true;
            currentState.currentFile = currentFile;
            currentState.ws = ws;
        }
    }
}

const LANG = LANGS[getLang()];

document.addEventListener('DOMContentLoaded', function() {
    // 动态设置文本
    document.title = LANG.title;
    document.querySelector('h2').textContent = LANG.title;
    document.querySelector('label[for="pdfFile"]').textContent = LANG.select;
    document.querySelector('.btn-primary').textContent = LANG.upload;

    // 设置语言切换按钮的点击事件
    document.querySelectorAll('.lang-switch .btn-link').forEach(btn => {
        btn.onclick = function() {
            const lang = this.getAttribute('data-lang');
            if (lang) {
                setLang(lang);
            }
        };
    });

    const form = document.getElementById('uploadForm');
    const logBox = document.getElementById('logBox');

    function connectWebSocket() {
        if (currentState.ws) {
            currentState.ws.close();
        }
        
        currentState.ws = new WebSocket('ws://127.0.0.1:8088/ws/progress');
        
        currentState.ws.onmessage = function(event) {
            const data = JSON.parse(event.data);
            if (data.type === 'progress') {
                updateProgress(data.stage, data.message);
            }
        };

        currentState.ws.onclose = function() {
            console.log('WebSocket connection closed');
            if (currentState.isProcessing) {
                // 如果仍在处理中，尝试重新连接
                setTimeout(connectWebSocket, 1000);
            }
        };

        currentState.ws.onerror = function(error) {
            console.error('WebSocket error:', error);
        };
    }

    function updateProgress(stage, message) {
        const progressDiv = document.createElement('div');
        progressDiv.className = 'progress-item';
        
        const icon = document.createElement('span');
        icon.className = 'progress-icon';
        
        const text = document.createElement('span');
        text.textContent = message || LANG.progress[stage];
        
        progressDiv.appendChild(icon);
        progressDiv.appendChild(text);
        logBox.appendChild(progressDiv);
        
        // 如果是完成状态，添加complete类
        if (stage === 'complete') {
            progressDiv.classList.add('complete');
            currentState.isProcessing = false;
        }
        
        // 滚动到底部
        logBox.scrollTop = logBox.scrollHeight;
    }

    form.addEventListener('submit', function(e) {
        e.preventDefault();
        if (currentState.isProcessing) {
            return; // 如果正在处理中，不响应新的提交
        }
        
        logBox.innerHTML = '';
        const fileInput = document.getElementById('pdfFile');
        if (!fileInput.files.length) {
            log(LANG.choose);
            return;
        }
        
        currentState.isProcessing = true;
        currentState.currentFile = fileInput.files[0];
        
        const file = currentState.currentFile;
        log(LANG.uploading);
        
        // 添加处理时间提示
        const timeHint = document.createElement('div');
        timeHint.className = 'processing-time-hint';
        timeHint.textContent = LANG.processing_time;
        logBox.appendChild(timeHint);
        
        // 连接WebSocket
        connectWebSocket();
        
        const formData = new FormData();
        formData.append('pdfFile', file);
        fetch('http://127.0.0.1:8088/api/v1/podcasts', {
            method: 'POST',
            body: formData,
            headers: {
                'Authorization': localStorage.getItem('token')
                    ? 'Bearer ' + localStorage.getItem('token')
                    : 'Bearer testtoken'
            }
        }).then(response => {
            if (response.status === 201) {
                log(LANG.uploaded);
            } else {
                log(LANG.fail + response.status);
                currentState.isProcessing = false;
            }
            return response.json();
        }).then(data => {
            if (data.message) {
                log(LANG.success + data.message);
                if (data.output_path) {
                    const filename = data.output_path.split('/').pop();
                    log(LANG.podcast + data.output_path);
                    // 添加下载按钮
                    const downloadBtn = document.createElement('button');
                    downloadBtn.textContent = LANG.download;
                    downloadBtn.className = 'btn btn-success mt-2';
                    downloadBtn.onclick = () => {
                        window.location.href = `http://127.0.0.1:8088/api/v1/podcasts/download/${filename}`;
                    };
                    logBox.appendChild(downloadBtn);
                }
            } else if (data.error) {
                log(LANG.error + data.error);
                currentState.isProcessing = false;
            }
        }).catch(err => {
            log(LANG.neterr + err);
            currentState.isProcessing = false;
        });
    });

    function log(msg) {
        const p = document.createElement('div');
        p.textContent = msg;
        logBox.appendChild(p);
    }
});