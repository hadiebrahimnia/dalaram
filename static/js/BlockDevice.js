document.addEventListener('DOMContentLoaded', function () {
    // اول دستگاه را بررسی کن
    const canContinue = initDeviceCheck(
        (typeof INITIAL_STAGE !== 'undefined' ? INITIAL_STAGE : 'sequence_practice')
    );

    // اگر دستگاه غیرمجاز بود، بقیه کد اجرا نشود
    if (!canContinue) return;

    // مخفی کردن همه بخش‌ها به جز rotate-device
    document.querySelectorAll('.content > div:not(#rotate-device)').forEach(function (el) {
        el.classList.add('hidden');
    });

    if (typeof IS_AT_BLOCK_BREAK !== 'undefined' && IS_AT_BLOCK_BREAK) {
        const blockBreak = document.getElementById('block-break');
        if (blockBreak) {
            blockBreak.classList.remove('hidden');
            const msg = document.getElementById('block-break-message');
            if (msg) msg.innerHTML = BLOCK_BREAK_MESSAGE;
        }
    } else if (typeof SHOW_RESUME_SCREEN !== 'undefined' && SHOW_RESUME_SCREEN) {
        const stageId = (typeof INITIAL_STAGE !== 'undefined' ? INITIAL_STAGE : 'sequence_practice').replace(/_/g, '-');
        const stageEl = document.getElementById(stageId);
        if (stageEl) stageEl.classList.remove('hidden');

        const msgEl = document.getElementById(stageId + '-message');
        if (msgEl && typeof RESUME_MESSAGE !== 'undefined') {
            msgEl.textContent = RESUME_MESSAGE;
        }
    } else {
        const stageId = (typeof INITIAL_STAGE !== 'undefined' ? INITIAL_STAGE : 'sequence_practice').replace(/_/g, '-');
        const stageEl = document.getElementById(stageId);
        if (stageEl) stageEl.classList.remove('hidden');
    }
});