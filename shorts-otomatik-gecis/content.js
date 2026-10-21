// Shorts Otomatik Geçiş — içerik betiği
// YouTube Shorts videoları normalde sonsuz döngüde oynar. Bu betik aktif Shorts
// videosunun sonuna gelindiğini yakalar ve bir sonraki videoya geçer.
(() => {
  "use strict";

  const AYAR_ANAHTARI = "etkin";
  const BEKLEME_MS = 1500; // iki geçiş arasında en az bu kadar süre olmalı

  let etkin = true;
  let sonGecis = 0;
  const izlenenler = new WeakSet();

  // --- Ayarlar --------------------------------------------------------------
  chrome.storage.sync.get({ [AYAR_ANAHTARI]: true }, (sonuc) => {
    etkin = sonuc[AYAR_ANAHTARI];
  });
  chrome.storage.onChanged.addListener((degisiklik, alan) => {
    if (alan === "sync" && AYAR_ANAHTARI in degisiklik) {
      etkin = degisiklik[AYAR_ANAHTARI].newValue;
    }
  });

  // --- Yardımcılar ----------------------------------------------------------
  const shortsSayfasi = () => location.pathname.startsWith("/shorts/");

  function aktifVideo() {
    return (
      document.querySelector("ytd-reel-video-renderer[is-active] video") ||
      document.querySelector("#shorts-player video") ||
      document.querySelector("ytm-shorts-player video") || // mobil site
      [...document.querySelectorAll("ytd-shorts video, ytm-reel-player video")]
        .find((v) => !v.paused)
    );
  }

  function sonrakineGec() {
    const simdi = Date.now();
    if (!etkin || !shortsSayfasi() || simdi - sonGecis < BEKLEME_MS) return;
    sonGecis = simdi;

    // 1) "Sonraki video" düğmesi
    const dugme =
      document.querySelector("#navigation-button-down button") ||
      document.querySelector("#navigation-button-down ytd-button-renderer button") ||
      document.querySelector("#navigation-button-down");
    if (dugme && dugme.offsetParent !== null) {
      dugme.click();
      return;
    }

    // 2) Klavye kısayolu (Aşağı ok)
    const tus = { key: "ArrowDown", code: "ArrowDown", keyCode: 40, which: 40, bubbles: true };
    document.dispatchEvent(new KeyboardEvent("keydown", tus));
    document.dispatchEvent(new KeyboardEvent("keyup", tus));

    // 3) Kaydırma (yedek)
    const kap = document.querySelector("#shorts-inner-container");
    if (kap) kap.scrollBy({ top: kap.clientHeight, behavior: "smooth" });
  }

  function videoyuIzle(video) {
    if (izlenenler.has(video)) return;
    izlenenler.add(video);

    let oncekiZaman = 0;

    // Döngü kapatılabilirse "ended" olayı tetiklenir.
    video.addEventListener("ended", () => {
      if (video === aktifVideo()) sonrakineGec();
    });

    // YouTube döngüyü yeniden açabilir; bu durumda sondan başa sarılmayı yakala.
    video.addEventListener("timeupdate", () => {
      const sure = video.duration;
      const zaman = video.currentTime;
      if (
        etkin &&
        sure > 0 &&
        isFinite(sure) &&
        oncekiZaman > sure - 1 &&
        zaman < 1 &&
        !video.seeking &&
        video === aktifVideo()
      ) {
        sonrakineGec();
      }
      oncekiZaman = zaman;
    });

    // Kullanıcı elle başa sararsa yanlış algılamayı önle.
    video.addEventListener("seeking", () => {
      oncekiZaman = video.currentTime;
    });
  }

  function denetle() {
    if (!shortsSayfasi()) return;
    const video = aktifVideo();
    if (!video) return;
    videoyuIzle(video);
    // Döngüyü kapat ki video bitince "ended" olayı gelsin.
    if (etkin && video.loop) video.loop = false;
    if (!etkin && !video.loop) video.loop = true;
  }

  // YouTube tek sayfalık uygulama: sayfa değişimlerini ve DOM değişimlerini izle.
  document.addEventListener("yt-navigate-finish", denetle);
  new MutationObserver(denetle).observe(document.documentElement, {
    childList: true,
    subtree: true,
    attributes: true,
    attributeFilter: ["is-active", "loop"],
  });
  setInterval(denetle, 1000);
  denetle();
})();
