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
        fail: "请求失败，状态码："
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
        fail: "Request failed, status: "
    }
};

function getLang() {
    // 优先 URL ?lang=，否则浏览器语言
    const urlLang = new URLSearchParams(window.location.search).get('lang');
    if (urlLang && LANGS[urlLang]) return urlLang;
    const nav = navigator.language || navigator.userLanguage;
    if (nav.startsWith('zh')) return 'zh';
    return 'en';
}

const LANG = LANGS[getLang()];

document.addEventListener('DOMContentLoaded', function() {
    // 动态设置文本
    document.title = LANG.title;
    document.querySelector('h2').textContent = LANG.title;
    document.querySelector('label[for="pdfFile"]').textContent = LANG.select;
    document.querySelector('.btn-primary').textContent = LANG.upload;

    const form = document.getElementById('uploadForm');
    const logBox = document.getElementById('logBox');
    form.addEventListener('submit', function(e) {
        e.preventDefault();
        logBox.innerHTML = '';
        const fileInput = document.getElementById('pdfFile');
        if (!fileInput.files.length) {
            log(LANG.choose);
            return;
        }
        const file = fileInput.files[0];
        log(LANG.uploading);
        const formData = new FormData();
        formData.append('pdfFile', file);
        fetch('http://127.0.0.1:8088/api/v1/podcasts', {
            method: 'POST',
            body: formData,
            headers: {
                // 预留JWT认证头部，实际可从本地存储或登录后获取
                'Authorization': localStorage.getItem('token') ? 'Bearer ' + localStorage.getItem('token') : ''
            }
        }).then(response => {
            if (response.status === 201) {
                log(LANG.uploaded);
            } else {
                log(LANG.fail + response.status);
            }
            return response.json();
        }).then(data => {
            if (data.message) {
                log(LANG.success + data.message);
                if (data.output_path) {
                    log(LANG.podcast + data.output_path);
                }
            } else if (data.error) {
                log(LANG.error + data.error);
            }
        }).catch(err => {
            log(LANG.neterr + err);
        });
    });
    function log(msg) {
        const p = document.createElement('div');
        p.textContent = msg;
        logBox.appendChild(p);
    }
});