let currentBlock = CURRENT_BLOCK_INIT;
let currentTrial = CURRENT_TRIAL_INIT;
let currentStage = INITIAL_STAGE;

let seqTrial = SEQ_TOTAL_INIT + 1;
let seqCorrect = SEQ_CORRECT_INIT;
let valencePracticeTrial = VALENCE_PRACTICE_COMPLETED_COUNT + 1;
let ratingPracticeTrial = RATING_PRACTICE_COMPLETED_COUNT + 1;
let currentReratingIndex = RERATING_COMPLETED_COUNT;

let catchTrialCountInBlock = 0;

let currentCue = null, currentStim1 = null, currentStim2 = null;
let expectedSequence = null, actualSequence = null;
let categoryStim1 = null, categoryStim2 = null;

let ratingStep = 0; // 0: stim1, 1: stim2, 2: sequence
let valenceStartTime = null;
let responseTimer = null;
const RESPONSE_TIMEOUT = 4000;

const audio = $("#audio-player")[0];

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

function startTrial() {
    currentCue = cueUrls[Math.floor(Math.random() * cueUrls.length)];
    expectedSequence = cuesMapping[currentCue];

    // تعیین توالی واقعی
    const isInconsistent = currentStage === "main" && Math.random() < INCONSISTENT_RATIO;
    actualSequence = isInconsistent
        ? Object.values(cuesMapping).filter(s => s !== expectedSequence)[Math.floor(Math.random() * 2)]
        : expectedSequence;

    [categoryStim1, categoryStim2] = actualSequence.split("-");
    const pool1 = categoryStim1 === "Neutral" ? neutralUrls : negativeUrls;
    const pool2 = categoryStim2 === "Neutral" ? neutralUrls : negativeUrls;

    currentStim1 = pool1[Math.floor(Math.random() * pool1.length)];
    currentStim2 = pool2[Math.floor(Math.random() * pool2.length)];

    // آیا Catch Trial است؟
    const isCatch = currentStage === "main" && currentTrial <= CATCH_TRIALS_PER_BLOCK && catchTrialCountInBlock < CATCH_TRIALS_PER_BLOCK;

    showFixation(() => {
        playSound(currentCue, () => {
            playSound(currentStim1, () => {
                playSound(currentStim2, () => {
                    if (isCatch || currentStage === "seq_practice") {
                        showSequenceChoice();
                        if (isCatch) catchTrialCountInBlock++;
                    } else {
                        ratingStep = 0;
                        showValenceRating("لطفاً خوشایندی محرک اول را رتبه‌بندی کنید");
                    }
                });
            });
        });
    });
}

function showSequenceChoice() {
    $("#seq-practice-choice").removeClass("hidden");
    $("#seq-feedback").hide();
    responseTimer = setTimeout(() => {
        $("#seq-feedback").text("لطفاً سریع‌تر پاسخ دهید!").css("color", "red").show();
        saveSequencePractice(null, false);
        setTimeout(checkSequencePracticeCompletion, 2000);
    }, RESPONSE_TIMEOUT);
}

function showValenceRating(question) {
    $("#valence-question").text(question);
    $("#valence-rating").removeClass("hidden");
    $(".sam-btn").removeClass("selected");
    valenceStartTime = Date.now();
    responseTimer = setTimeout(() => processValenceResponse(null, null), RESPONSE_TIMEOUT);
}

