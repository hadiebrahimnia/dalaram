let currentBlock = CURRENT_BLOCK_INIT;
let currentTrial = CURRENT_TRIAL_INIT;
let currentStage = INITIAL_STAGE;
let practiceCorrect = PRACTICE_CORRECT_INIT;
let practiceTotal = PRACTICE_TOTAL_INIT;
let valencePracticeTrial = VALENCE_PRACTICE_COMPLETED_COUNT + 1;
let catchTrialCountInBlock = 0;

let currentCue = null;
let currentStim1 = null;
let currentStim2 = null;
let expectedSequence = null;
let actualSequence = null;
let categoryStim1 = null;
let categoryStim2 = null;

let trialValenceStim1 = null, trialValenceRtStim1 = null;
let trialValenceStim2 = null, trialValenceRtStim2 = null;
let trialValenceSequence = null, trialValenceRtSequence = null;

let valenceStartTime = null;
let ratingStep = 0;
let responseTimer = null;
const RESPONSE_TIMEOUT = 4000;

let currentReratingIndex = RERATING_COMPLETED_COUNT;
let reratingValence = null, reratingArousal = null;
let reratingValenceStart = null, reratingArousalStart = null;

const audio = $("#audio-player")[0];

// توابع کمکی
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

function showFixation(callback, delay = 1000) {
  $("#fixation").removeClass("hidden");
  setTimeout(() => {
    $("#fixation").addClass("hidden");
    if (callback) callback();
  }, delay);
}

function playSound(url, next) {
  audio.src = url;
  audio.play().catch(e => console.error("خطا در پخش:", e));
  audio.onended = () => setTimeout(next, 500);
}

function clearResponseTimer() {
  if (responseTimer) clearTimeout(responseTimer);
  responseTimer = null;
}

// شروع تریال
function startTrial() {
  // انتخاب کیو و توالی
  currentCue = cueUrls[Math.floor(Math.random() * cueUrls.length)];
  expectedSequence = cuesMapping[currentCue];

  // تعیین توالی واقعی
  if (currentStage === "practice" || currentStage === "valence_practice") {
    actualSequence = expectedSequence;
  } else {
    const isInconsistent = Math.random() < INCONSISTENT_RATIO;
    if (isInconsistent) {
      const others = Object.values(cuesMapping).filter(s => s !== expectedSequence);
      actualSequence = others[Math.floor(Math.random() * others.length)];
    } else {
      actualSequence = expectedSequence;
    }
  }

  const [cat1, cat2] = actualSequence.split("-");
  categoryStim1 = cat1;
  categoryStim2 = cat2;

  const pool1 = cat1 === "Neutral" ? neutralUrls : negativeUrls;
  const pool2 = cat2 === "Neutral" ? neutralUrls : negativeUrls;

  currentStim1 = pool1[Math.floor(Math.random() * pool1.length)];
  currentStim2 = pool2[Math.floor(Math.random() * pool2.length)];

  // تشخیص catch trial
  const isCatchTrial = currentStage === "main" &&
                       currentTrial <= CATCH_TRIALS_PER_BLOCK &&
                       catchTrialCountInBlock < CATCH_TRIALS_PER_BLOCK;

  showFixation(() => {
    playSound(currentCue, () => {
      playSound(currentStim1, () => {
        playSound(currentStim2, () => {
          if (isCatchTrial || currentStage === "practice") {
            showPracticeChoiceWithTimer();
            if (isCatchTrial) catchTrialCountInBlock++;
          } else {
            ratingStep = 0;
            showValenceRatingWithTimer("لطفاً خوشایندی محرک اول را رتبه‌بندی کنید");
          }
        });
      });
    });
  });
}

// مرحله تمرینی توالی
function showPracticeChoiceWithTimer() {
  $("#practice-choice").removeClass("hidden");
  $("#practice-feedback").text("").hide();

  responseTimer = setTimeout(handlePracticeTimeout, RESPONSE_TIMEOUT);
}

