document.addEventListener('DOMContentLoaded', function () {
    const buttons = document.querySelectorAll('.sequence-btn, .sam-btn');

    buttons.forEach(btn => {
      // تاچ / کلیک
      btn.addEventListener('pointerdown', function () {
        this.classList.add('touch-effect');
      });

      btn.addEventListener('pointerup', function () {
        const el = this;
        setTimeout(() => {
          el.classList.remove('touch-effect');
          el.blur(); // ← این خط خیلی مهمه (حذف focus آبی)
        }, 130);
      });

      btn.addEventListener('pointerleave', function () {
        this.classList.remove('touch-effect');
      });

      btn.addEventListener('pointercancel', function () {
        this.classList.remove('touch-effect');
        this.blur();
      });

      // کیبورد
      btn.addEventListener('keydown', function (e) {
        if (e.key === 'Enter' || e.key === ' ') {
          this.classList.add('keyboard-effect');
        }
      });

      btn.addEventListener('keyup', function (e) {
        if (e.key === 'Enter' || e.key === ' ') {
          const el = this;
          setTimeout(() => {
            el.classList.remove('keyboard-effect');
            el.blur();
          }, 130);
        }
      });
    });
  });