function processValenceResponse(value, rt) {
    clearResponseTimer();
    if (value === null) rt = null;

    let trialData = {
        cue: currentCue,
        stimulus1: currentStim1,
        stimulus2: currentStim2,
        category_stim1: categoryStim1,
        category_stim2: categoryStim2,
    };

    if (ratingStep === 0) trialData.valence_stim1 = value, trialData.valence_rt_stim1 = rt;
    else if (ratingStep === 1) trialData.valence_stim2 = value, trialData.valence_rt_stim2 = rt;
    else if (ratingStep === 2) trialData.valence_sequence = value, trialData.valence_rt_sequence = rt;

    if (ratingStep < 2) {
        ratingStep++;
        const questions = [
            "لطفاً خوشایندی محرک اول را رتبه‌بندی کنید",
            "لطفاً خوشایندی محرک دوم را رتبه‌بندی کنید",
            "لطفاً خوشایندی کل توالی را رتبه‌بندی کنید"
        ];
        setTimeout(() => showValenceRating(questions[ratingStep]), 600);
        return;
    }

    // ذخیره نهایی
    if (currentStage === "valence_practice") {
        trialData.is_valence_practice = true;
        trialData.trial = valencePracticeTrial++;
    } else {
        trialData.block = currentBlock;
        trialData.trial = currentTrial;
        trialData.expected_sequence = expectedSequence;
        trialData.is_consistent = actualSequence === expectedSequence;
    }

    $.post("", JSON.stringify(trialData), null, "json");

    $("#valence-rating").addClass("hidden");

    if (currentStage === "valence_practice") {
        if (valencePracticeTrial > VALENCE_PRACTICE_TRIALS) {
            $("#main-intro").removeClass("hidden");
        } else {
            setTimeout(startTrial, 1000);
        }
    } else {
        // مرحله اصلی
        currentTrial++;
        if (currentTrial > TRIALS_PER_BLOCK) {
            currentTrial = 1;
            currentBlock++;
            catchTrialCountInBlock = 0;
            if (currentBlock > NUM_BLOCKS) {
                $("#rating-practice-intro").removeClass("hidden");
                return;
            }
            $("#block-break-message").html(BLOCK_BREAK_MESSAGE || `بلوک ${currentBlock - 1} پایان یافت. استراحت کنید.`);
            $("#block-break").removeClass("hidden");
        } else {
            setTimeout(startTrial, 1000);
        }
    }
}

function saveSequencePractice(userChoice, correct) {
    seqTrial++;
    if (correct) seqCorrect++;
    $.post("", JSON.stringify({
        is_seq_practice: true,
        trial: seqTrial - 1,
        cue: currentCue,
        stimulus1: currentStim1,
        stimulus2: currentStim2,
        category_stim1: categoryStim1,
        category_stim2: categoryStim2,
        user_response: userChoice,
        is_correct: correct
    }), null, "json");
}

function checkSequencePracticeCompletion() {
    $("#seq-practice-choice").addClass("hidden");
    if (seqTrial > SEQ_PRACTICE_TRIALS) {
        if (seqCorrect / SEQ_PRACTICE_TRIALS >= SEQ_THRESHOLD) {
            $("#valence-practice-intro").removeClass("hidden");
        } else {
            alert("دقت کافی نبود. مرحله تمرینی دوباره شروع می‌شود.");
            seqTrial = 1; seqCorrect = 0;
            startTrial();
        }
    } else {
        startTrial();
    }
}

function startReratingPractice() {
    if (ratingPracticeTrial > RATING_PRACTICE_TRIALS) {
        $("#rating-main-intro").removeClass("hidden");
        return;
    }
    const stim = neutralUrls.concat(negativeUrls)[Math.floor(Math.random() * (neutralUrls.length + negativeUrls.length))];
    playSound(stim, () => {
        ratingStep = 0;
        showValenceRating("لطفاً خوشایندی این صدا را رتبه‌بندی کنید");
    });
}

function startMainRerating() {
    if (currentReratingIndex >= TOTAL_RERATING_FILES) {
        $("#final-thanks").removeClass("hidden");
        return;
    }
    const stim = reratingFiles[currentReratingIndex];
    playSound(stim, () => {
        ratingStep = 0;
        showValenceRating("لطفاً خوشایندی این صدا را رتبه‌بندی کنید");
    });
}

