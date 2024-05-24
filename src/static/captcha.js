let captcha;

initAliyunCaptcha({
    SceneId: '7ud95im0',
    prefix: '1wp3rx',
    mode: 'embed',
    element: '#captcha-element',
    captchaVerifyCallback: captchaVerifyCallback,
    onBizResultCallback: onBizResultCallback,
    getInstance: getInstance,
    slideStyle: {
      width: 365,
      height: 40,
    },
    language: 'cn',
    immediate: true,
    region: 'cn'
});

function getInstance(instance) {
    captcha = instance;
}

async function captchaVerifyCallback(captchaVerifyParam) {
    const request_id = await fetch(window.location.origin + '/captcha-request', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            'captchaVerifyParam': captchaVerifyParam
        })
    }).then(function(response){
      return response.text();
    })
    const passed = request_id != 'NO'
    const verifyResult = {
        captchaResult: passed,
        bizResult: null,
    };
    if (passed) {
        window.location.href = window.location.origin + '?token=' + request_id;
    }
    return verifyResult;
}

function onBizResultCallback(bizResult) {
    
}