function handlePracticeTimeout() {
  clearResponseTimer();
  $("#practice-feedback").text("لطفاً سریع‌تر پاسخ دهید!").css("color", "red").show();
  practiceTotal++;
  savePracticeData(null, false);
  setTimeout(() => {
    $("#practice-choice").addClass("hidden");
    checkPracticeCompletion();
  }, 2000);
}

function savePracticeData(userChoice, correct) {
  const data = {
    is_practice: true,
    practice_trial: practiceTotal,
    cue: currentCue,
    stimulus1: currentStim1,
    stimulus2: currentStim2,
    category_stim1: categoryStim1,
    category_stim2: categoryStim2,
    user_response: userChoice,
    practice_correct: correct,
  };
  $.post("", JSON.stringify(data), null, "json").fail(err => console.error(err));
}

// رتبه‌بندی خوشایندی
function showValenceRatingWithTimer(question) {
  $("#valence-question").text(question);
  $("#valence-rating").removeClass("hidden");
  $(".sam-btn").removeClass("selected");
  valenceStartTime = Date.now();

  responseTimer = setTimeout(handleValenceTimeout, RESPONSE_TIMEOUT);
}

function handleValenceTimeout() {
  clearResponseTimer();
  processValenceResponse(null, null);
}

function processValenceResponse(value, rt) {
  clearResponseTimer();
  if (value === null) rt = null;

  if (ratingStep === 0) {
    trialValenceStim1 = value; trialValenceRtStim1 = rt;
  } else if (ratingStep === 1) {
    trialValenceStim2 = value; trialValenceRtStim2 = rt;
  } else if (ratingStep === 2) {
    trialValenceSequence = value; trialValenceRtSequence = rt;
  }

  if (ratingStep < 2) {
    ratingStep++;
    const questions = [
      "لطفاً خوشایندی محرک اول را رتبه‌بندی کنید",
      "لطفاً خوشایندی محرک دوم را رتبه‌بندی کنید",
      "لطفاً خوشایندی کل توالی را رتبه‌بندی کنید"
    ];
    setTimeout(() => {
      $("#valence-question").text(questions[ratingStep]);
      valenceStartTime = Date.now();
      responseTimer = setTimeout(handleValenceTimeout, RESPONSE_TIMEOUT);
    }, 600);
    return;
  }

  // پایان رتبه‌بندی سه‌گانه
  let data = {
    block: currentBlock,
    trial: currentTrial,
    cue: currentCue,
    stimulus1: currentStim1,
    stimulus2: currentStim2,
    expected_sequence: expectedSequence,
    is_consistent: actualSequence === expectedSequence,
    category_stim1: categoryStim1,
    category_stim2: categoryStim2,
    valence_stim1: trialValenceStim1,
    valence_rt_stim1: trialValenceRtStim1,
    valence_stim2: trialValenceStim2,
    valence_rt_stim2: trialValenceRtStim2,
    valence_sequence: trialValenceSequence,
    valence_rt_sequence: trialValenceRtSequence,
  };

  if (currentStage === "valence_practice") {
    data = {
      is_valence_practice: true,
      trial: valencePracticeTrial,
      cue: currentCue,
      stimulus1: currentStim1,
      stimulus2: currentStim2,
      valence_stim1: trialValenceStim1,
      valence_rt_stim1: trialValenceRtStim1,
      valence_stim2: trialValenceStim2,
      valence_rt_stim2: trialValenceRtStim2,
      valence_sequence: trialValenceSequence,
      valence_rt_sequence: trialValenceRtSequence,
    };
    $.post("", JSON.stringify(data), null, "json");
    valencePracticeTrial++;

    $("#valence-rating").addClass("hidden");
    if (valencePracticeTrial > VALENCE_PRACTICE_TRIALS) {
      $("#main-intro").removeClass("hidden");
    } else {
      setTimeout(startTrial, 1000);
    }
    return;
  }

  // مرحله اصلی
  $.post("", JSON.stringify(data), null, "json");

  currentTrial++;
  if (currentTrial > TRIALS_PER_BLOCK) {
    currentTrial = 1;
    currentBlock++;
    catchTrialCountInBlock = 0; // ریست catch برای بلوک بعدی

    if (currentBlock > NUM_BLOCKS) {
      if (HAS_RERATING === 'true') {
        $("#rerating-intro").removeClass("hidden");
      } else {
        $("#final-thanks").removeClass("hidden");
      }
      return;
    }

    $("#block-break-message").html(`بلوک ${currentBlock - 1} پایان یافت.<br>استراحت کنید و سپس بلوک ${currentBlock} را شروع کنید.`);
    $("#block-break").removeClass("hidden");
    return;
  }

  $("#valence-rating").addClass("hidden");
  setTimeout(startTrial, 1000);
}

