const kutu = document.getElementById("etkin");
const durum = document.getElementById("durum");

function durumYaz(acik) {
  durum.textContent = acik
    ? "Video bitince bir sonraki Shorts'a geçilir."
    : "Kapalı: Shorts videoları döngüde oynar.";
}

chrome.storage.sync.get({ etkin: true }, ({ etkin }) => {
  kutu.checked = etkin;
  durumYaz(etkin);
});

kutu.addEventListener("change", () => {
  chrome.storage.sync.set({ etkin: kutu.checked });
  durumYaz(kutu.checked);
});
