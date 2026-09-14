/**
 * SOFA Giriş (Splash) Ekranı Kontrolcüsü
 *
 * Sıra: logo -> "SOFA" -> "Safe" "One" "For" "All" (teker teker) ->
 * yükleme çubuğu (%0-%100) -> yükleme bitince: logo+SOFA grubu yukarı
 * kayıp küçülerek söner, header'daki brand belirir (devralma hissi),
 * splash geri kalanıyla birlikte söner ve arkadaki uygulama
 * bulanıklıktan netliğe geçerek ortaya çıkar.
 */
document.addEventListener("DOMContentLoaded", () => {
  const splash = document.getElementById("splash-screen");
  const splashContent = document.getElementById("splash-content");
  const splashBrand = document.getElementById("splash-brand");
  const appShell = document.getElementById("app-shell");
  const headerBrand = document.getElementById("header-brand");
  const fill = document.getElementById("splash-loading-fill");
  const loadingText = document.getElementById("splash-loading-text");

  if (!splash || !appShell) return;

  // Yükleme çubuğu, tagline kelimeleri belirdikten sonra dolmaya başlar
  // (CSS'teki .splash-loading animation-delay ile senkron).
  const LOADING_START_DELAY_MS = 2600;
  const LOADING_FILL_DURATION_MS = 1500;

  let finished = false;

  function setProgress(percent) {
    const clamped = Math.max(0, Math.min(100, percent));
    if (fill) fill.style.width = `${clamped}%`;
    if (loadingText) {
      loadingText.textContent = clamped >= 100 ? "Hazır" : `Yükleniyor... %${Math.round(clamped)}`;
    }
    if (clamped >= 100) {
      finishSplash();
    }
  }

  function finishSplash() {
    if (finished) return;
    finished = true;

    // 1) Tagline + yükleme çubuğu söner; logo+SOFA grubu yukarı/ortaya taşınır.
    splashContent.classList.add("collapsing");
    splashBrand.classList.add("collapse");

    // 2) Header'daki brand aynı anda belirir (devralma / crossfade hissi).
    headerBrand.classList.add("show");

    // 3) Arkadaki uygulama bulanıklıktan netliğe geçerek belirir.
    // Bir sonraki frame'de class eklemek, transition'ın tetiklenmesini garanti eder.
    requestAnimationFrame(() => {
      requestAnimationFrame(() => appShell.classList.add("revealed"));
    });

    // 4) Splash overlay'i tamamen söner ve DOM'dan kaldırılır.
    window.setTimeout(() => {
      splash.classList.add("fade-out");
    }, 300);

    splash.addEventListener(
      "transitionend",
      () => {
        splash.remove();
      },
      { once: true }
    );
  }

  const startTime = Date.now() + LOADING_START_DELAY_MS;
  const tick = window.setInterval(() => {
    const now = Date.now();
    if (now < startTime) return;

    const elapsed = now - startTime;
    const percent = (elapsed / LOADING_FILL_DURATION_MS) * 100;
    setProgress(percent);

    if (percent >= 100) {
      window.clearInterval(tick);
    }
  }, 40);
});