// دکمه‌های رتبه‌بندی
$(".sam-btn").on("click", function () {
  clearResponseTimer();
  $(".sam-btn").removeClass("selected");
  $(this).addClass("selected");

  const value = parseInt($(this).data("value"));
  const rt = Date.now() - valenceStartTime;

  if (currentStage === "rerating") {
    if (reratingValence === null) {
      reratingValence = value;
      setTimeout(showReratingArousal, 300);
    } else {
      reratingArousal = value;
      saveReratingResponse();
    }
  } else {
    processValenceResponse(value, rt);
  }
});

// کیبورد
$(document).on("keydown.pcm", function (e) {
  if ($("#valence-rating").is(":visible") || $("#arousal-rating").is(":visible")) {
    if (e.key >= "1" && e.key <= "9") {
      $(`.sam-btn[data-value="${e.key}"]`).trigger("click");
    }
  }
});

// رویدادها
$("#start-practice").click(() => {
  $("#intro").addClass("hidden");
  currentStage = "practice";
  startTrial();
});

$(".sequence-btn").click(function () {
  clearResponseTimer();
  const userChoice = $(this).data("seq");
  const correct = userChoice === expectedSequence;

  practiceTotal++;
  if (correct) practiceCorrect++;

  $("#practice-feedback").text(correct ? "درست!" : "غلط!").css("color", correct ? "green" : "red").show();

  savePracticeData(userChoice, correct);

  setTimeout(() => {
    $("#practice-choice").addClass("hidden");
    $("#practice-feedback").hide();

    if (practiceTotal >= PRACTICE_TRIALS) {
      if (practiceCorrect / practiceTotal >= PRACTICE_THRESHOLD) {
        $("#valence-practice-intro").removeClass("hidden");
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

$("#start-valence-practice-intro").click(function() {
  $("#valence-practice-intro").addClass("hidden");
  currentStage = "valence_practice";
  valencePracticeTrial = 1;  // اگر لازم بود ریست بشه
  startTrial();
});

// ادامه از وسط تمرینی رتبه‌بندی (resume)
$("#resume-valence-practice-btn").click(function() {
  $("#resume-valence-practice").addClass("hidden");
  currentStage = "valence_practice";
  startTrial();
});

$("#start-main, #resume-main-button").click(() => {
  $(this).closest("div").addClass("hidden");
  currentStage = "main";
  catchTrialCountInBlock = 0;
  startTrial();
});

$("#continue-after-break").click(() => {
  $("#block-break").addClass("hidden");
  catchTrialCountInBlock = 0;
  setTimeout(startTrial, 1000);
});

$("#start-rerating, #resume-rerating-btn").click(() => {
  $(this).closest("div").addClass("hidden");
  currentStage = "rerating";
  startRerating();
});

$(document).ready(function () {
  $(".content > div:not(#rotate-device)").addClass("hidden");
  $(".sam-btn").off("click").on("click", $(".sam-btn").handlers); // جلوگیری از دابل‌بایند

  const stage = INITIAL_STAGE;
  if (stage === "block_break" || IS_AT_BLOCK_BREAK === 'true') {
    $("#block-break").removeClass("hidden");
  } else if (stage.includes("valence_practice")) {
    $(`#${stage.replace("_", "-")}`).removeClass("hidden");
  } else if (stage === "final_thanks") {
    $("#final-thanks").removeClass("hidden");
  } else {
    $(`#${stage.replace("_", "-")}`).removeClass("hidden");
  }
});