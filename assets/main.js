function main() {
  lazyload();
  const container = document.getElementById('bg-container');
  container.classList.forEach((cl) => {
    if (cl.startsWith('sephira-')) {
      container.classList.remove(cl);
    }
  });

  const choices = ['sephira-smile', 'sephira-surprise', 'sephira-upturned', 'sephira-wink', 'sephira-yandere'];
  const idx = Math.floor(Math.random() * choices.length);
  container.classList.add(choices[idx]);
}

window.onload = main;
