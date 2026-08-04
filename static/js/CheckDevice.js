// ======================================================
// تنظیمات سیاست دستگاه
// ======================================================
const DEVICE_POLICY = {
  allowedDeviceTypes: ['Desktop','Mobile','Tablet'],   // موبایل هم مجاز است (ولی باید افقی شود)
  allowedOS: [],
  allowedBrowsers: ['Chrome', 'Firefox'],
  minScreenWidth: 0,                           // برای موبایل محدودیت عرض نمی‌گذاریم
  allowTouchDevices: true
};

// ======================================================
// تشخیص دستگاه
// ======================================================
function detectDevice() {
  const ua = navigator.userAgent.toLowerCase();
  const width = window.innerWidth;
  const height = window.innerHeight;
  const isTouch = 'ontouchstart' in window || navigator.maxTouchPoints > 0;

  let os = 'Unknown';
  if (/windows/.test(ua)) os = 'Windows';
  else if (/macintosh|mac os x/.test(ua)) os = 'macOS';
  else if (/android/.test(ua)) os = 'Android';
  else if (/iphone|ipad|ipod/.test(ua)) os = 'iOS';
  else if (/linux/.test(ua)) os = 'Linux';

  let browser = 'Unknown';
  if (/edg/.test(ua)) browser = 'Edge';
  else if (/chrome/.test(ua) && !/edg/.test(ua)) browser = 'Chrome';
  else if (/firefox/.test(ua)) browser = 'Firefox';
  else if (/safari/.test(ua) && !/chrome/.test(ua)) browser = 'Safari';

  let deviceType = 'Desktop';
  if (/mobile|android|iphone|ipod/.test(ua) || (isTouch && width < 768)) {
    deviceType = 'Mobile';
  } else if (/ipad|tablet/.test(ua) || (isTouch && width >= 768 && width <= 1024)) {
    deviceType = 'Tablet';
  }

  return {
    device_type: deviceType,
    os,
    browser,
    screen_width: width,
    screen_height: height,
    is_touch: isTouch,
    user_agent: navigator.userAgent
  };
}

// ======================================================
// بررسی مجاز بودن
// ======================================================
function checkDeviceAllowed(info) {
  const policy = DEVICE_POLICY;
  const problems = [];

  if (policy.allowedDeviceTypes.length && !policy.allowedDeviceTypes.includes(info.device_type)) {
    problems.push('نوع دستگاه');
  }
  if (policy.allowedOS.length && !policy.allowedOS.includes(info.os)) {
    problems.push('سیستم‌عامل');
  }
  if (policy.allowedBrowsers.length && !policy.allowedBrowsers.includes(info.browser)) {
    problems.push('مرورگر');
  }
  if (info.screen_width < policy.minScreenWidth) {
    problems.push('اندازه صفحه');
  }
  if (!policy.allowTouchDevices && info.is_touch) {
    problems.push('دستگاه لمسی');
  }

  return {
    allowed: problems.length === 0,
    problems
  };
}

// ======================================================
// نمایش پیام دستگاه غیرمجاز
// ======================================================
function showBlockedMessage(info) {
  const infoEl = document.getElementById('device-blocked-info');
  const allowedEl = document.getElementById('device-blocked-allowed');
  const blockedEl = document.getElementById('device-blocked');

  if (!infoEl || !allowedEl || !blockedEl) return;

  // پر کردن اطلاعات فعلی دستگاه
  infoEl.innerHTML = `
    <div><strong>نوع دستگاه:</strong> ${info.device_type}</div>
    <div><strong>سیستم‌عامل:</strong> ${info.os}</div>
    <div><strong>مرورگر:</strong> ${info.browser}</div>
    <div><strong>عرض صفحه:</strong> ${info.screen_width}px</div>
  `;

  // پر کردن لیست شرایط مجاز
  let allowedList = '<ul>';
  if (DEVICE_POLICY.allowedDeviceTypes.length) {
    allowedList += `<li>نوع دستگاه: <strong>${DEVICE_POLICY.allowedDeviceTypes.join(' یا ')}</strong></li>`;
  }
  if (DEVICE_POLICY.allowedOS.length) {
    allowedList += `<li>سیستم‌عامل: <strong>${DEVICE_POLICY.allowedOS.join(' یا ')}</strong></li>`;
  }
  if (DEVICE_POLICY.allowedBrowsers.length) {
    allowedList += `<li>مرورگر: <strong>${DEVICE_POLICY.allowedBrowsers.join(' یا ')}</strong></li>`;
  }
  if (DEVICE_POLICY.minScreenWidth > 0) {
    allowedList += `<li>حداقل عرض صفحه: <strong>${DEVICE_POLICY.minScreenWidth} پیکسل</strong></li>`;
  }
  if (!DEVICE_POLICY.allowTouchDevices) {
    allowedList += `<li>دستگاه نباید لمسی باشد</li>`;
  }
  allowedList += '</ul>';

  allowedEl.innerHTML = allowedList;

  // نمایش پیام
  blockedEl.style.display = 'flex';
}

