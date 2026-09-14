/**
 * SOFA Giriş (Splash) Ekranı Kontrolcüsü
 * Sıra: "Safe One For All" -> ikon -> "S-O-F-A" harfleri teker teker -> ana uygulamaya geçiş.
 */
document.addEventListener("DOMContentLoaded", () => {
  const splash = document.getElementById("splash-screen");
  const appShell = document.getElementById("app-shell");

  if (!splash || !appShell) return;

  // CSS animasyon gecikmelerinin tamamlanması için yeterli süre (style.css ile senkron).
  const TOTAL_SPLASH_DURATION_MS = 3200;

  window.setTimeout(() => {
    splash.classList.add("fade-out");
    appShell.hidden = false;

    splash.addEventListener(
      "transitionend",
      () => {
        splash.remove();
      },
      { once: true }
    );
  }, TOTAL_SPLASH_DURATION_MS);
});