// رویدادها
$(document).ready(function () {
    $(".content > div:not(#rotate-device)").addClass("hidden");

    if (IS_AT_BLOCK_BREAK) {
        $("#block-break").removeClass("hidden");
        $("#block-break-message").html(BLOCK_BREAK_MESSAGE);
    } else if (SHOW_RESUME_SCREEN) {
        $(`#${INITIAL_STAGE.replace(/_/g, "-")}`).removeClass("hidden");
        $(`#${INITIAL_STAGE.replace(/_/g, "-")}-message`).text(RESUME_MESSAGE);
    } else {
        $(`#${INITIAL_STAGE.replace(/_/g, "-")}`).removeClass("hidden");
    }
});

$("#start-seq-practice, #resume-seq-btn").click(() => {
    $(this).closest("div").addClass("hidden");
    currentStage = "seq_practice";
    startTrial();
});

$(".sequence-btn").click(function () {
    clearResponseTimer();
    const userChoice = $(this).data("seq");
    const correct = userChoice === expectedSequence;
    $("#seq-feedback").text(correct ? "درست!" : "غلط!").css("color", correct ? "green" : "red").show();
    saveSequencePractice(userChoice, correct);
    setTimeout(checkSequencePracticeCompletion, 1500);
});

$("#start-valence-practice, #resume-valence-btn").click(() => {
    $(this).closest("div").addClass("hidden");
    currentStage = "valence_practice";
    startTrial();
});

$("#start-main, #resume-main-btn").click(() => {
    $(this).closest("div").addClass("hidden");
    currentStage = "main";
    catchTrialCountInBlock = 0;
    startTrial();
});

$("#continue-after-break").click(() => {
    $("#block-break").addClass("hidden");
    catchTrialCountInBlock = 0;
    startTrial();
});

$("#start-rating-practice, #resume-rating-practice-btn").click(() => {
    $(this).closest("div").addClass("hidden");
    currentStage = "rating_practice";
    startReratingPractice();
});

$("#start-rating-main, #resume-rating-main-btn").click(() => {
    $(this).closest("div").addClass("hidden");
    currentStage = "rating_main";
    startMainRerating();
});

$(".sam-btn").click(function () {
    clearResponseTimer();
    $(".sam-btn").removeClass("selected");
    $(this).addClass("selected");
    const value = parseInt($(this).data("value"));
    const rt = Date.now() - valenceStartTime;

    if (currentStage === "rating_practice" || currentStage === "rating_main") {
        if (ratingStep === 0) {
            // Valence
            $.post("", JSON.stringify({
                [currentStage === "rating_practice" ? "is_rating_practice" : "is_rerating"]: true,
                trial: ratingPracticeTrial,
                stimulus: audio.src,
                stimulus_number: audio.src.split('/').pop().split('.')[0],
                valence: value,
                valence_rt: rt
            }), null, "json");
            $("#valence-rating").addClass("hidden");
            $("#arousal-rating").removeClass("hidden");
            valenceStartTime = Date.now();
        } else {
            // Arousal
            $.post("", JSON.stringify({
                [currentStage === "rating_practice" ? "is_rating_practice" : "is_rerating"]: true,
                trial: ratingPracticeTrial,
                stimulus: audio.src,
                stimulus_number: audio.src.split('/').pop().split('.')[0],
                arousal: value,
                arousal_rt: rt
            }), null, "json");
            $("#arousal-rating").addClass("hidden");
            if (currentStage === "rating_practice") {
                ratingPracticeTrial++;
                setTimeout(startReratingPractice, 1000);
            } else {
                currentReratingIndex++;
                setTimeout(startMainRerating, 1000);
            }
        }
        ratingStep = 1 - ratingStep;
    } else {
        processValenceResponse(value, rt);
    }
});

$(document).on("keydown.pcm", function (e) {
    if ($("#valence-rating, #arousal-rating").is(":visible") && e.key >= "1" && e.key <= "9") {
        $(`.sam-btn[data-value="${e.key}"]`).trigger("click");
    }
});