// ======================================================
// تابع اصلی
// ======================================================
function initDeviceCheck(stageName) {
  const info = detectDevice();
  const check = checkDeviceAllowed(info);

  // ۱. اگر دستگاه غیرمجاز بود
  if (!check.allowed) {
    showBlockedMessage(info);
    return false; // متوقف کن
  }

  // ۲. ثبت لاگ دستگاه
  const payload = {
    stage: stageName,
    device_type: info.device_type,
    os: info.os,
    browser: info.browser,
    screen_width: info.screen_width,
    screen_height: info.screen_height,
    is_touch: info.is_touch,
    audio_volume: window.audioVolume || null
  };

  fetch('/save-device-log/', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-CSRFToken': getCsrfToken()
    },
    body: JSON.stringify(payload)
  }).catch(err => console.error('Error saving device log:', err));

  // ۳. اگر موبایل بود → پیام چرخش را مدیریت کن
  if (info.device_type === 'Mobile') {
    updateRotateMessage();
    window.addEventListener('resize', updateRotateMessage);
    window.addEventListener('orientationchange', updateRotateMessage);
  }

  return true;
}

// ======================================================
// مدیریت پیام چرخش گوشی (با استایل داخلی)
// ======================================================
function isLandscape() {
  return window.innerWidth > window.innerHeight;
}

function updateRotateMessage() {
  let rotateEl = document.getElementById('rotate-device');

  // اگر المان وجود نداشت، آن را بساز
  if (!rotateEl) {
    rotateEl = document.createElement('div');
    rotateEl.id = 'rotate-device';
    document.body.appendChild(rotateEl);
  }

  // استایل را همیشه اعمال کن
  rotateEl.innerHTML = `
    <style>
      #rotate-device {
        position: fixed;
        inset: 0;
        background: #0f172a;
        color: white;
        display: none;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        text-align: center;
        z-index: 99998;
        padding: 20px;
        direction: rtl;
        font-family: Tahoma, sans-serif;
      }
      #rotate-device i {
        font-size: 64px;
        margin-bottom: 20px;
        display: block;
      }
      #rotate-device h3 {
        font-size: 1.4rem;
        margin: 0 0 12px 0;
        font-weight: 700;
      }
      #rotate-device p {
        font-size: 1rem;
        opacity: 0.85;
        margin: 0;
        max-width: 280px;
        line-height: 1.6;
      }
    </style>
    <i>↻</i>
    <h3>لطفاً گوشی را بچرخانید</h3>
    <p>برای تجربه بهتر، صفحه را به حالت افقی ببرید</p>
  `;

  if (isLandscape()) {
    rotateEl.style.display = 'none';
  } else {
    rotateEl.style.display = 'flex';
  }
}

// ======================================================
// تابع اصلی (بدون تغییر زیاد)
// ======================================================
function initDeviceCheck(stageName) {
  const info = detectDevice();
  const check = checkDeviceAllowed(info);

  // ۱. اگر دستگاه غیرمجاز بود
  if (!check.allowed) {
    showBlockedMessage(info);
    return false;
  }

  // ۲. ثبت لاگ دستگاه
  const payload = {
    stage: stageName,
    device_type: info.device_type,
    os: info.os,
    browser: info.browser,
    screen_width: info.screen_width,
    screen_height: info.screen_height,
    is_touch: info.is_touch,
    audio_volume: window.audioVolume || null
  };

  fetch('/save-device-log/', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-CSRFToken': getCsrfToken()
    },
    body: JSON.stringify(payload)
  }).catch(err => console.error('Error saving device log:', err));

  // ۳. اگر موبایل بود → پیام چرخش را مدیریت کن
  if (info.device_type === 'Mobile') {
    updateRotateMessage();
    window.addEventListener('resize', updateRotateMessage);
    window.addEventListener('orientationchange', updateRotateMessage);
  }

  return true;
}