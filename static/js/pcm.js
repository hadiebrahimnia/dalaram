let currentBlock = 1;
let currentTrial = 1;
let currentStage = 'intro'; // intro, practice, main

let practiceCorrect = 0;
let practiceTotal = 0;

let currentCue = null;
let currentStim1 = null;
let currentStim2 = null;
let expectedSequence = null;     // دنبالهٔ پیش‌بینی‌شده توسط cue
let actualSequence = null;       // دنبالهٔ واقعی ارائه‌شده (ممکن است inconsistent باشد)
let categoryStim1 = null;
let categoryStim2 = null;

let valenceStartTime = null;
let ratingStep = 0; // 0: stim1, 1: stim2, 2: sequence

const audio = $("#audio-player")[0];

// ------------------- توابع کمکی -------------------

function getCsrfToken() {
  const name = "csrftoken";
  let cookieValue = null;
  if (document.cookie && document.cookie !== "") {
    const cookies = document.cookie.split(";");
    for (let i = 0; i < cookies.length; i++) {
      const cookie = cookies[i].trim();
      if (cookie.substring(0, name.length + 1) === (name + "=")) {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
}

function showFixation(callback, delay = 1000) {
  $("#fixation").removeClass("hidden");
  setTimeout(() => {
    $("#fixation").addClass("hidden");
    if (callback) callback();
  }, delay);
}

function playSound(url, next) {
  audio.src = url;
  audio.play().catch(e => console.error("خطا در پخش صدا:", e));
  audio.onended = () => setTimeout(next, 500);
}

// ------------------- شروع تریال -------------------
function startTrial() {
  // انتخاب تصادفی یک cue از لیست URLها
  currentCue = cueUrls[Math.floor(Math.random() * cueUrls.length)];


  // گرفتن دنبالهٔ مورد انتظار مستقیماً از mapping (کلید = URL کامل)
  expectedSequence = cuesMapping[currentCue];

  // بررسی اینکه mapping درست کار می‌کنه (در صورت undefined بودن، خطا می‌ده)
  if (!expectedSequence) {
    console.error("Cue mapping پیدا نشد برای:", currentCue);
    console.log("موجود در cuesMapping:", Object.keys(cuesMapping));
    alert("خطا در بارگذاری کیوها. لطفاً صفحه را رفرش کنید.");
    return;
  }

  // تصمیم‌گیری دربارهٔ سازگار یا ناسازگار بودن
  const isInconsistent = Math.random() < INCONSISTENT_RATIO;

  let actualSequence;
  if (isInconsistent) {
    // انتخاب یکی از دو دنبالهٔ دیگر (نه expected)
    const allSequences = [...new Set(Object.values(cuesMapping))]; // فقط 3 تا منحصر به فرد
    const others = allSequences.filter(s => s !== expectedSequence);
    actualSequence = others[Math.floor(Math.random() * others.length)];
  } else {
    actualSequence = expectedSequence;
  }

  // تجزیه دنباله واقعی برای انتخاب محرک‌ها
  const [cat1, cat2] = actualSequence.split('-');
  categoryStim1 = cat1 === 'Neutral' ? 'Neutral' : 'Negative';
  categoryStim2 = cat2 === 'Neutral' ? 'Neutral' : 'Negative';

  const pool1 = categoryStim1 === 'Neutral' ? neutralUrls : negativeUrls;
  const pool2 = categoryStim2 === 'Neutral' ? neutralUrls : negativeUrls;

  currentStim1 = pool1[Math.floor(Math.random() * pool1.length)];
  currentStim2 = pool2[Math.floor(Math.random() * pool2.length)];

  // پخش توالی
  showFixation(() => {
    playSound(currentCue, () => {
      playSound(currentStim1, () => {
        playSound(currentStim2, () => {
          if (currentStage === 'practice') {
            showPracticeChoice();
          } else {
            ratingStep = 0;
            showValenceRating("لطفاً خوشایندی محرک اول را رتبه‌بندی کنید");
          }
        });
      });
    });
  });
}

function showPracticeChoice() {
  $("#practice-choice").removeClass("hidden");
  $("#practice-feedback").text("");
}

function showValenceRating(question) {
  $("#valence-question").text(question);
  $("#valence-rating").removeClass("hidden");
  valenceStartTime = Date.now();
}

// ------------------- هندل کردن رتبه‌بندی -------------------
function setupValenceButtons(callback) {
  $(".sam-btn").off("click").on("click", function () {
    $(".sam-btn").removeClass("selected");
    $(this).addClass("selected");
    const value = parseInt($(this).data("value"));
    const rt = Date.now() - valenceStartTime;
    callback(value, rt);
  });
}

// پشتیبانی کیبورد
$(document).off("keydown.pcm").on("keydown.pcm", function (e) {
  if ($("#valence-rating").is(":visible") && e.key >= "1" && e.key <= "9") {
    const val = parseInt(e.key);
    $(`#valence-rating .sam-btn[data-value="${val}"]`).trigger("click");
  }
});

// ------------------- رویدادها -------------------

// شروع مرحله تمرینی
$("#start-practice").click(() => {
  $("#intro").addClass("hidden");
  currentStage = 'practice';
  practiceCorrect = practiceTotal = 0;
  startTrial();
});

// انتخاب توالی در مرحله تمرینی
$(".sequence-btn").click(function () {
  const userChoice = $(this).data("seq");
  const correct = userChoice === expectedSequence;

  practiceTotal++;
  if (correct) practiceCorrect++;

  $("#practice-feedback")
    .text(correct ? "درست!" : "غلط!")
    .css("color", correct ? "green" : "red");

  // === اضافه کردن ذخیره‌سازی داده تمرین ===
  const practiceData = {
    is_practice: true,
    practice_trial: practiceTotal,
    cue: currentCue,
    stimulus1: currentStim1,
    stimulus2: currentStim2,
    user_response: userChoice,
    practice_correct: correct
  };

  $.ajax({
    type: "POST",
    url: "",  // یا URL مخصوص تمرین اگر جدا دارید
    data: JSON.stringify(practiceData),
    contentType: "application/json",
    headers: { "X-CSRFToken": getCsrfToken() },
    success: () => console.log(`تمرین تریال ${practiceTotal} ذخیره شد`),
    error: (err) => console.error("خطا در ذخیره تمرین:", err)
  });
  // ==========================================

  setTimeout(() => {
    $("#practice-choice").addClass("hidden");
    $("#practice-feedback").text("");

    if (practiceTotal >= PRACTICE_TRIALS) {
      if (practiceCorrect / practiceTotal >= PRACTICE_THRESHOLD) {
        $("#main-intro").removeClass("hidden");
      } else {
        alert("دقت کافی نبود. مرحله تمرینی دوباره شروع می‌شود.");
        practiceCorrect = practiceTotal = 0;
        startTrial();
      }
    } else {
      startTrial();
    }
  }, 1500);
});

// شروع آزمون اصلی
$("#start-main").click(() => {
  $("#main-intro").addClass("hidden");
  currentStage = 'main';
  currentBlock = 1;
  currentTrial = 1;
  startTrial();
});

// رتبه‌بندی در مرحله اصلی
setupValenceButtons((value, rt) => {
  const data = {
    block: currentBlock,
    trial: currentTrial,
    cue: currentCue,
    stimulus1: currentStim1,
    stimulus2: currentStim2,
    expected_sequence: expectedSequence,           // دنبالهٔ پیش‌بینی‌شده توسط cue
    category_stim1: categoryStim1,
    category_stim2: categoryStim2,
  };

  if (ratingStep === 0) {
    data.valence_stim1 = value;
    data.valence_rt_stim1 = rt;
    ratingStep++;
    $("#valence-rating").addClass("hidden");
    setTimeout(() => showValenceRating("لطفاً خوشایندی محرک دوم را رتبه‌بندی کنید"), 600);
  } else if (ratingStep === 1) {
    data.valence_stim2 = value;
    data.valence_rt_stim2 = rt;
    ratingStep++;
    $("#valence-rating").addClass("hidden");
    setTimeout(() => showValenceRating("لطفاً خوشایندی کل توالی را رتبه‌بندی کنید"), 600);
  } else {
    data.valence_sequence = value;
    data.valence_rt_sequence = rt;

    // ارسال به سرور
    $.ajax({
      type: "POST",
      url: "",
      data: JSON.stringify(data),
      contentType: "application/json",
      headers: { "X-CSRFToken": getCsrfToken() },
      success: () => console.log(`بلاک ${currentBlock} - تریال ${currentTrial} ذخیره شد`),
      error: (err) => console.error("خطا در ذخیره:", err)
    });

    // ادامه یا پایان
    $("#valence-rating").addClass("hidden");
    currentTrial++;

    if (currentTrial > TRIALS_PER_BLOCK) {
      currentTrial = 1;
      currentBlock++;
    }

    if (currentBlock > NUM_BLOCKS) {
      $("#thanks").removeClass("hidden");
    } else {
      setTimeout(startTrial, 1000);
    }
  }
});

// فول‌اسکرین هنگام شروع
$("#start-practice, #start-main").click(function () {
  const elem = document.documentElement;
  if (elem.requestFullscreen) elem.requestFullscreen();
  else if (elem.mozRequestFullScreen) elem.mozRequestFullScreen();
  else if (elem.webkitRequestFullscreen) elem.webkitRequestFullscreen();
  else if (elem.msRequestFullscreen) elem.msRequestFullscreen();
});