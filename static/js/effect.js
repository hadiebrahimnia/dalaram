document.addEventListener('DOMContentLoaded', function () {
  // برای دکمه‌های sequence-btn
  document.querySelectorAll('.sequence-btn').forEach(btn => {
    btn.addEventListener('pointerdown', function () {
      this.classList.add('touch-effect');
    });

    btn.addEventListener('pointerup', function () {
      setTimeout(() => this.classList.remove('touch-effect'), 120);
    });

    btn.addEventListener('pointerleave', function () {
      this.classList.remove('touch-effect');
    });

    // برای کیبورد
    btn.addEventListener('keydown', function (e) {
      if (e.key === 'Enter' || e.key === ' ') {
        this.classList.add('keyboard-effect');
      }
    });
    btn.addEventListener('keyup', function (e) {
      if (e.key === 'Enter' || e.key === ' ') {
        setTimeout(() => this.classList.remove('keyboard-effect'), 120);
      }
    });
  });

  // برای دکمه‌های sam-btn
  document.querySelectorAll('.sam-btn').forEach(btn => {
    btn.addEventListener('pointerdown', function () {
      this.classList.add('touch-effect');
    });

    btn.addEventListener('pointerup', function () {
      setTimeout(() => this.classList.remove('touch-effect'), 120);
    });

    btn.addEventListener('pointerleave', function () {
      this.classList.remove('touch-effect');
    });

    // کیبورد
    btn.addEventListener('keydown', function (e) {
      if (e.key === 'Enter' || e.key === ' ') {
        this.classList.add('keyboard-effect');
      }
    });
    btn.addEventListener('keyup', function (e) {
      if (e.key === 'Enter' || e.key === ' ') {
        setTimeout(() => this.classList.remove('keyboard-effect'), 120);
      }
    });
  });
});