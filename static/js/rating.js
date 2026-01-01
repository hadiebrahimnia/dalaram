// فعال کردن تمام صفحه (Fullscreen) هنگام شروع
$("#start-practice").click(() => {
  const elem = document.documentElement;
  if (elem.requestFullscreen) {
    elem.requestFullscreen();
  } else if (elem.mozRequestFullScreen) {
    elem.mozRequestFullScreen();
  } else if (elem.webkitRequestFullscreen) {
    elem.webkitRequestFullscreen();
  } else if (elem.msRequestFullscreen) {
    elem.msRequestFullscreen();
  }

  $("#practice-note").addClass("hidden");
  showFixation();
});

let allFiles = practiceFiles.concat(mainFiles);
let currentIndex = 0;
let valence = null;
let arousal = null;
let valenceStartTime = null;
let arousalStartTime = null;
let valenceTimeout = null;
let arousalTimeout = null;
const RESPONSE_TIME_LIMIT = 3000; // زمان محدودیت در مرحله آزمایشی (میلی‌ثانیه)

const CSRF_TOKEN = "{{ csrf_token }}";

// تابع تنظیم دکمه‌های SAM (Valence و Arousal)
function setupButtons(containerId, callback) {
  $(`${containerId} .sam-btn`)
    .off("click") // جلوگیری از بایند شدن چندباره
    .on("click", function () {
      $(`${containerId} .sam-btn`).removeClass("selected");
      $(this).addClass("selected");
      callback(parseInt($(this).data("value")));
    });
}

// نمایش فیکسیشن (+)
function showFixation() {
  $("#fixation").removeClass("hidden");
  setTimeout(() => {
    $("#fixation").addClass("hidden");
    playAudio();
  }, 1000);
}

// پخش صدا
function playAudio() {
  const file = allFiles[currentIndex];
  $("#audio-player").attr("src", file);
  const audio = $("#audio-player")[0];
  audio.play();

  // بعد از ۶ ثانیه صدا را متوقف کرده و صفحه Valence را نشان می‌دهیم
  setTimeout(() => {
    audio.pause();
    audio.currentTime = 0;
    showValence();
  }, 6000);
}

// نمایش پیام "لطفاً سریع‌تر پاسخ دهید!" (فقط در مرحله آزمایشی)
function showFeedback() {
  const feedback = $("#feedback-message");
  feedback.removeClass("hidden").css("opacity", "1");

  setTimeout(() => {
    feedback.css("opacity", "0");
    setTimeout(() => feedback.addClass("hidden"), 400);
  }, 1800);
}

// صفحه خوشایندی (Valence)
function showValence() {
  $("#valence-rating").removeClass("hidden");
  valenceStartTime = Date.now();

  const isPractice = currentIndex < practiceFiles.length;

  // در مرحله آزمایشی: محدودیت زمانی + بازخورد
  if (isPractice) {
    valenceTimeout = setTimeout(() => {
      showFeedback();
      saveAndNext();
    }, RESPONSE_TIME_LIMIT);
  }

  setupButtons("#valence-rating", (val) => {
    valence = val;
    const valenceRT = Date.now() - valenceStartTime;
    if (isPractice) clearTimeout(valenceTimeout);
    setTimeout(() => showArousal(valenceRT), 400);
  });
}

// صفحه برانگیختگی (Arousal)
function showArousal(valenceRT = null) {
  $("#valence-rating").addClass("hidden");
  $("#arousal-rating").removeClass("hidden");
  arousalStartTime = Date.now();

  const isPractice = currentIndex < practiceFiles.length;

  if (isPractice) {
    arousalTimeout = setTimeout(() => {
      showFeedback();
      saveAndNext(valenceRT);
    }, RESPONSE_TIME_LIMIT);
  }

  setupButtons("#arousal-rating", (val) => {
    arousal = val;
    const arousalRT = Date.now() - arousalStartTime;
    if (isPractice) clearTimeout(arousalTimeout);
    saveAndNext(valenceRT, arousalRT);
  });
}

// ذخیره پاسخ و رفتن به محرک بعدی
function saveAndNext(valenceRT = null, arousalRT = null) {
  clearTimeout(valenceTimeout);
  clearTimeout(arousalTimeout);
  $("#valence-rating, #arousal-rating").addClass("hidden");

  const file = allFiles[currentIndex];
  const isPractice = currentIndex < practiceFiles.length;

  function getCsrfToken() {
    const name = "csrftoken";
    let cookieValue = null;
    if (document.cookie && document.cookie !== "") {
      const cookies = document.cookie.split(";");
      for (let i = 0; i < cookies.length; i++) {
        const cookie = cookies[i].trim();
        if (cookie.substring(0, name.length + 1) === name + "=") {
          cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
          break;
        }
      }
    }
    return cookieValue;
  }

  // فقط در مرحله اصلی پاسخ‌ها را به سرور ارسال می‌کنیم
  if (!isPractice) {
    $.ajax({
      type: "POST",
      url: "", // یا URL کامل اگر لازم بود
      data: JSON.stringify({
        audio_file: file,
        valence: valence,
        arousal: arousal,
        valence_rt: valence !== null ? valenceRT : null,
        arousal_rt: arousal !== null ? arousalRT : null,
      }),
      contentType: "application/json",
      headers: {
        "X-CSRFToken": getCsrfToken(), // ← فقط این کافی است
      },
      success: () => console.log(`ذخیره شد: ${file}`),
      error: (err) => {
        console.error("خطا در ذخیره:", err);
        if (err.status === 403) {
          alert("خطای CSRF. صفحه را رفرش کنید و دوباره امتحان کنید.");
        }
      },
    });
  }

  currentIndex++;

  // اگر مرحله آزمایشی تمام شد → نمایش صفحه توضیحی قبل از آزمون اصلی
  if (currentIndex === practiceFiles.length) {
    $("#main-note").removeClass("hidden");
    return; // منتظر کلیک کاربر برای شروع مرحله اصلی
  }

  // اگر هنوز محرک داریم → ادامه
  if (currentIndex < allFiles.length) {
    valence = arousal = null;
    showFixation();
  } else {
    // پایان آزمون کامل
    $("#thanks").removeClass("hidden");
  }
}

// شروع آزمون اصلی بعد از صفحه توضیحی
$("#start-main").click(() => {
  $("#main-note").addClass("hidden");
  valence = arousal = null;
  showFixation();
});

// پشتیبانی از کیبورد (1 تا 9)
$(document).on("keydown", function (e) {
  if ($("#valence-rating").is(":visible") && e.key >= "1" && e.key <= "9") {
    const val = parseInt(e.key);
    $("#valence-rating .sam-btn").removeClass("selected");
    $(`#valence-rating .sam-btn[data-value="${val}"]`).addClass("selected");
    valence = val;
    const valenceRT = Date.now() - valenceStartTime;
    clearTimeout(valenceTimeout);
    setTimeout(() => showArousal(valenceRT), 400);
  } else if (
    $("#arousal-rating").is(":visible") &&
    e.key >= "1" &&
    e.key <= "9"
  ) {
    const val = parseInt(e.key);
    $("#arousal-rating .sam-btn").removeClass("selected");
    $(`#arousal-rating .sam-btn[data-value="${val}"]`).addClass("selected");
    arousal = val;
    const arousalRT = Date.now() - arousalStartTime;
    clearTimeout(arousalTimeout);
    saveAndNext(valenceRT, arousalRT);
  }
});
